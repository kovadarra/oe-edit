import csv
import enum
import os
import pickle
import re
from itertools import chain

from pkg_resources import resource_filename
from sortedcontainers import SortedDict


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
    r"($|\.|;)\s*(\ba |\ban |\bthe |\bto )?\s*(\w[\w ']*)",
    flags=re.IGNORECASE)

def get_wordbook(path: str) -> SortedDict[str, wordbook_entry]:
    if not os.path.isfile(path):
        import requests
        response = requests.get(
            'https://docs.google.com/spreadsheets/d/1y8_11RDvuCRyUK_MXj5K7ZjccgCUDapsPDI5PjaEkMw/gviz/tq?tqx=out:csv&sheet=Wordbook')
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
    with open(resource_filename('oe_edit.resources', 'wordbook.bin'), 'rb') as fbase:
        with open(path, newline='', encoding='U8') as fcsv:
            reader = iter(csv.reader(fcsv))
            next(reader)

            kfa = pkind.findall
            def csv_entry(data):
                return wordbook_entry([data[0], '; '.join(filter(
                    None, map(str.strip, data[1].split('᛫')))), '|'.join(kfa(data[2]))])

            # l = list of entries
            l = [*map(wordbook_entry, zip(*([iter(pickle.load(fbase))] * 3))),
                 *map(csv_entry, reader)]

            # data = base derivative, wb derivative, base exact, wb exact
            sl = str.lower
            wfa = pword.findall
            return SortedDict(chain(chain.from_iterable(
                [[(sl(m[2]), e) for m in wfa(e.meaning)] for e in l]), [(sl(e.word), e) for e in l]))
