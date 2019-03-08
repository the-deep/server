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
    'barchart': barchart.plot,
    'barcharth': lambda *args, **kwargs: barchart.plot(*args, **kwargs, horizontal=True),
    'map': mapViz.plot,

    # Frequency data not required
    'histograms': histograms.plot,
    'wordcloud': wordcloud.plot,
}


def clean_real_data(data, val_column):
    """
    Return clean_dataframe, original_dataframe
    """

    # NOTE: The folloing loop adds the keys empty and invalid if not present
    # TODO: Handle the following case from pandas itself
    for datum in data:
        if datum.get('empty') is None:
            datum['empty'] = False
        if datum.get('invalid') is None:
            datum['invalid'] = False

    df = pd.DataFrame(data)
    filterd_df = df[~(df['empty'] == True) & ~(df['invalid'] == True)]  # noqa
    return filterd_df, df


def calc_data(field):
    val_column = 'processed_value' if field.type == 'geo' else 'value'

    data, df = clean_real_data(field.data, val_column)

    if val_column not in data.columns:
        logger.warning('{} not present'.format(val_column))
        return None, {}

    data = data.groupby(val_column).count()['empty'].sort_values().to_frame()
    data = data.rename(columns={'empty': 'count', val_column: 'value'})

    if data.empty:
        logger.warn('Empty DataFrame: no numeric data to calculate')
        return [], {}

    data['value'] = data.index
    health_stats = {
        'empty': int(df[df['empty'] == True]['empty'].count()), # noqa
        'invalid': int(df[df['invalid'] == True]['invalid'].count()), # noqa
        'total': int(df[val_column].count()),
    }
    return data.to_dict(orient='records'), health_stats


def generate_chart(field, chart_type='barchart'):
    val_column = 'processed_value' if field.type == 'geo' else 'value'

    if field.type == 'geo':
        chart_type = 'map'
    elif field.type == 'number':
        chart_type = 'histograms'

    params = {
        'x_label': field.title,
        'y_label': None,
        'chart_size': (8, 4),
    }

    if chart_type not in ['histograms', 'wordcloud']:
        df = pd.DataFrame(field.cache.get('series'))
        df.set_index('value', inplace=True)
        params['data'] = df
    else:
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


def _add_image_to_gallery(image_name, image):
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


def render_field_chart(field):
    """
    Save normalized data to field
    """
    image, chart_type = generate_chart(field)

    if image:
        file = _add_image_to_gallery(
            'tabular_{}_{}'.format(field.sheet.id, field.id),
            image,
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
