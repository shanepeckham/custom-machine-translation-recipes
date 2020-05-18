# Custom machine translation recipes

![Python package](https://github.com/shanepeckham/custom-machine-translation-recipes/workflows/Python%20package/badge.svg)

This repository contains code samples to help train and optimise a custom translation model on Azure,
see [Custom Translator Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/overview)
for more info.

## Overview
This repo contains the following:

| Stage | Scenario | Description |
| -------- | ----------- | ------|
| Analysis | [Creating datasets](Analysis/Translation-Memory-to-datasets.ipynb) | Cleaning Translation memory files and generate train/test/tune datasets
| Analysis | [Generate Phrase Dictionary](Analysis/Phrase_Dictionary/README.md) | Illustrates unsupervised approaches to building a Phrase Dictionary
| Evaluation | [Translator pipeline](Evaluation/translator_pipeline.py) | A full source to target language multi-model evaluation pipeline
| Evaluation | [Evaluate and compare model results](Evaluation/Evaluate-Results.ipynb) | Aggregate and compare all model results

## Getting Started

The order in which to run these scripts is as follows:

1) Start by creating your [datasets](Analysis/Translation-Memory-to-datasets.ipynb)
2) Train your models on these datasets using different base language models per language
3) [Evaluate all models](Evaluation/translator_pipeline.py) against your test document set
4) [Select the best model](Evaluation/Evaluate Results.ipynb) - include human evaluation
5) [Generate a Phrase dictionary](Analysis/Phrase_Dictionary/README.md) using your best model
6) Consider creating a [stylistic accurate tuning dataset](https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/training-and-model#tuning-document-type-for-custom-translator)
7) Retrain the model using the Phrase Dictionary and optimised tuning set