import pandas as pd
import logging

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


CHART_RENDER = {
    # frequency data required
    'barchart': barchart.plotly,
    'barcharth': lambda *args, **kwargs: barchart.plotly(*args, **kwargs, horizontal=True),
    'map': mapViz.plot,

    # Frequency data not required
    'histograms': histograms.plotly,
    'wordcloud': wordcloud.plot,
}


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
    val_column = 'processed_value' if field.type == 'geo' else 'value'

    data, df = clean_real_data(field.data, val_column)

    if data.empty:
        logger.warn('Empty DataFrame: no numeric data to calculate')
        return [], {}

    if val_column not in data.columns:
        logger.warning('{} not present'.format(val_column))
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


def generate_chart(field, chart_type='barchart', image_format='svg'):
    if field.type == 'geo':
        chart_type = 'map'
    elif field.type == 'number':
        chart_type = 'histograms'

    params = {
        'x_label': field.title,
        'y_label': 'count',
        'chart_size': (8, 4),
        'format': image_format,
        # data will be added according to chart type
    }

    if chart_type not in ['histograms', 'wordcloud']:
        df = pd.DataFrame(field.cache.get('series'))
        if df.empty or 'value' not in df.columns:
            return None, {}
        params['data'] = df
    else:
        val_column = 'processed_value' if field.type == 'geo' else 'value'
        df, _ = clean_real_data(field.data, val_column)
        if chart_type == 'histograms':
            params['data'] = pd.to_numeric(df[val_column])
        elif chart_type == 'wordcloud':
            params['data'] = ' '.join(df[val_column].values)

    if isinstance(params['data'], pd.DataFrame) and params['data'].empty:
        logger.warn('Empty DataFrame: no numeric data to plot')
        return None, {}

    chart_render = CHART_RENDER.get(chart_type)
    if chart_render:
        try:
            image = chart_render(**params)
        except Exception:
            logger.error('Tabular Chart Render Error', exc_info=1)
            return None, chart_type
        return image, chart_type
    return None, chart_type


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
    except Exception:
        cache = {'status': Field.CACHE_ERROR}
        logger.error(
            'Failed to calculate processed data for field({})'.format(
                field.id,
            ),
            exc_info=1,
        )

    field.cache = cache
    field.save()
    return field.cache['status']


def _add_image_to_gallery(image_name, image, mime_type):
    file = File.objects.create(
        title=image_name,
        mime_type='image/png',
        metadata={'tabular': True},
    )
    file.file.save(image_name, image)
    logger.info(
        'Added image to tabular gallery {}(id={})'.format(image_name, file.id),
    )
    return file


def render_field_chart(field):
    """
    Save normalized data to field
    """
    image_format = 'png'
    image_mime = 'image/png'
    image, chart_type = generate_chart(field, image_format=image_format)

    if image:
        file = _add_image_to_gallery(
            'tabular_{}_{}.{}'.format(field.sheet.id, field.id, image_format),
            image,
            mime_type=image_mime,
        )
        images = [{'id': file.id, 'chart_type': chart_type}]
    else:
        images = [{'id': None, 'chart_type': chart_type}]
    field.cache['images'] = images
    field.save()
    return field.cache['images']


def get_entry_image(entry):
    """
    Use cached Graph for given entry
    """
    if not entry.tabular_field:
        return None

    field = entry.tabular_field

    images = field.cache.get('images')
    if not images or not len(images) > 0 or not images[0].get('id'):
        return None
    file_id = images[0].get('id')
    return File.objects.get(pk=file_id).file
