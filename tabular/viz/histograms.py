import matplotlib.pyplot as plt
from utils.common import create_plot_image


@create_plot_image
def plot(x_label, y_label, data):
    # data.plot.hist(color='teal', edgecolor='white', linewidth=0.4)
    data.plot.hist(color='teal')
    plt.ylabel(y_label)
    plt.xlabel(x_label)
