import argparse
import io
import os
import os.path
import subprocess

import pandas as pd
import sacrebleu
from dotenv import load_dotenv
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from ..common.common import call_translation, set_log_level, load_tmx_file
import logging

load_dotenv()


class Config:
    """
    Read from .env file - These are params that are static across parallel jobs
    """
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # Our Subscription key
    CATEGORIES = os.environ.get("CATEGORIES")  # The categories/model ids we are evaluating
    REGION = os.environ.get("REGION")  # The region our model is deployed in
    ALIGNER_PATH = os.environ.get("ALIGNER_PATH")  # The location of the alignment script
    # https://www.microsoft.com/en-us/download/details.aspx?id=52608&from=https%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fdownloads%2Faafd5dcf-4dcc-49b2-8a22-f7055113e656%2F
    DEBUG = bool(os.environ.get("DEBUG"))  # Activate debugging


def pdf_parser(data):
    """

    :param data: The file stream
    :return: The converted text
    """
    fp = open(data, 'rb')
    rsrc_mgr = PDFResourceManager()
    ret_str = io.StringIO()
    la_params = LAParams()
    device = TextConverter(rsrc_mgr, ret_str, laparams=la_params)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrc_mgr, device)
    # Process each page contained in the document.

    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
        data = ret_str.getvalue()

    return data


def build_HTML_aligned_report(categories, cat_sentences, lst_source_text, lst_target_txt, output_path, source_doc,
                              translated_doc):
    """
    This function generates a simple HTML page that is sentence aligned, per model, containing the HYP, REF and MT text
    :param categories: The models we are evaluating
    :param cat_sentences: The translated sentences per model
    :param lst_source_text: The HYP text
    :param lst_target_txt: The REF text
    :param output_path: The path we want to write to
    :param source_doc: The source document HYP we are translating
    :param translated_doc: The human translated REF doc
    :return:
    """

    for cat_id, category_id in enumerate(categories):

        for i, source_text in enumerate(lst_source_text):

            # Create a simple aligned html report
            html_file = open(os.path.join(output_path, 'MT_' + translated_doc[:-3] + '_' + category_id + '.html'), 'a')

            if i == 0:
                html = """<!DOCTYPE html><html lang = "en" ><head><meta charset = "UTF-8">"""
                html_file.write(html)

                html = """<title>""" + 'MT_' + translated_doc[:-3] + '_' + category_id + """</title>"""
                html_file.write(html)
                html = """</head><div>"""
                html_file.write(html)

                html = """<table id =""" + '"' + source_doc + '"' + """style = "border:1px solid; width:50%; 
                float:left" frame=void rules=rows><tr>"""
                html_file.write(html)
                html = """<td><u>""" + source_doc + """</u></td></tr>"""
                html_file.write(html)

            # Now we add a table row
            html = """<tr><td>ENU: """ + source_text + """</td></tr>"""
            html_file.write(html)
            html = """<tr><td>REF: """ + lst_target_txt[i] + """</td></tr>"""
            html_file.write(html)

            if i == len(lst_source_text) - 1:
                html = """</table>"""
                html_file.write(html)

        html = """<table id =""" + '"' + translated_doc + '"' + """style = "border:1px solid; width:50%; float:left"
        frame=void rules=rows><tr>"""
        html_file.write(html)
        html = """<td><u>""" + translated_doc + """</u></td></tr>"""
        html_file.write(html)

        # Now we add a table row
        for j, sentence in enumerate(cat_sentences[cat_id]):
            html = """<tr><td>MT: """ + sentence + """</td></tr>"""
            html_file.write(html)
            html = """<tr><td>REF: """ + lst_target_txt[j] + """</td></tr>"""
            html_file.write(html)

        html = """</table>"""
        html_file.write(html)
        html = """</div><body></body></html>"""
        html_file.write(html)
        html_file.close()
        logging.debug(f"Generated HTML report "
                      f"{str(os.path.join(output_path, 'MT_' + translated_doc[:-3] + '_' + category_id + '.html'))}")


