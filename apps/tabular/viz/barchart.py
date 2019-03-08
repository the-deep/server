import matplotlib.pyplot as plt
from utils.common import create_plot_image


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
