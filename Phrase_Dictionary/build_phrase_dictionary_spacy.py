import argparse
import os

import spacy
import textacy
from textacy import ke
from dotenv import load_dotenv
from translate.storage.tmx import tmxfile
from ..common.common import call_translation, set_log_level, load_tmx_file, load_spacy_model, load_phrase_dictionary
import logging

load_dotenv()


class Config:
    """
    Read from .env file - These are params that are static across parallel jobs
    """
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # Our Subscription key
    REGION = os.environ.get("REGION")  # The region our model is deployed in
    DEBUG = bool(os.environ.get("DEBUG"))  # Activate debugging


def main():
    # We pass these dynamic arguments in for parallel jobs
    parser = argparse.ArgumentParser(description='Build a phrase dictionary using spaCy and TextaCy')
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
    set_log_level(Config.DEBUG)

    nlp_model_id = load_spacy_model(args.nlp_id)
    nlp_model_target = load_spacy_model(args.nlp_target)
    logging.debug(f"Loaded models {args.nlp_id} {args.nlp_target}")

    phrases = {}

    tmx_file = load_tmx_file(args.source_tmx)
    logging.debug(f"Loaded {args.source_tmx}")

    if os.path.isfile(os.path.join(args.dictionary_path, args.target_language + '_phrase_dictionary.txt')):
        phrase_file_name = str(os.path.join(args.dictionary_path, args.target_language + '_phrase_dictionary.txt'))
        phrase_file = load_phrase_dictionary(phrase_file_name, 'a')
        logging.debug(f"Found existing phrase dictionary {phrase_file_name}")
        phrase_list = [line.rstrip('\n') for line in open(phrase_file_name)]
        for line in phrase_list:
            lst_line = line.split(',')
            if len(lst_line[0]) > 0:
                phrases[lst_line[0]] = lst_line[1]

    else:
        phrase_file = load_phrase_dictionary(os.path.join(args.dictionary_path, args.target_language +
                                                          '_phrase_dictionary.txt'), 'a')

    for i, unit in enumerate(tmx_file.getunits()):

        if i < args.batch_start:
            continue

        if i > args.batch_end:
            break

        logging.info(f"Processing record {i} of {len(tmx_file.units)} (Batch start {args.batch_start} Batch end "
                     f"{args.batch_end})")

        nlp_id = nlp_model_id(unit.getid())
        nlp_target = nlp_model_target(unit.gettarget())
        res_id = ke.textrank(nlp_id, normalize='lemma', include_pos=('NOUN', 'PROPN', 'ADJ', 'VERB'), window_size=10,
                                     edge_weighting='binary', position_bias=False, topn=5)
        res_target = ke.textrank(nlp_target, normalize='lemma', include_pos=('NOUN', 'PROPN', 'ADJ', 'VERB'),
                                         window_size=5, edge_weighting='binary', position_bias=False, topn=10)

        for r_id in res_id:
            if (len(r_id[0].split()) > 1) and (len(res_target) > 0):  # We don't want single words, we want phrases
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
                                    bleu_score = 1  # We use absolute matches but keep this here for BLEU if needed
                                    print(f"Found {r_id[0]} : {r_tar[0].strip()}")
                                    phrases[r_id[0]] = r_tar[0].strip()
                                    # As the phrase dictionary is case sensitive, let's include a few variations
                                    phrase_file.write('\n' + r_id[0] + ', ' + r_tar[0].strip())
                                    phrase_file.write('\n' + r_id[0].lower() + ', ' + r_tar[0].strip().lower())
                                    phrase_file.write('\n' + r_id[0].upper() + ', ' + r_tar[0].strip().upper())
                                # TODO add BLEU evaluation if needed
    phrase_file.close()


if __name__ == '__main__':
    main()
