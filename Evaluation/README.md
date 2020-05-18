# Translation pipeline

The following code is a scripted basic pipeline to translate and evaluate a document into a target language and 
evaluate it against the human translation. It generates numerous outputs including automated evaluation scores and
prepares formats of the translation for human evaluation.

## Overview
This script will perform the following:

1) Convert source and target pdf documents to UTF-8 encoded text documents
2) Run sentence alignment on both documents and generated aligned text documents
3) Translate each sentence against multiple models and evaluate BLEU scores against each model translation
4) Generates output reports for analysis

## Requirements

### The sentence alignment script

This code uses the [Bilingual Sentence Aligner](https://www.microsoft.com/en-us/download/details.aspx?id=52608&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Faafd5dcf-4dcc-49b2-8a22-f7055113e656%2F)
that must be downloaded and extracted to a directory. Note, when you train a model with the Custom Translation portal
the sentences will be [automatically aligned](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/sentence-alignment)
between the documents you are hoping to translate. We do this here so that
we can evaluate our models against our own test set against multiple models. 

### Python libraries

Ensure that the [required libraries](../requirements.txt) have been installed in your virtual environment.

## Input arguments

The script takes inputs from both an environment .env file for the more static arguments and accepts command line input
arguments for variable parameters as this script has been developed to run in parallel. 

### Environment parameters

These values need to be present in a file called .env within your script directory, note these are shared between 
numerous scripts and thus not all parameters in the file may be required for this script.

```bash
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # The Custom Translation Subscription key
    CATEGORIES = os.environ.get("CATEGORIES")  # The categories/model ids we are evaluating
    REGION = os.environ.get("REGION")  # The region our model is deployed in
    ALIGNER_PATH = os.environ.get("ALIGNER_PATH")  # The location of the Bilingual Sentence Aligner script 
    DEBUG = bool(os.environ.get("DEBUG"))  # Activate debugging if True verbose logging
```

#### Example environment parameters

The follow illustrates the format of the environment parameters in the .env file

```bash
CATEGORIES=127676767-SCIENCE-MODEL, 12873847384738-Custom-CUSTOM, 786384823748327482-Energy-ENERGY, 9848293489234-Government-GOVRMNT, 9823948239849234-Law-LAW
SUBSCRIPTION_KEY=[your_key]
REGION=westeurope
ALIGNER_PATH=/home/usr/aligner/bilingual-sentence-aligner/
DEBUG=true
```

Every model listed in CATEGORIES will be invoked against the target sentence for comparative evaluation. The region 
value should be populated if the Custom Translation service has only been deployed in a single region, for example for
data sovereignty purposes - see [Deploy a trained model](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/quickstart-build-deploy-custom-model#deploy-a-trained-model)

### Command line arguments

The following command line arguments are required:

```bash
--translated-path  # Path to the translated documents
--source-path      # Path to the source documents
--translated-doc   # The translated document
--source-doc       # The document to translate
--output-path      # The output path for our translation scores and results
--target-language  # The target language code e.g es for Spanish, fr for French)
```

The following illustrates how to invoke the python code with the command line arguments:

```python
python3 translation_pipeline.py --source-path /home/usr/translation/docs/en/ --translated-path /home/usr/translation/docs/fr/ 
--source-doc english.pdf --translated-doc french.pdf --output-path /home/usr/translation/docs/output_fr/
--target-language fr
```