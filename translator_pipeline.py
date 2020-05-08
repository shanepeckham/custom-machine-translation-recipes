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
from common import call_translation

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


def pdf_parser(data):
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


def main():
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
        print(f"Error with alignment script {align_error}")

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
            print(f"Processing {i} of {len(lst_en_aligned)}")
            hypothesis = lst_fr_aligned[i]
            lst_source_text.append(etxt)
            lst_target_txt.append(hypothesis)
            for cat_ind, category_id in enumerate(categories):
                category_id = category_id.strip()
                translation_results = call_translation([{'Text': etxt}], args.target_language, category_id,
                                                       subscription_key, Config.REGION)

                for translations in translation_results:
                    print(f"CategoryId {category_id} translation {translations}")
                    for translation in translations['translations']:
                        translated_text = translation['text']
                        if len(translated_text) == 0:
                            bleu_score = 0
                        else:
                            bleu_scores = sacrebleu.corpus_bleu(hypothesis, translated_text)
                            bleu_score = bleu_scores.score
                        print(f"*** Category {category_id}")
                        mt_file.write(f"\n*** Category {category_id}")
                        print(f"ENG: {etxt}")
                        mt_file.write(f"\n ENG: {etxt}")
                        print(f"REF: {hypothesis}")
                        mt_file.write(f"\n REF: {hypothesis}")
                        print(f"MT : {translated_text}")
                        mt_file.write(f"\n MT : {translated_text}")
                        print(f"{bleu_scores}")
                        print(f"\n********************************")
                        cat_dicts[cat_ind][i] = []
                        cat_dicts[cat_ind][i].append(translated_text)
                        cat_dicts[cat_ind][i].append(bleu_score)
                        print(f"_____________________")
                        print('\n')

    cat_scores = [[] for category_id in categories]
    cat_sentences = [[] for category_id in categories]
    # This creates a text file for the translated model for each model
    for cat_id, category_id in enumerate(categories):
        with open(os.path.join(output_path, 'MT_' + translated_doc[:-3] + '_' + category_id + '.txt'),
                  'w') as mt_file:
            for key, value in cat_dicts[cat_id].items():
                cat_sentences[cat_id].append(value[0])
                cat_scores[cat_id].append(value[1])
                mt_file.write(value[0])

    data = {'Source': lst_source_text, 'Target': lst_target_txt}

    print(len(lst_source_text), len(lst_target_txt), len(cat_scores), len(cat_sentences))

    for cat_id, category_id in enumerate(categories):
        data[categories[cat_id] + '_score'] = cat_scores[cat_id]
        data[categories[cat_id] + '_sentence'] = cat_sentences[cat_id]

    df_translated = pd.DataFrame(data)

    df_translated.to_csv(os.path.join(output_path, 'MT_' + translated_doc[:-3] + 'csv'), sep=',')


if __name__ == '__main__':
    main()
