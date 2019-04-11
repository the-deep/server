import matplotlib.pyplot as plt
import plotly.graph_objs as go
from utils.common import create_plot_image, create_plotly_image


@create_plot_image
def plot(x_label, y_label, data):
    # data.plot.hist(color='teal', edgecolor='white', linewidth=0.4)
    data.plot.hist(color='teal')
    plt.ylabel(y_label)
    plt.xlabel(x_label)


@create_plotly_image
def plotly(data):
    histogram = go.Histogram(
        x=data,
        marker=create_plotly_image.marker,
        opacity=0.8,
    )
    return [histogram], None
