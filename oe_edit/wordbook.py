import csv
import enum
import os
import pickle
import re
import threading
import time
from itertools import chain

from pkg_resources import resource_filename
from sortedcontainers import SortedDict, SortedSet


class csv_kind(enum.Enum):
    NOUN = 'N',
    PROPER_NOUN = 'PN',
    VERB = 'V',
    ADJECTIVE = 'ADJ',
    ADVERB = 'ADV',
    PREPOSITION = 'PREP',
    CONJUNCTION = 'CONJ',
    INTERJECTION = 'INT',
    AFFIX = 'AFF'

pkind = re.compile('|'.join(f'\\b{x.value[0]}\\b' for x in csv_kind))

class wordbook_entry:
    def __init__(self, data):
        self.word, self.meaning, self.kind = data
    word: str
    meaning: str
    kind: csv_kind

pword = re.compile(
    r"(^|\.|᛬|;)\s*(\ba |\ban |\bthe |\bto )?\s*(\w[\w']*)",
    flags=re.IGNORECASE)

def _wb_init(path: str) -> tuple[SortedDict[str,
                                            wordbook_entry], SortedDict[str, list[wordbook_entry]]]:
    '''
    Initializes word book data: returns dicts of by-word matches and by-meaning matches.
    '''
    def old():
        age_s = time.time() - os.stat(path).st_mtime
        return age_s > 60 * 60 * 24 * 10
    if not os.path.isfile(path) or old():
        import requests
        print('getting wordbook.', end='')
        response = requests.get(
            'https://docs.google.com/spreadsheets/d/1y8_11RDvuCRyUK_MXj5K7ZjccgCUDapsPDI5PjaEkMw/gviz/tq?tqx=out:csv&sheet=Wordbook')
        print('.\r', end='')
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        print('getting wordbook... done')
    with open(resource_filename('oe_edit.resources', 'wordbook.bin'), 'rb') as fbase:
        with open(path, newline='', encoding='U8') as fcsv:
            reader = iter(csv.reader(fcsv))
            next(reader)

            kfa = pkind.findall
            def csv_entry(data):
                return wordbook_entry([data[0], '; '.join(filter(
                    None, map(str.strip, data[2].split('᛫')))), '|'.join(kfa(data[2]))])

            # l = list of entries
            l = [*map(wordbook_entry, zip(*([iter(pickle.load(fbase))] * 3))),
                 *map(csv_entry, reader)]

            sl = str.lower
            wfa = pword.findall
            word_match = SortedDict([(sl(e.word), e) for e in l])
            mean_match = SortedDict()
            for (k, v) in chain.from_iterable(
                    [[(sl(m[2]), e) for m in wfa(e.meaning)] for e in l]):
                mean_match.setdefault(k, []).append(v)
            return word_match, mean_match

class wordbook:
    def __init__(self, path: str):
        self.__dw, self.__dm = _wb_init(path)
        self.__curw, self.__curl = '', []
    def __work(self, w: str):
        dw, dm = self.__dw, self.__dm
        sw = str.startswith

        lw = []
        for (k, v) in map(dw.peekitem, range(
                dw.bisect_left(w), len(self.__dw))):
            if not sw(k, w):
                break
            lw.append(v)

        lm = SortedSet(key=lambda x: x.word)
        for (k, v) in map(dm.peekitem, range(
                dm.bisect_left(w), len(self.__dm))):
            if not sw(k, w):
                break
            lm.update(v)

        lw.extend(lm)
        self.__curl = lw
    def __getitem__(self, word: str):
        word = word.strip().lower()
        if self.__curw == word:
            return self.__curl
        elif word:
            self.__curw, self.__curl = word, None
            threading.Thread(target=self.__work, args=(word,)).start()
    @property
    def current_word(self) -> str:
        return self.__curw
    @property
    def current_list(self) -> list[wordbook_entry]:
        return self.__curl
