# Copyright 2021 Mufeed Ali
# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import httpx
from langdetect import detect_langs, DetectorFactory

from dialect.translators.basetrans import Detected, TranslatorBase, TranslationError, Translation

DetectorFactory.seed = 0


class LibreTranslator(TranslatorBase):
    name = 'libretranslate'
    client = None
    history = []
    languages = {}
    supported_features = {
        'mistakes': False,
        'pronunciation': False,
        'voice': False,
        'change-instance': True,
    }
    base_url = ''

    def __init__(self, base_url=None, **kwargs):
        if base_url is not None:
            self.base_url = base_url

        self.client = httpx.Client()
        try:
            r = self.client.get(self.lang_url)
        except:
            r = self.client.get('https://translate.astian.org/languages')
        for lang in r.json():
            self.languages[lang['code']] = lang['name']

    @property
    def translate_url(self):
        return 'https://' + self.base_url + '/translate'

    @property
    def lang_url(self):
        return 'https://' + self.base_url + '/languages'

    def detect(self, src_text):
        """Detect the language using the same mechanisms that LibreTranslate uses but locally."""
        try:
            candidate_langs = list(
                filter(lambda l: l.lang in self.languages, detect_langs(src_text))
            )

            if len(candidate_langs) > 0:
                candidate_langs.sort(key=lambda l: l.prob, reverse=True)

                source_lang = next(
                    iter(
                        [
                            l
                            for l in self.languages.keys()
                            if l == candidate_langs[0].lang
                        ]
                    ),
                    None,
                )
                if not source_lang:
                    source_lang = 'en'
            else:
                source_lang = 'en'

            detected_object = Detected(source_lang, 1.0)
            return detected_object
        except Exception as e:
            raise TranslationError(e)

    def translate(self, src_text, src, dest):
        try:
            r = self.client.post(
                self.translate_url,
                data={
                    'q': src_text,
                    'source': src,
                    'target': dest,
                },
            )
            return Translation(
                r.json()['translatedText'],
                {
                    'possible-mistakes': None,
                    'translation': [],
                },
            )
        except Exception as e:
            raise TranslationError(e)