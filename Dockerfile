FROM python:3.8-slim-buster as base

LABEL maintainer="Deep Dev dev@thedeep.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY pyproject.toml poetry.lock /code/

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        # Basic Packages
        iproute2 git vim \
        # Build required packages
        gcc libc-dev libproj-dev \
        # NOTE: procps: For pkill command
        procps \
        # Deep Required Packages
        wait-for-it binutils gdal-bin \
    # Upgrade pip and install python packages for code
    && pip install --upgrade --no-cache-dir pip poetry \
    && poetry --version \
    # Configure to use system instead of virtualenvs
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    # Clean-up
    && pip uninstall -y poetry virtualenv-clone virtualenv \
    && apt-get remove -y gcc libc-dev libproj-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*


# -------------------------- WEB ---------------------------------------
FROM base AS web

COPY . /code/


# -------------------------- WORKER ---------------------------------------
FROM base AS worker

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        libreoffice \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /code/
