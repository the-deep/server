FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
ARG ORCA_VERSION=1.2.1

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        # Basic Packages
        iproute2 git vim cron \
        # NOTE: procps: For pkill command
        procps \
        # Deep Required Packages
        binutils libproj-dev gdal-bin libreoffice gawk \
        # Required by cloudwatch scripts
        unzip libwww-perl libdatetime-perl \
        # Required by deploy/scripts/aws_metrics_put.py
        sysstat \
        # Clean apt
        && rm -rf /var/lib/apt/lists/* \
        && apt-get autoremove

COPY ./deploy/scripts/remote2_syslog_init.sh /tmp/
RUN /tmp/remote2_syslog_init.sh

WORKDIR /code

COPY Pipfile Pipfile.lock /code/

# Upgrade pip and install python packages for code
RUN pip install --upgrade --no-cache-dir pip pipenv \
    && pipenv install --dev --system --deploy \
    && pip uninstall -y pipenv virtualenv-clone virtualenv

COPY . /code/

CMD ./deploy/scripts/prod_exec.sh