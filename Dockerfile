FROM ubuntu:16.04

MAINTAINER togglecorp info@togglecorp.com

# Clean apt
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/lib/apt/lists/partial/* && \
    rm -rf /var/cache/apt/*

# Update and install common packages with apt
RUN apt-get update -y ; \
    apt-get install -y \
        # Basic Packages
        git \
        locales \
        vim \
        curl \
        cron \
        unzip \
        python3 \
        python3-dev \
        python3-setuptools \
        python3-pip \
        # Deep Required Packages
        binutils libproj-dev gdal-bin \
        libreoffice \
        gawk \
        # Required by cloudwatch scripts
        unzip \
        libwww-perl \
        libdatetime-perl \
        # Required by deploy/scripts/aws_metrics_put.py
        sysstat

# Support utf-8
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

COPY ./deploy/scripts/remote2_syslog_init.sh /tmp/
RUN /tmp/remote2_syslog_init.sh

# Install uwsgi for django
RUN pip3 install uwsgi

WORKDIR /code

RUN pip3 install virtualenv
RUN virtualenv /venv

COPY ./requirements.txt /code/requirements.txt
RUN . /venv/bin/activate && \
    pip install -r requirements.txt

COPY . /code/

CMD ./deploy/scripts/prod_exec.sh
