# Document De-Duplication Scripts
There are two scripts:
1. `raw_trigrams.py` generates all present trigrams in the leadpreview documents in json format:
    ```
    {
        "en": { <trigram>: <trigram_count>, ... },
        "es": { <trigram>: <trigram_count>, ... },
        "fr": { <trigram>: <trigram_count>, ... }
    }
    ```
    It also prints out the documents statistics:
    ```
    {
        "en": { "count": <english docs count>, "corpus_length": <total_byte_size> },
        "es": { "count": <spanish docs count>, "corpus_length": <total_byte_size> },
        "fr": { "count": <french docs count>, "corpus_length": <total_byte_size> },
    }
    ```

2. `process_raw_trigrams.py` removes unnecessary/invalid trigrams from the documents and gives out csv containing trigrams and their relative frequencies


## Usage
Since these need to access `LeadPreview` model, these need to be run from django shell.

### Generate raw trigrams
This creates a json file containing all the trigrams present in the documents marked as specific language.
1. `python manage.py shell`
2. `from utils.document_deduplication.scripts.raw_trigrams import generate_trigrams`
3. `generate_trigrams("<raw_output_json_path>")`

### Generate language specific trigrams csvs
Note that the json created above might contain a lot of noises. For example a language marked english can also have other characters present.
This step removes the non-language trigrams.

`python process_raw_trigrams.py <raw_output_json_path>`
This will generate `<lang>-filtered.csv` and `<lang>-normalized.csv` for `en`, `es` and `fr`.
