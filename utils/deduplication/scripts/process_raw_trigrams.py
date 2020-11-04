import sys
import string
import json
import numpy as np

RAW_TRIGRAMS_PATH = 'trigrams_statistics_raw.json'
DOCUMENTS_SUMMARY_PATH = 'documents_summary.json'

ENGLISH = 'en'
SPANISH = 'es'
FRENCH = 'fr'

LANGS = [ENGLISH, SPANISH, FRENCH]

ENGLISH_ALPHABET = set(string.ascii_lowercase + string.digits + ' ')
SPANISH_ALPHABET = {*ENGLISH_ALPHABET, 'ñ'}
FRENCH_ALPHABET = {*ENGLISH_ALPHABET, *set('çéâêîôûàèìòùëïü')}


def all_digits(text) -> bool:
    text = text.strip()  # strip spaces
    for x in text:
        if x not in string.digits:
            return False
    return True


def all_nondigits(text) -> bool:
    for x in text:
        if x in string.digits:
            return False
    return True


def filter_non_alaphabetic_trigrams(all_trigrams):
    filtered_trigrams = {}
    filtered_trigrams[ENGLISH] = {
        k: v
        for k, v in all_trigrams[ENGLISH].items()
        if all(x in ENGLISH_ALPHABET for x in k) and (all_digits(k) or all_nondigits(k))  # Do not allow things like '2ba' or 'a2d' but allow ' 34' or '22 '
    }
    filtered_trigrams[SPANISH] = {
        k: v
        for k, v in all_trigrams[SPANISH].items()
        if all(x in SPANISH_ALPHABET for x in k) and (all_digits(k) or all_nondigits(k))
    }
    filtered_trigrams[FRENCH] = {
        k: v
        for k, v in all_trigrams[FRENCH].items()
        if all(x in FRENCH_ALPHABET for x in k) and (all_digits(k) or all_nondigits(k))
    }
    return filtered_trigrams


def normalize_all_trigrams(all_trigrams):
    totals = {
        lang: sum(v for v in all_trigrams[lang].values())
        for lang in LANGS
    }
    return {
        lang: {k: v / totals[lang] for k, v in all_trigrams[lang].items()}
        for lang in LANGS
    }


# NOT USED
def filter_significant_trigrams(all_trigrams, n=80):
    """ This calculates the standard deviation and returns values within n * sigma"""
    langs = [ENGLISH, SPANISH, FRENCH]
    means = {
        k: np.array(list(all_trigrams[k].values())).mean(dtype=np.float64)
        for k in langs
    }
    stds = {
        k: np.array(list(all_trigrams[k].values())).std(dtype=np.float64)
        for k in langs
    }
    print(means)
    print(stds)
    return {
        lang: {k: v for k, v in all_trigrams[lang].items() if v - means[lang] < -n * stds[lang]}
        for lang in langs
    }


def get_counts(all_trigrams):
    return {
        lang: len(all_trigrams[lang].keys())
        for lang in LANGS
    }


def write_to_file_key_vals(lang, data, prefix):
    with open(f'{lang}-{prefix}.csv', 'w') as f:
        for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True):
            f.write(f'{k},{v}\n')


def generate_csvs(raw_path=RAW_TRIGRAMS_PATH):
    with open(raw_path) as f:
        all_trigrams = json.load(f)
        print('Raw trigrams count:')
        print(get_counts(all_trigrams))
        filtered_trigrams = filter_non_alaphabetic_trigrams(all_trigrams)
        [write_to_file_key_vals(lang, filtered_trigrams[lang], 'filtered') for lang in LANGS]
        normalized_trigrams = normalize_all_trigrams(filtered_trigrams)
        [write_to_file_key_vals(lang, normalized_trigrams[lang], 'normalized') for lang in LANGS]
        print('Filtered trigrams count:')
        print(get_counts(normalized_trigrams))
        print('DONE!!')


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print('Usage: python process_raw_trigrams.py <raw_json_path>')
        exit()
    path = args[1]
    generate_csvs(path)
