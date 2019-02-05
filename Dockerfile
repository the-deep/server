FROM ubuntu:16.04

MAINTAINER togglecorp info@togglecorp.com

# Update and install common packages with apt
RUN apt-get update -y ; \
        apt-get install -y \
        # Basic Packages
        git \
        locales \
        vim \
        curl \
        gnupg \
        apt-transport-https \
        ca-certificates \
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
        sysstat \
        #for headless chrome //after curl is installed
        && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update -y \
        && apt-get install -y \
        ttf-freefont \
        google-chrome-stable \
        # Clean apt
        && rm -rf /var/lib/apt/lists/*

# Install chromedriver
RUN VERSION=$(curl http://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$VERSION/chromedriver_linux64.zip \
    && unzip -qq /tmp/chromedriver_linux64.zip -d /usr/bin/ \
    && chmod 755 /usr/bin/chromedriver \
    && rm /tmp/chromedriver_linux64.zip 

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
