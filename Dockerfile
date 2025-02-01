FROM python:3.8-bullseye AS base

LABEL maintainer="Deep Dev dev@thedeep.io"
ENV PYTHONUNBUFFERED 1

WORKDIR /code

# Copy dependency files
COPY pyproject.toml poetry.lock /code/

# Install required system dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        iproute2 git vim \
        gcc libc-dev libproj-dev \
        wait-for-it binutils gdal-bin \
        libcairo2 \
        libpango1.0-dev \
        libpangocairo-1.0-0 \
        fonts-dejavu-core \
        fonts-liberation \
    && pip install --upgrade --no-cache-dir pip poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    && apt-get remove -y gcc libc-dev libproj-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Verify installation
RUN pip install weasyprint==53.0

# -------------------------- WEB ---------------------------------------
FROM base AS web

# Copy all project files
COPY . /code/


# -------------------------- WORKER ---------------------------------------
FROM base AS worker

# Additional worker-specific tools
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        libreoffice \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . /code/
