import os
import pandas as pd
import logging
from datetime import datetime

from django.conf import settings

from deep.documents_types import CHART_IMAGE_MIME
from gallery.models import File
from tabular.models import Field
from tabular.viz import (
    barchart,
    wordcloud,
    histograms,
    map as mapViz,
)


logger = logging.getLogger(__name__)


def DEFAULT_CHART_RENDER(*args, **kwargs):
    return None


BARCHART = 'barchart'
BARCHARTH = 'barcharth'
MAP = 'map'
HISTOGRAM = 'histogram'
WORDCLOUD = 'wordcloud'

DEFAULT_CHART_TYPE_FIELD_MAP = BARCHART
CHART_TYPE_FIELD_MAP = {
    Field.GEO: MAP,
    Field.NUMBER: HISTOGRAM,
}

DEFAULT_IMAGE_PATH = os.path.join(settings.BASE_DIR, 'apps/static/image/deep_chart_preview.png')

CHART_RENDER = {
    # frequency data required
    BARCHART: barchart.plotly,
    BARCHARTH: lambda *args, **kwargs: barchart.plotly(*args, **kwargs, horizontal=True),
    MAP: mapViz.plot,

    # Frequency data not required
    HISTOGRAM: histograms.plotly,
    WORDCLOUD: wordcloud.plot,
}


def get_val_column(field):
    if field.type in [Field.GEO, Field.DATETIME, Field.NUMBER]:
        return 'processed_value'
    return 'value'


def clean_real_data(data, val_column):
    """
    Return clean_dataframe, original_dataframe
    """
    # NOTE: The folloing loop adds the keys empty and invalid if not present
    # TODO: Handle the following case from pandas itself
    formatted_data = []
    for datum in data:
        formatted_data.append({
            **datum,
            'empty': datum.get('empty', False),
            'invalid': datum.get('invalid', False),
        })

    df = pd.DataFrame(formatted_data)

    if df.empty:
        return df, df

    filterd_df = df[~(df['empty'] == True) & ~(df['invalid'] == True)]  # noqa
    return filterd_df, df


def calc_data(field):
    val_column = get_val_column(field)

    data, df = clean_real_data(field.actual_data, val_column)

    if data.empty:
        logger.warning('Empty DataFrame: no numeric data to calculate for field ({})'.format(field.pk))
        return [], {}

    if val_column not in data.columns:
        logger.warning('{} not present in field ({})'.format(val_column, field.pk))
        return None, {}

    data = data.groupby(val_column).count()['empty'].sort_values().to_frame()
    data = data.rename(columns={'empty': 'count', val_column: 'value'})

    data['value'] = data.index
    health_stats = {
        'empty': int(df[df['empty'] == True]['empty'].count()), # noqa
        'invalid': int(df[df['invalid'] == True]['invalid'].count()), # noqa
        'total': len(df.index),
    }
    return data.to_dict(orient='records'), health_stats


def generate_chart(field, chart_type, images_format=['svg']):
    params = {
        'x_label': field.title,
        'y_label': 'count',
        'x_params': {},
        'chart_size': (8, 4),
        'format': images_format,
        # data will be added according to chart type
    }

    if chart_type not in [HISTOGRAM, WORDCLOUD]:
        df = pd.DataFrame(field.cache.get('series'))
        if df.empty or 'value' not in df.columns:
            return None
        params['data'] = df
        if field.type == Field.STRING:  # NOTE: revered is used for ascending order
            params['x_params']['autorange'] = 'reversed'
            params['data']['value'] = params['data']['value'].str.slice(0, 30) + '...'  # Pre slice with ellipses
        elif field.type == Field.GEO:
            adjust_df = pd.DataFrame([
                {'value': 0, 'count': 0},   # Count 0 is min's max value
                {'value': 0, 'count': 5},   # Count 5 is max's min value
            ])
            params['data'] = params['data'].append(adjust_df, ignore_index=True)
        elif field.type == Field.DATETIME:
            if df['value'].count() > 10:
                params['x_params']['tickformat'] = '%d-%m-%Y'
            else:
                params['x_params']['type'] = 'category'
                params['x_params']['ticktext'] = [
                    datetime.strptime(value, '%Y-%m-%dT%H:%M:%S').strftime('%d-%m-%Y')
                    for value in df['value']
                ]
                params['x_params']['tickvals'] = df['value']

    else:
        val_column = get_val_column(field)
        df, _ = clean_real_data(field.actual_data, val_column)
        if chart_type == HISTOGRAM:
            params['data'] = pd.to_numeric(df[val_column])
        elif chart_type == WORDCLOUD:
            params['data'] = ' '.join(df[val_column].values)

    if isinstance(params['data'], pd.DataFrame) and params['data'].empty:
        logger.warning('Empty DataFrame: no numeric data to plot for field ({})'.format(field.pk))
        return None

    chart_render = CHART_RENDER.get(chart_type)
    if chart_render:
        images = chart_render(**params)
        return images
    return None


