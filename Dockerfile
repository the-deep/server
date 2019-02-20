FROM ubuntu:18.04

MAINTAINER togglecorp info@togglecorp.com

# Update and install common packages with apt
RUN apt-get update -y && apt-get install -y \
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
        # for headless chrome
        && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update -y && apt-get install -y \
            fonts-freefont-ttf \
            google-chrome-stable \
        # Install chromedriver
        && curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/2.46/chromedriver_linux64.zip \
        && unzip -qq /tmp/chromedriver_linux64.zip -d /usr/bin/ \
        && chmod 755 /usr/bin/chromedriver \
        && rm /tmp/chromedriver_linux64.zip \
        # Clean apt
        && rm -rf /var/lib/apt/lists/*

# Support utf-8
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

COPY ./deploy/scripts/remote2_syslog_init.sh /tmp/
RUN /tmp/remote2_syslog_init.sh

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN echo 'alias python=python3\nalias pip=pip3' >> ~/.bashrc \
    && python3 -m pip install --upgrade pip \ 
    && pip3 install uwsgi \
    && pip3 install -r requirements.txt

COPY . /code/

CMD ./deploy/scripts/prod_exec.sh
