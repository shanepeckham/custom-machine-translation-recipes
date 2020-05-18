from unittest import TestCase

import logging
import subprocess
import spacy
from translate.storage.tmx import tmxfile


class TestRecipesCommon(TestCase):

    def test_load_spacy_model(self):
        """
        Loads the spaCy model
        :param model: The model we want to load
        :return: The loaded spaCy model
        """
        import en_core_web_sm
        nlp_model = en_core_web_sm.load()
        assert nlp_model is not None

    def test_load_tmx_file(source_language=None, target_language=None):
        """
        Loads the tmx file
        :param file: The tmx memory file to open
        :param source_language: The source language we are translating
        :param target_language: The target language we are translating to
        :return: The tmx file XML file as a translation.storage.tmx object
        """
        file = 'Data/en_es.tmx'
        with open(file, 'rb') as tmx:
            tmx_file = tmxfile(tmx, 'en-GB', 'es-ES')  # TODO This does not affect what is loaded

        unit_zero = "CONVENTION ON A COMMON TRANSIT PROCEDURE"
        assert str(tmx_file.getunits()[0].getid()) == unit_zero

    def test_call_sentence_alignment(self, source_aligner='Data/english.txt', target_aligner="Data/spanish.txt",
                                     aligner_path="../Aligner"):
        """
        This invokes the Microsoft Bilingual Sentence Aligner perl script
        see https://www.microsoft.com/en-us/download/details.aspx?id=52608&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Faafd5dcf-4dcc-49b2-8a22-f7055113e656%2F
        :param source_aligner: The source language document
        :param target_aligner: The target language document
        :param aligner_path: The path where the Microsoft Bilingual Sentence Aligner perl script
        :return: pipe - The subprocess result
        """

        with open(source_aligner, 'r') as source:
            source_file = source.read()

        with open(target_aligner, 'r') as target:
            target_file = target.read()

        pipe = None
        try:
            # Now we call the alignment Perl script
            pipe = subprocess.Popen(["perl", "align-sents-all.pl", source_file, target_file],
                                    stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=aligner_path).communicate()
        except Exception as align_error:
            logging.error(f"Error with alignment script {align_error}")

        assert pipe is not None

    pass
