from requests import post


def call_translation(text, language_code, category_id, subscription_key, region):

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