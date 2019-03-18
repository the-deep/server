import matplotlib.pyplot as plt
import plotly.graph_objs as go

from utils.common import create_plot_image, create_plotly_image


@create_plot_image
def plot(x_label, y_label, data, horizontal=False):
    chart_basic_config = {
        'width': 0.8,
        'color': 'teal',
    }
    if horizontal:
        data.plot.barh(**chart_basic_config)
        plt.locator_params(axis='y', nbins=24)
    else:
        data.plot.bar(**chart_basic_config)
        plt.locator_params(axis='x', nbins=39)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.gca().get_legend().remove()


@create_plotly_image
def plotly(data, horizontal=False):
    bar = go.Bar(
        x=data['count'] if horizontal else data['value'],
        y=data['value'] if horizontal else data['count'],
        marker=create_plotly_image.marker,
        orientation='h' if horizontal else 'v',
        opacity=0.8
    )
    return [bar], None
