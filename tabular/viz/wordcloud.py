import matplotlib.pyplot as plt
from utils.common import create_plot_image
from wordcloud import WordCloud


@create_plot_image
def plot(x_label, y_label, data):
    # Create and generate a word cloud image:
    wordcloud = WordCloud(background_color="white").generate(data)

    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
