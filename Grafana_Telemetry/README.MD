
# Grafana Dashboards for ISS Telemetry with Prometheus

This folder contains the `iss-telemetry-exporter` and `docker-compose.yml` to get quicly started.

## Container included in `docker-compose.yml`

- iss-telemetry-exporter: expose data from [lightstreamer](https://demos.lightstreamer.com/ISSLive/) as Prometheus compatible metric
- [Prometheus](https://prometheus.io): scape those data from the exporter
- [Grafana](https://grafana.com): visualise the data from Prometheus

### `iss-telemetry-exporter`
The metrics are collected with help of [py-iss-telemetry](https://pypi.org/project/py-iss-telemetry/) (currently directly installed through [Kariton's GitHub fork](https://github.com/Kariton/py-iss-telemetry))

## Ready to use Dashboards
- iss-telemetry: an [autograf](https://github.com/FUSAKLA/autograf) generated dashboard with minor inprovements as PoC

## Deployment

Adjust the `.env` and `.env_grafana` as nessesary.

After startup, you can either log in with the default credentials, and Grafana will prompt you to set a new password or
you set an admin username and password in `.env_grafana`.

Uncomment and set a secure password here:
```yaml
#GF_SECURITY_ADMIN_USER=admin
#GF_SECURITY_ADMIN_PASSWORD=grafana
```

The container will listen on these host ports:
- 9090: Prometheus
- 3000: Grafana
- 9155: iss-telemetry-exporter

To deploy this stack run

```bash
  docker compose up -d
```

