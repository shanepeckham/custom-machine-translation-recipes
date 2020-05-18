from requests import post
import logging
from translate.storage.tmx import tmxfile
import spacy
import subprocess


def set_log_level(debug):
    """

    :param debug: Boolean value
    :return: None
    """
    if bool(debug):
        logging.basicConfig(level=logging.DEBUG)


def call_translation(text, language_code, category_id, subscription_key, region):
    """

    :param text: The text to be translated
    :param language_code: The target language to translate to
    :param category_id: The category Id of the Machine Translation model
    :param subscription_key: The Subscription Key for the Custom Machine Translation service
    :param region: The Region that the model is deployed to
    :return: The translated text in a json object
    """

    analyze_result_response = None

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Region": region
    }

    try:
        url = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=' + language_code + \
              '&category=' + category_id
        resp = post(url=url, json=text, headers=headers)
        analyze_result_response = resp.json()

    except Exception as e:
        print('Exception Translate', e)

    return analyze_result_response


def load_tmx_file(file, source_language=None, target_language=None):
    """
    Loads the tmx file
    :param file: The tmx memory file to open
    :param source_language: The source language we are translating
    :param target_language: The target language we are translating to
    :return: The tmx file XML file as a translation.storage.tmx object
    """

    with open(file, 'rb') as tmx:
        tmx_file = tmxfile(tmx, 'en-GB', 'fr-FR')  # TODO This does not affect what is loaded

    return tmx_file


def load_spacy_model(model):
    """
    Loads the spaCy model
    :param model: The model we want to load
    :return: The loaded spaCy model
    """
    nlp_model = spacy.load(model)
    return nlp_model


def load_phrase_dictionary(file, mode):
    """
    Loads a phrase dictionary
    :param file: The phrase dictionary to open
    :param mode: Mode w, a, r - write, append, read
    :return: The loaded phrase dictionary
    """
    phrase_dict = open(file, mode)
    return phrase_dict


def call_sentence_alignment(source_aligner, target_aligner, aligner_path):
    """
    This invokes the Microsoft Bilingual Sentence Aligner perl script
    see https://www.microsoft.com/en-us/download/details.aspx?id=52608&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Faafd5dcf-4dcc-49b2-8a22-f7055113e656%2F
    :param source_aligner: The source language document
    :param target_aligner: The target language document
    :param aligner_path: The path where the Microsoft Bilingual Sentence Aligner perl script
    :return: pipe - The subprocess result
    """

    pipe = None
    try:
        # Now we call the alignment Perl script
        pipe = subprocess.Popen(["perl", "align-sents-all.pl", source_aligner, target_aligner],
                                stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=aligner_path).communicate()
    except Exception as align_error:
        logging.error(f"Error with alignment script {align_error}")

    return pipe
