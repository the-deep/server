import logging

from utils.common import create_plot_image

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud
except ImportError as e:
    logger.warning(f'ImportError: {e}')


@create_plot_image
def plot(x_label, y_label, data):
    # Create and generate a word cloud image:
    wordcloud = WordCloud(background_color="white").generate(data)

    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
