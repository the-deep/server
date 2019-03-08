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


def generate(title, series, data_type, chart_type='barchart'):
    val_column = 'processed_value' if data_type == 'geo' else 'value'

    if data_type == 'geo':
        chart_type = 'map'
    elif data_type == 'number':
        chart_type = 'histograms'

    # NOTE: The folloing loop adds the keys empty and invalid if not present
    # TODO: Handle the following case from pandas itself
    for data in series:
        if data.get('empty') is None:
            data['empty'] = False
        if data.get('invalid') is None:
            data['invalid'] = False

    df = pd.DataFrame(series)

    if val_column not in df.columns:
        logger.warning('{} not present'.format(val_column))
        return None, chart_type

    data = df[~(df['empty'] == True) & ~(df['invalid'] == True)]  # noqa
    data = data.groupby(val_column).count()['empty'].sort_values().to_frame()
    data = data.rename(columns={'empty': 'count', val_column: 'value'})

    if data.empty:
        logger.warn('Empty DataFrame: no numeric data to plot')
        return None, chart_type, None

    params = {
        'x_label': title,
        'y_label': None,
        'data': data,
        'chart_size': (8, 4),
    }

    image = None
    # frequency data required
    if (chart_type == 'barchart'):
        image = barchart.plot(**params)
    elif (chart_type == 'barcharth'):
        image = barchart.plot(**params, horizontal=True)
    elif (chart_type == 'map'):
        image = mapViz.plot(**params)

    # Frequency data not required
    elif (chart_type == 'histograms'):
        df[val_column] = pd.to_numeric(df[val_column])
        params['data'] = df[val_column]
        image = histograms.plot(**params)
    elif (chart_type == 'wordcloud'):
        params['data'] = ' '.join(df['value'].values)
        image = wordcloud.plot(**params)

    data['value'] = data.index
    return image, chart_type, {
        'series': data.to_dict(orient='records'),
        'health_stats': {
            'empty': int(df[df['empty'] == True]['empty'].count()), # noqa
            'invalid': int(df[df['invalid'] == True]['invalid'].count()), # noqa
            'total': int(df[val_column].count()),
        },
    }


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


def sheet_field_render(field):
    """
    Prerender Graphs and save normalized data to field
    """
    title = field.title
    series = field.data
    data_type = field.type

    try:
        # Move preprocessing to seperate task
        image, chart_type, processed_data = generate(title, series, data_type)
        status = Field.CACHE_SUCCESS
    except Exception:
        status = Field.CACHE_ERROR
        logger.error(
            'Failed to calculate processed data for field({})'.format(
                field.id,
            ),
            exc_info=1,
        )

    if image:
        file = _add_image_to_gallery(
            'tabular_{}_{}'.format(field.sheet.id, field.id),
            image,
        )
        images = [{'id': file.id, 'chart_type': chart_type}]
    else:
        images = [{'id': None, 'chart_type': chart_type}]
    field.cache = {
        'status': status,
        'series': processed_data.get('series', []),
        'health_stats': processed_data.get('health_stats'),
        'images': images,
    }
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
