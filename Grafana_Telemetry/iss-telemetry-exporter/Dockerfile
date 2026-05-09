### COMPILE ###
FROM python:3.11-alpine AS compile-image

RUN apk update && apk add git

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

#ADD ./py-iss-telemetry/ ./py-iss-telemetry/

COPY requirements.txt .
RUN pip install --upgrade --requirement requirements.txt
#RUN pip install ./py-iss-telemetry/
RUN pip install git+https://github.com/Kariton/py-iss-telemetry.git@master

### BUILD ###

FROM python:3.11-alpine AS build-image
RUN adduser -D iss-telemetry
USER iss-telemetry
WORKDIR /home/iss-telemetry

ADD --chown=iss-telemetry ./iss-telemetry/ ./iss-telemetry/
COPY --from=compile-image --chown=iss-telemetry /opt/venv /opt/venv

RUN chmod +x ./iss-telemetry/bot.py

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
CMD ./iss-telemetry/bot.py
