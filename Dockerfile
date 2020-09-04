FROM ubuntu:18.04

MAINTAINER togglecorp info@togglecorp.com

ENV PYTHONUNBUFFERED 1
ARG ORCA_VERSION=1.2.1

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
        fonts-noto \
        # Required by orca (Plotly)
        libxss1 xvfb libgtk2.0-0 libgconf-2-4 \
        # Required by cloudwatch scripts
        unzip \
        libwww-perl \
        libdatetime-perl \
        # Required by deploy/scripts/aws_metrics_put.py
        sysstat \
        # for headless chrome
        && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update -y && apt-get install -y \
            fonts-freefont-ttf \
            google-chrome-stable \
        # Install orca for plotly
        && curl https://github.com/plotly/orca/releases/download/v${ORCA_VERSION}/orca-${ORCA_VERSION}-x86_64.AppImage \
            -L --output /tmp/orca-x86_64.AppImage \
        && chmod +x /tmp/orca-x86_64.AppImage \
        && /tmp/orca-x86_64.AppImage --appimage-extract \
        && mv squashfs-root /opt/orca \
        && printf '#!/bin/bash\n xvfb-run -a /opt/orca/app/orca "$@"' > /usr/bin/orca \
        && chmod +x /usr/bin/orca && orca --version \
        # Clean apt
        && rm -rf /var/lib/apt/lists/* \
        && apt-get autoremove

# Chrome webdriver
RUN CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") \
        && CHROME_DRIVER_VERSION=$(curl "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
        && curl -sS -o /tmp/chromedriver_linux64.zip \
            http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
        && unzip -qq /tmp/chromedriver_linux64.zip -d /usr/bin/ \
        && chmod 755 /usr/bin/chromedriver \
        && rm /tmp/chromedriver_linux64.zip

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
