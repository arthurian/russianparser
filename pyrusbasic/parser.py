# -*- coding: utf-8 -*-
import string
import re
import unicodedata
import collections
import pygtrie

from pyrusbasic.const import (
    RUS_ALPHABET_STR,
    RUS_ALPHABET_SET,
    COMBINING_ACCENT_CHAR,
    COMBINING_BREVE_CHAR,
    COMBINING_DIURESIS_CHAR,
    EN_DASH_CHAR,
    HYPHEN_CHAR
)

RE_WHITESPACE_ONLY = re.compile(r'^\s+$')
TRANSLATOR_PUNCT_REMOVE = str.maketrans('', '', string.punctuation)

class Word(object):
    TYPE_NONE = 0
    TYPE_WORD = 1
    TYPE_HYPHENATED_WORD = 2
    TYPE_MWE = 3
    TYPE_WHITESPACE = 5
    TYPE_OTHER = 4

    def __init__(self, tokens=None, word_type=TYPE_NONE):
        if tokens is None:
            self.tokens = []
        elif isinstance(tokens, str):
            self.tokens = [tokens]
        else:
            self.tokens = tokens
        self.word_type = word_type

    def gettext(self, remove_accents=False, remove_punct=False):
        text = ''.join(self.tokens)
        if remove_accents:
            text = text.replace(COMBINING_ACCENT_CHAR, '')
        if remove_punct:
            text = text.translate(TRANSLATOR_PUNCT_REMOVE)
        return text

    def canonical(self):
        return self.gettext(remove_accents=True)

    def numtokens(self):
        return len(self.tokens)

    def getdata(self):
        return [self.word_type] + self.tokens

    def __repr__(self):
        return str(self.getdata())

    def __str__(self):
        return self.gettext()

class Preprocessor(object):
    def preprocess(self, text):
        text = text.replace(EN_DASH_CHAR, HYPHEN_CHAR)
        nfkd_form = unicodedata.normalize('NFKD', text)
        return nfkd_form

class Tokenizer(object):
    def tokenize(self, text):
        # First pass at splitting text into groups of russian characters, including accents, and then all others.
        # Assumes normalized in NFKD form.
        # Note the intention is to preserve upper/lower case characters and all whitespace, punctuation, etc
        COMBINING_CHARS = COMBINING_ACCENT_CHAR + COMBINING_BREVE_CHAR + COMBINING_DIURESIS_CHAR
        pattern = "([^" + RUS_ALPHABET_STR + COMBINING_CHARS + "]+)"
        tokens = re.split(pattern, text)
        tokens = [t for t in tokens if t != '']
        return tokens

class Parser(object):
    def __init__(self):
        self._mwes = pygtrie.Trie()

    def add_mwe(self, mwe):
        self._mwes[mwe.lower()] = True

    def add_mwes(self, mwes):
        for mwe in mwes:
            self._mwes[mwe.lower()] = True

    def preprocess(self, text):
        return Preprocessor().preprocess(text)

    def tokenize(self, text):
        return Tokenizer().tokenize(text)

    def tokens2words(self, tokens):
        tokenqueue = collections.deque(tokens)
        words = []
        while len(tokenqueue) > 0:
            # Initialize word object with first token from the queue
            token = tokenqueue.popleft()
            word = Word(tokens=token, word_type=Word.TYPE_OTHER)
            words.append(word)

            # Assume the word is russian if the first letter is russian based on the tokenization method
            if token[0] in RUS_ALPHABET_SET:
                word.word_type = Word.TYPE_WORD
                # Look ahead for hyphenated words or multi-word expressions
                if len(tokenqueue) > 0:
                    if tokenqueue[0] == HYPHEN_CHAR:
                        word.type = Word.TYPE_HYPHENATED_WORD
                        word.tokens.append(tokenqueue.popleft())
                        if tokenqueue[0][0] in RUS_ALPHABET_SET:
                            word.tokens.append(tokenqueue.popleft())
                    else:
                        self.find_mwe(tokenqueue, word)
            elif RE_WHITESPACE_ONLY.match(token):
                word.type = Word.TYPE_WHITESPACE

        return words

    def find_mwe(self, tokenqueue, word):
        tokenstack = word.tokens.copy()
        startpos = len(tokenstack)
        j = 0
        while j < len(tokenqueue):
            tokenstack.append(tokenqueue[j])
            expr = Word(tokenstack).gettext(remove_accents=True)
            expr = expr.lower()
            if self._mwes.has_subtrie(expr):
                j += 1
                continue
            elif self._mwes.has_key(expr):
                word.word_type = Word.TYPE_MWE
                for i in range(startpos, len(tokenstack)):
                    word.tokens.append(tokenqueue.popleft())
                return True
            else:
                break
        return False

    def parse(self, text):
        nfkd_text = self.preprocess(text)
        tokens = self.tokenize(nfkd_text)
        words = self.tokens2words(tokens)
        return words
