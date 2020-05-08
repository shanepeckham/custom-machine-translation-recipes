import argparse
import os

import spacy
import textacy
from dotenv import load_dotenv
from translate.storage.tmx import tmxfile

from common import call_translation

load_dotenv()


class Config:
    """
    Read from .env file - These are params that are static across parallel jobs
    """
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # Our Subscription key
    REGION = os.environ.get("REGION")  # The region our model is deployed in


def main():
    # We pass these dynamic arguments in for parallel jobs
    parser = argparse.ArgumentParser(description='Process docs for machine translation')
    parser.add_argument('--source-tmx', type=str, default='',
                        help='The input tmx file to process')
    parser.add_argument('--dictionary-path', type=str, default='',
                        help='The input/output path for the phrase dictionary')
    parser.add_argument('--target-language', type=str, default='',
                        help='es or fr')
    parser.add_argument('--category-id', type=str, default='',
                        help='The model against which to build the phrase dictionary')
    parser.add_argument('--nlp-id', type=str, default='',
                        help='The source language spacy model e.g. en_core_web_md')
    parser.add_argument('--nlp-target', type=str, default='',
                        help='The target language spacy model e.g. fr_core_news_md')
    parser.add_argument('--batch-start', type=int, default=0, metavar='N',
                        help='start at this number + batch-size')
    parser.add_argument('--batch-end', type=int, default=100, metavar='N',
                        help='end at this number')

    args = parser.parse_args()

    nlp_model_id = spacy.load(args.nlp_id)
    nlp_model_target = spacy.load(args.nlp_target)

    phrases = {}

    with open(args.source_tmx, 'rb') as tmx:
        tmx_file = tmxfile(tmx, 'en-GB', 'fr-FR')  # TODO This does not affect what is loaded it seems

    if os.path.isfile(os.path.join(args.dictionary_path, args.target_language + '_phrase_dictionary.txt')):
        phrase_file_name = str(os.path.join(args.dictionary_path, args.target_language + '_phrase_dictionary.txt'))
        phrase_file = open(phrase_file_name, 'a')
        phrase_list = [line.rstrip('\n') for line in open(phrase_file_name)]
        for line in phrase_list:
            lst_line = line.split(',')
            if len(lst_line[0]) > 0:
                phrases[lst_line[0]] = lst_line[1]

    else:
        phrase_file = open(os.path.join(args.dictionary_path, args.target_language + '_phrase_dictionary.txt'), 'a')

    for i, unit in enumerate(tmx_file.units):

        if i < args.batch_start:
            continue

        if i > args.batch_end:
            break

        print(f"Processing record {i} of {len(tmx_file.units)} Batch start {args.batch_start} Batch end "
              f"{args.batch_end}")

        nlp_id = nlp_model_id(unit.getid())
        nlp_target = nlp_model_target(unit.gettarget())
        res_id = textacy.ke.textrank(nlp_id, normalize='lemma', include_pos=('NOUN', 'PROPN', 'ADJ'), window_size=10,
                                     edge_weighting='binary', position_bias=True, topn=10)
        res_target = textacy.ke.textrank(nlp_target, normalize='lemma', include_pos=('NOUN', 'PROPN', 'ADJ'),
                                         window_size=10, edge_weighting='binary', position_bias=False, topn=10)

        for r_id in res_id:
            if len(r_id[0].split()) > 1:
                if not r_id[0] in phrases:
                    translation_results = call_translation([{'Text': r_id[0]}], args.target_language,
                                                           args.category_id, Config.SUBSCRIPTION_KEY, Config.REGION)
                    if len(translation_results[0]['translations'][0]) > 0:
                        for r_tar in res_target:
                            if len(r_tar[0].split()) > 1:
                                bleu_score = 0
                                # Let's only take exact matches
                                if r_tar[0].lower().strip() == translation_results[0]['translations'][0][
                                    'text'].lower().strip():
                                    bleu_score = 1
                                    print(f"Found {r_id[0]} : {r_tar[0].strip()}")
                                    phrases[r_id[0]] = r_tar[0].strip()
                                    phrase_file.write('\n' + r_id[0] + ', ' + r_tar[0].strip())
                                    phrase_file.write('\n' + r_id[0].lower() + ', ' + r_tar[0].strip().lower())
                                    phrase_file.write('\n' + r_id[0].upper() + ', ' + r_tar[0].strip().upper())
                                # TODO add BLEU evaluation if needed
    phrase_file.flush()
    phrase_file.close()


if __name__ == '__main__':
    main()