# -*- coding: utf-8 -*-

import pandas as pd
import random
import string

from django.views.generic import View
from django.http import FileResponse, HttpResponse


from geo.models import GeoArea
from tabular.viz import (
    barchart,
    histograms,
    map as _map,
)


STRINGS = string.ascii_uppercase + string.digits + 'चैनपुर नगरपालिका à€'


def _get_random_string(N):
    return ''.join(random.choice(STRINGS) for _ in range(N))


def _get_random_number(min, max):
    return random.randint(min, max)


def _get_image_response(fp, image_format):
    if image_format == 'svg':
        return HttpResponse(
            '''
            <!DOCTYPE html>
            <html>
            <body>
            {}
            </body>
            </html>
            '''.format(fp.read().decode('utf-8'))
        )
    return FileResponse(fp, content_type='image/png')


class RenderChart(View):
    """
    Debug chart rendering
    NOTE: Use Only For Debug
    """
    MAX_VALUE_LEN = 1000
    MAX_VALUE_INTEGER = 100
    MAX_ROW = 10
    MAX_COUNT = 100

    def get_geo_data(self):
        return [
            {
                'count': _get_random_number(1, self.MAX_COUNT),
                'value': geoarea.id,
            } for geoarea in GeoArea.objects.filter(admin_level_id=2)
        ]

    def get_data(self, number=False):
        return [
            {
                'count': _get_random_number(10, self.MAX_COUNT),
                'value': _get_random_number(10, self.MAX_VALUE_INTEGER)
                if number else _get_random_string(self.MAX_VALUE_LEN),
            } for row in range(self.MAX_ROW)
        ]

    def get(self, request):
        image_format = request.GET.get('format', 'png')
        chart_type = request.GET.get('chart_type', 'barchart')
        if chart_type in ['histograms']:
            df = pd.DataFrame(self.get_data(number=True))
        elif chart_type in ['map']:
            df = pd.DataFrame(self.get_geo_data())
        else:
            df = pd.DataFrame(self.get_data())

        params = {
            'x_label': 'Test Label',
            'y_label': 'count',
            'chart_size': (8, 4),
            'data': df,
            'format': image_format,
        }

        if chart_type == 'barchart':
            params['data']['value'] = params['data']['value'].str.slice(0, 20) + '...'
            fp = barchart.plotly(**params)
        elif chart_type == 'histograms':
            new_data = []
            values = df['value'].tolist()
            counts = df['count'].tolist()
            for index, value in enumerate(values):
                new_data.extend([value for i in range(counts[index])])
            params['data'] = pd.to_numeric(new_data)
            fp = histograms.plotly(**params)
        elif chart_type == 'map':
            adjust_df = pd.DataFrame([
                {'value': 0, 'count': 0},   # Count 0 is min's max value
                {'value': 0, 'count': 5},   # Count 5 is max's min value
            ])
            params['data'] = params['data'].append(adjust_df, ignore_index=True)
            fp = _map.plot(**params)

        return _get_image_response(fp[0]['image'], fp[0]['format'])
