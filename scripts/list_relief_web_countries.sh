#!/bin/bash

function get_countries_data {
    curl 'https://api.reliefweb.int/v1/countries?fields[include][]=name&fields[include][]=iso3&limit=300' \
        --globoff
}

COUNTRIES_DATA=`get_countries_data`

echo $COUNTRIES_DATA | jq -r '.data[].fields | [.iso3, .name] | @csv'
