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
    number_widget.WIDGET_ID: number_widget,
    scale_widget.WIDGET_ID: scale_widget,
    geo_widget.WIDGET_ID: geo_widget,
    # TODO: import the rest rather defining here
    select_widget.WIDGET_ID: select_widget,
    multiselect_widget.WIDGET_ID: multiselect_widget,
    organigram_widget.WIDGET_ID: organigram_widget,
    matrix1d_widget.WIDGET_ID: matrix1d_widget,
    matrix2d_widget.WIDGET_ID: matrix2d_widget,
    number_matrix_widget.WIDGET_ID: number_matrix_widget,
    conditional_widget.WIDGET_ID: conditional_widget,
    text_widget.WIDGET_ID: text_widget,
}