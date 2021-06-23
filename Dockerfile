FROM python:3.8-buster

ENV PYTHONUNBUFFERED 1
ARG ORCA_VERSION=1.2.1

RUN apt-get update -y \
    && apt-get install -y \
        # Basic Packages
        git \
        iproute2 \
        locales \
        vim \
        curl \
        gnupg \
        apt-transport-https \
        ca-certificates \
        cron \
        unzip \
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
