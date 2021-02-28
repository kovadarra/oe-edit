import os
from sortedcontainers import SortedDict
import re
import enum
from itertools import chain
import csv

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

class csv_entry:
    def __init__(self, data):
        self.word, self.meaning, self.kind, self.forebear, self.whence, self.notes = data[:6]
    word: str
    meaning: str
    kind: csv_kind
    forebear: str
    whence: str
    notes: str

pword = re.compile(r"(\ba |\ban |\bthe |\bto )?(\w[\w ']*)")

def get_wordbook(path: str) -> SortedDict[str, csv_entry]:
    if not os.path.isfile(path):
        import requests
        response = requests.get(
            'https://docs.google.com/spreadsheets/d/1y8_11RDvuCRyUK_MXj5K7ZjccgCUDapsPDI5PjaEkMw/gviz/tq?tqx=out:csv&sheet=Wordbook')
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
    with open(path, newline='', encoding='U8') as f:
        reader = iter(csv.reader(f))
        next(reader)
        return SortedDict(sorted(chain.from_iterable([(e.word.lower(), e), *((x.lower(), e) for x in (
            m[2] for m in pword.finditer(e.meaning)) if x)] for e in map(csv_entry, reader)), key=lambda x: x[0]))