def main():
    """
    This script takes a source document, reference translated document and:
    * Converts the PDF to text
    * Sentence aligns the source and reference documents
    * Translates the document sentence by sentence against all models
    * Generates various reports
    :return: Full text translation, CSV file with BLEU scores and text, HTML report with sentences only
    """
    # We pass these dynamic arguments in for parallel jobs
    parser = argparse.ArgumentParser(description='Process docs for machine translation')
    parser.add_argument('--translated-path', type=str,
                        help='path to translated documents')
    parser.add_argument('--source-path', type=str,
                        help='path to source documents')
    parser.add_argument('--translated-doc', type=str,
                        help='The translated document')
    parser.add_argument('--source-doc', type=str, default='',
                        help='The document to translate')
    parser.add_argument('--output-path', type=str, default='',
                        help='The output path for our translation scores and results')
    parser.add_argument('--target-language', type=str, default='',
                        help='es or fr')

    args = parser.parse_args()
    set_log_level(Config.DEBUG)

    translated_path = args.translated_path
    translated_doc = args.translated_doc
    source_path = args.source_path
    source_doc = args.source_doc
    output_path = args.output_path

    fr_text = pdf_parser(os.path.join(translated_path, translated_doc))
    en_text = pdf_parser(os.path.join(source_path, source_doc))

    source_text_doc = source_doc[:-3] + 'txt'
    translated_text_doc = translated_doc[:-3] + 'txt'

    with open(os.path.join(translated_path, translated_text_doc), 'w') as fr:
        fr.write(fr_text)

    with open(os.path.join(source_path, source_text_doc), 'w') as en:
        en.write(en_text)

    target_aligner = os.path.join(translated_path, translated_text_doc)
    source_aligner = os.path.join(source_path, source_text_doc)

    try:
        # Now we call the alignment Perl script
        pipe = subprocess.Popen(["perl", "align-sents-all.pl", source_aligner, target_aligner],
                                stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Config.ALIGNER_PATH).communicate()
    except Exception as align_error:
        logging.error(f"Error with alignment script {align_error}")

    source_aligned_doc = source_text_doc + '.aligned'
    translated_aligned_doc = translated_text_doc + '.aligned'

    with open(os.path.join(translated_path, translated_aligned_doc), 'r') as fr:
        fr_aligned = fr.read()

    with open(os.path.join(source_path, source_aligned_doc), 'r') as en:
        en_aligned = en.read()

    lst_fr_aligned = fr_aligned.split('\n')
    lst_en_aligned = en_aligned.split('\n')

    subscription_key = Config.SUBSCRIPTION_KEY

    categories = Config.CATEGORIES
    print(categories)
    categories = categories.strip().split(',')

    cat_dicts = [{} for category_id in categories]
    category_score = {}
    category_sentence = {}
    lst_target_txt = []
    lst_source_text = []
    lst_mt_score = []

    with open(os.path.join(output_path, 'MT_' + translated_doc[:-3] + '_all_models' + '.txt'),
              'w') as mt_file:

        for i, etxt in enumerate(lst_en_aligned):
            logging.debug(f"Processing {i} of {len(lst_en_aligned)}")
            hypothesis = lst_fr_aligned[i]
            lst_source_text.append(etxt)
            lst_target_txt.append(hypothesis)
            for cat_ind, category_id in enumerate(categories):
                category_id = category_id.strip()
                translation_results = call_translation([{'Text': etxt}], args.target_language, category_id,
                                                       subscription_key, Config.REGION)

                for translations in translation_results:
                    logging.info(f"CategoryId {category_id} translation {translations}")
                    for translation in translations['translations']:
                        translated_text = translation['text']
                        if len(translated_text) == 0:
                            bleu_score = 0
                            bleu_scores = 0
                        else:
                            bleu_scores = sacrebleu.corpus_bleu(hypothesis, translated_text)
                            bleu_score = bleu_scores.score
                        logging.info(f"*** Category {category_id}")
                        mt_file.write(f"\n*** Category {category_id}")
                        logging.info(f"ENG: {etxt}")
                        mt_file.write(f"\n ENG: {etxt}")
                        logging.info(f"REF: {hypothesis}")
                        mt_file.write(f"\n REF: {hypothesis}")
                        logging.info(f"MT : {translated_text}")
                        mt_file.write(f"\n MT : {translated_text}")
                        logging.info(f"{bleu_scores}")
                        logging.info(f"\n********************************")
                        cat_dicts[cat_ind][i] = []
                        cat_dicts[cat_ind][i].append(translated_text)
                        cat_dicts[cat_ind][i].append(bleu_score)
                        logging.info(f"_____________________")
                        logging.info('\n')

    cat_scores = [[] for category_id in categories]
    cat_sentences = [[] for category_id in categories]
    # This creates a text file for the translated document for each model
    for cat_id, category_id in enumerate(categories):
        with open(os.path.join(output_path, 'MT_' + translated_doc[:-3] + '_' + category_id + '.txt'),
                  'w') as mt_file:
            for key, value in cat_dicts[cat_id].items():
                cat_sentences[cat_id].append(value[0])
                cat_scores[cat_id].append(value[1])
                mt_file.write(value[0])

    data = {'Source': lst_source_text, 'Target': lst_target_txt}

    for cat_id, category_id in enumerate(categories):
        data[categories[cat_id] + '_score'] = cat_scores[cat_id]
        data[categories[cat_id] + '_sentence'] = cat_sentences[cat_id]

    df_translated = pd.DataFrame(data)

    df_translated.to_csv(os.path.join(output_path, 'MT_' + translated_doc[:-3] + 'csv'), sep=',')
    logging.debug(f"Generated CSV file {str(os.path.join(output_path, 'MT_' + translated_doc[:-3] + 'csv'))}")

    build_HTML_aligned_report(categories, cat_sentences, lst_source_text, lst_target_txt, output_path, args.source_doc,
                              args.translated_doc)


if __name__ == '__main__':
    main()
