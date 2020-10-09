import json
import requests
from flask_babel import _


def translate(text, source_language, dest_language):
    r = requests.get(
        'http://translate.google.cn/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl={}&tl={}&q={}'.format(
            source_language, dest_language, text
        ))
    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8'))['sentences'][0]['trans']