def calc_preprocessed_data(field):
    """
    Save normalized data to field
    """
    try:
        series, health_stats = calc_data(field)
        cache = {
            'status': Field.CACHE_SUCCESS,
            'series': series,
            'health_stats': health_stats,
        }
        # NOTE: Geo Field cache success after chart generation
        if field.type == Field.GEO:
            cache['status'] = Field.CACHE_PENDING
    except Exception:
        cache = {
            'status': Field.CACHE_ERROR,
            'image_status': Field.CACHE_ERROR,
        }
        logger.error(
            'Tabular Processed Data Calculation Error!!',
            exc_info=True,
            extra={'data': {'field_id': field.pk}},
        )

    field.cache = cache
    field.save()
    return field.cache['status']


def _add_image_to_gallery(image_name, image, mime_type, project):
    file = File.objects.create(
        title=image_name,
        mime_type=mime_type,
        metadata={'tabular': True},
        is_public=False,
    )
    file.file.save(image_name, image)
    if project:
        file.projects.add(project)
    logger.info(
        'Added image to tabular gallery {}(id={})'.format(image_name, file.id),
    )
    return file


def render_field_chart(field):
    """
    Save normalized data to field
    """
    images_format = ['png', 'svg'] if field.type == Field.GEO else ['png']
    chart_type = CHART_TYPE_FIELD_MAP.get(field.type, DEFAULT_CHART_TYPE_FIELD_MAP)

    try:
        images = generate_chart(field, chart_type, images_format=images_format)
    except Exception:
        logger.error(
            'Tabular Chart Render Error!!',
            exc_info=True,
            extra={'data': {'field_id': field.pk}}
        )
        images = []

    project = field.sheet.book.project
    if images and len(images) > 0:
        field_images = []
        for image in images:
            file_format = image['format']
            file_content = image['image']
            file_mime = CHART_IMAGE_MIME[file_format]

            file = _add_image_to_gallery(
                'tabular_{}_{}.{}'.format(field.sheet.id, field.id, file_format),
                file_content,
                file_mime,
                project,
            )
            field_images.append({
                'id': file.id, 'chart_type': chart_type, 'format': file_format,
            })
        field.cache['image_status'] = Field.CACHE_SUCCESS
        if field.type == Field.GEO:
            field.cache['status'] = Field.CACHE_SUCCESS
    else:
        field_images = []
        for image_format in images_format:
            field_images.append({'id': None, 'chart_type': chart_type, 'format': image_format})
        field.cache['image_status'] = Field.CACHE_ERROR
        if field.type == Field.GEO:
            field.cache['status'] = Field.CACHE_ERROR
    field.cache['images'] = field_images
    field.save()
    return field.cache['images']


def get_entry_image(entry):
    """
    Use cached Graph for given entry
    """
    default_image = open(DEFAULT_IMAGE_PATH, 'rb')
    if not entry.tabular_field:
        return default_image

    field = entry.tabular_field

    images = field.cache.get('images')

    if not images or not len(images) > 0:
        return default_image

    for image in images:
        if image.get('id') is not None and image.get('format') == 'png':
            file_id = images[0].get('id')
            return File.objects.get(pk=file_id).file
    return default_image
