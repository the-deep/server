# -*- coding: utf-8 -*-

import pandas as pd

from django.views.generic import View
from django.http import FileResponse, HttpResponse


from tabular.viz import (
    barchart,
)


class RenderChart(View):
    """
    Debug chart rendering
    NOTE: Use Only For Debug
    """

    data = [
        {'count': 10, 'value': 'toggle'},
        {'count': 20, 'value': 'cor€p'},
        {'count': 30, 'value': 'चैनपुर नगरपालिका '},
        {'count': 1, 'value': 'funà'},
        {'count': 10, 'value': 'fमहालक्ष्मि नगरपालिका '},
        {'count': 10, 'value': 'gमहालक्ष्मि नगरपालिका '},
        {'count': 30, 'value': 'hचैनपुर नगरपालिका '},
        {'count': 30, 'value': 'iचैनपुर नगरपालिका '},
        {'count': 30, 'value': 'jचैनपुर नगरपालिका '},
        {'count': 30, 'value': 'kचैनपुर नगरपालिका '},
        {'count': 30000, 'value': 'toggle21  is my name'},
        {'count': 30, 'value': 'toggle48 is my name'},
        {'count': 30, 'value': 'toggle49 is my name'},
    ]

    def get(self, request):
        df = pd.DataFrame(self.data)

        image_format = request.GET.get('format', 'png')

        params = {
            'x_label': 'Test Label',
            'y_label': 'count',
            'chart_size': (8, 4),
            'data': df,
            'format': image_format,
        }

        fp = barchart.plotly(**params)

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
