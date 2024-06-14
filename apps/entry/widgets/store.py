from . import (
    conditional_widget,
    date_range_widget,
    date_widget,
    geo_widget,
    matrix1d_widget,
    matrix2d_widget,
    multiselect_widget,
    number_matrix_widget,
    number_widget,
    organigram_widget,
    scale_widget,
    select_widget,
    text_widget,
    time_range_widget,
    time_widget,
)

widget_store = {
    widget.WIDGET_ID: widget
    for widget in (
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
}
