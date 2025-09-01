#!/usr/bin/env python3

import time
import requests
import pyisstelemetry
from prometheus_client import start_http_server as start_prom_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY


class ISSCollector(object):
    def __init__(self):
        self.stream = pyisstelemetry.TelemetryStream()
        self.metrics = {}


    def _get_iss_position(self):
        url = "http://api.open-notify.org/iss-now.json"
        response = requests.get(url)

        if response.status_code != 200 or response.json().get("message", "failed") != "success":
            print("Failed to fetch ISS position")
            return

        position_data = response.json().get("iss_position", {})

        # Define labels for ISS position metrics
        for meta_dict in [{"longitude": "USLAB000LON"}, {"latitude": "USLAB000LAT"}]:
            for k, v in meta_dict.items():
                labels = {"axis": k, "public_pui": v, "subsystem": "ADCO"}
                self._prom_metric(
                    "iss_position", 'ISS position above Earth', labels, float(position_data.get(k, 0.0))
                )


    def _get_iss_telemetry(self):
        data = self.stream.dump_tm()

        for item in data:
            prom_metric_string = f"iss_telemetry_{item['OPS_NOM'] if item['OPS_NOM'] != 'N/A' else item['Description']}"
            prom_metric = prom_metric_string.lower().replace(' ', '_').replace('-', '_')
            prom_help = f"{item['Description']}. Unit: {item['UNITS']}, Format: {item['Format_Spec']}"
            label_public_pui = item["Public_PUI"]
            label_subsystem = item["Discipline"]

            # Define labels for ISS telemetry metric
            labels = {"public_pui": label_public_pui, "subsystem": label_subsystem}
            value = float(item["Value"])

            self._prom_metric(prom_metric, prom_help, labels, value)


    def _prom_metric(self, prom_metric, prom_help, labels, value):
        if prom_metric in self.metrics:
            existing_metric = self.metrics[prom_metric]

            # https://prometheus.io/docs/instrumenting/writing_exporters/
            # > When implementing the collector for your exporter, you should never use the usual direct instrumentation approach and then update the metrics on each scrape.
            # > Rather create new metrics each time.
            #
            # intentional anti-pattern: Remove the already existing metric{labels}, the metric{labels} will be added at the end.
            # Some metrics are rarely reported by the ISS and would simply result in a few values a day (or less).
            # The Grafana panel function "Connect null values" would not always work to accominate this issue because it needs at least two values in the selected time range.
            # Otherwise it would display "No Data"
            # Because metric labels don't change there wont be "old metrics" in a sense of "metrics/labels which are no longer valid".
            # They are just old. But always present, at least as last known value.
            for sample in existing_metric.samples:
                if sample.labels == labels:
                    existing_metric.samples.remove(sample)

        elif prom_metric not in self.metrics:
            # If the metric doesn't exist, create a new metric
            self.metrics[prom_metric] = GaugeMetricFamily(
                prom_metric, prom_help, labels=list(labels.keys())
            )
    
        self.metrics[prom_metric].add_metric(list(labels.values()), value)


    def collect(self):
        self._get_iss_telemetry()
        self._get_iss_position()

        for metric in list(self.metrics.values()):
            yield metric
        # https://prometheus.io/docs/instrumenting/writing_exporters/
        # > When implementing the collector for your exporter, you should never use the usual direct instrumentation approach and then update the metrics on each scrape.
        # > Rather create new metrics each time.
        #
        # intentional anti-pattern: Don't clear the collected metrics, they wil be readded on a value change.
        # Some metrics are rarely reported by the ISS and would simply result in a few values a day (or less).
        # The Grafana panel function "Connect null values" would not always work to accominate this issue because it needs at least two values in the selected time range.
        # Otherwise it would display "No Data"
        # Because metric labels don't change there wont be "old metrics" in a sense of "metrics/labels which are no longer valid".
        # They are just old. But always present, at least as last known value.
        #self.metrics.clear()


def main():
    REGISTRY.register(ISSCollector())
    start_prom_server(9155)
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
