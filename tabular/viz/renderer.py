import pandas as pd
import logging

from gallery.models import File
from tabular.models import (
    Field,
)
from tabular.viz import (
    barchart,
    wordcloud,
    histograms,
    map,
)


logger = logging.getLogger(__name__)


def generate(title, series, data_type, chart_type='barchart'):
    val_column = 'processed_value' if data_type == 'geo' else 'value'

    # NOTE: The folloing loop adds the keys empty and invalid if not present
    # TODO: Handle the following case from pandas itself
    for data in series:
        if data.get('empty') is None:
            data['empty'] = False
        if data.get('invalid') is None:
            data['invalid'] = False

    df = pd.DataFrame(series)

    if val_column not in df.columns:
        logger.warn('{} not present'.format(val_column))
        return

    df = df[~(df['empty'] == True) & ~(df['invalid'] == True)]  # noqa
    data = df.groupby(val_column).count()['empty'].sort_values().to_frame()
    data = data.rename(columns={'empty': 'count', val_column: 'value'})

    params = {
        'x_label': title,
        'y_label': None,
        'data': data,
        'chart_size': (8, 4),
    }

    if data_type == 'geo':
        chart_type = 'map'
    elif data_type == 'number':
        chart_type = 'histograms'

    image = None
    if (chart_type == 'barchart'):
        image = barchart.plot(**params)
    elif (chart_type == 'barcharth'):
        image = barchart.plot(**params, horizontal=True)
    elif (chart_type == 'histograms'):
        df[val_column] = pd.to_numeric(df[val_column])
        params['data'] = df[val_column]
        image = histograms.plot(**params)
    elif (chart_type == 'wordcloud'):
        params['data'] = ' '.join(df['value'].values)
        image = wordcloud.plot(**params)
    elif (chart_type == 'map'):
        image = map.plot(**params)

    return image, chart_type


def _add_image_to_gallery(image_name, image):
    file = File.objects.create(
        title=image_name,
        mime_type='image/png',
    )
    file.file.save(image_name, image)
    logger.info(
        'Added image to tabular gallery {}(id={})'.format(image_name, file.id),
    )
    return file


def sheet_field_render(sheet, field_id):
    field = Field.objects.get(pk=field_id)
    title = field.title
    series = field.data
    data_type = field.type

    image, chart_type = generate(title, series, data_type)
    file = _add_image_to_gallery(
        'tabular_{}_{}'.format(sheet.id, field.id),
        image,
    )
    field.options['images'] = [{'id': file.id, 'chart_type': chart_type}]
    field.save()
    return field.options['images']


def get_entry_image(entry):
    ds = entry.data_series
    images = ds.get('options', {}).get('images', [])
    if len(images) > 0:
        if not images[0].get('id'):
            return None
        image = File.objects.get(pk=images[0].get('id')).file
    else:
        title = ds.get('title')
        series = ds.get('data', [])
        data_type = ds.get('type')
        image, chart_type = generate(title, series, data_type)
        if image:
            file = _add_image_to_gallery(
                'tabular_entry_{}'.format(entry.id),
                image,
            )
            entry.data_series['options']['images'] = [
                {'id': file.id, 'chart_type': chart_type},
            ]
        else:
            entry.data_series['options']['image_id'] = [
                {'id': None, 'chart_type': chart_type},
            ]
        entry.save()
    return image
