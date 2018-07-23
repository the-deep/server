#!/bin/bash

if [ "$EBS_ENV_TYPE" == "web" ]; then
    exit 0
fi

exit 1
