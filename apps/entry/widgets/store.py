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
