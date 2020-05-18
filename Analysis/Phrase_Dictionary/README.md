# Phrase dictionary builder

The following code will build a phrase dictionary from a translation memory file using unsupervised techniques. We build
a Phrase Dictionary to translate common phrases that frequently occur within the documents. 
See [Phrase dictionary](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/what-is-dictionary#phrase-dictionary)

Note, we increment the Phrase Dictionary file, so this script can be run in batches and in parallel. 

## spaCy/texaCy approach overview

This approach uses both [spaCY](https://spacy.io/) and [textaCy](https://textacy.readthedocs.io/en/stable/index.html) to
identify key phrases to build the Phrase Dictionary. See the [Textrank algorithm](https://textacy.readthedocs.io/en/stable/api_reference/information_extraction.html#textrank)
for more details.

The script [build_phrase_dictionary_spacy.py](build_phrase_dictionary_spacy.py) will perform the following:

1) Load a tmx translation memory file
2) Load the spaCY models 
3) Perform the TextRank algorithm against both source and target languages to determine phrases
4) Check whether the Custom Translation matches the identified phrases, and it it matches, commit to the dictionary

## Requirements

A pre-trained Custom Translation model that performs well against your automated/human evaluation must exist as we will
invoke this model to help validate the key phrases identified. 

### The spaCY models

Firstly, the models must exist for both the source and target languages, navigate [here](https://spacy.io/models)
to see if the required language models are available and how to install them.

### Python libraries

Ensure that the [required libraries](../../requirements.txt) have been installed in your virtual environment.

## Input arguments

The script takes inputs from both an environment .env file for the more static arguments and accepts command line input
arguments for variable parameters as this script has been developed to run in parallel. 

### Environment parameters

These values need to be present in a file called .env within your script directory, note these are shared between 
numerous scripts and thus not all parameters in the file may be required for this script.

```bash
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # The Custom Translation Subscription key
    REGION = os.environ.get("REGION")  # The region our model is deployed in
    DEBUG = bool(os.environ.get("DEBUG"))  # Activate debugging if True verbose logging
```

#### Example environment parameters

The follow illustrates the format of the environment parameters in the .env file

```bash
SUBSCRIPTION_KEY=[your_key]
REGION=westeurope
DEBUG=true
```

### Command line arguments

The following command line arguments are required:

```bash
--source-tmx         # The input translation memory (tmx) file to process
--dictionary-path    # The input/output path for the phrase dictionary - we append to an already existing dictionary
--target-language    # The target language code e.g es for Spanish, fr for French
--category-id        # The best performing model against which to build the phrase dictionary
--nlp-id             # The source language spacy model e.g. en_core_web_md for English
--nlp-target         # The target language spacy model e.g. fr_core_news_md for French
--batch-start        # For running in batches - start at this number 
--batch-end          # For running in batches - end at this number
```

The following illustrates how to invoke the python code with the command line arguments:

```python
python3 translation_pipeline.py --source-path /home/usr/translation/docs/en/ --translated-path /home/usr/translation/docs/fr/ 
--source-doc english.pdf --translated-doc french.pdf --output-path /home/usr/translation/docs/output_fr/
--target-language fr
```