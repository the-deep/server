from . import (
    date_widget,
    date_range_widget,
    time_widget,
    time_range_widget,
    number_widget,
    scale_widget,
    select_widget,
    multiselect_widget,
    geo_widget,
    organigram_widget,
    matrix1d_widget,
    matrix2d_widget,
    number_matrix_widget,
    conditional_widget,
    text_widget,
)


widget_store = {
    date_widget.WIDGET_ID: date_widget,
    date_range_widget.WIDGET_ID: date_range_widget,
    time_widget.WIDGET_ID: time_widget,
    time_range_widget.WIDGET_ID: time_range_widget,
    'numberWidget': number_widget,
    scale_widget.WIDGET_ID: scale_widget,
    geo_widget.WIDGET_ID: geo_widget,
    # TODO: import the rest rather defining here
    'selectWidget': select_widget,
    'multiselectWidget': multiselect_widget,
    'organigramWidget': organigram_widget,
    'matrix1dWidget': matrix1d_widget,
    'matrix2dWidget': matrix2d_widget,
    'numberMatrixWidget': number_matrix_widget,
    conditional_widget.WIDGET_ID: conditional_widget,
    'textWidget': text_widget,
}
