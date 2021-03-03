import re
from itertools import zip_longest


def build_sub(d: dict, upper=False):
    def escape(x: str):
        return f'\\{x}' if x in '.+?![]$^' else x
    if upper:
        d.update({f'{k[0].upper()}{k[1:]}': v.upper() for k, v in d.items()})
    sub = re.compile(f"\\\\(.)|{'|'.join(map(escape, d.keys()))}").sub
    match = re.compile(
        f'(({"|".join([f"!{k}" for k in d.keys()])})+)\r?\n',
        flags=re.MULTILINE).match
    def res(x: str):
        if m := match(x):
            x = x[m.span()[1]:]
            skip = set(m[1][1:].split('!'))
        else:
            skip = set()
        at = re.Match.__getitem__
        return sub(lambda m: at(m, 1) or at(m, 0) in skip and at(
            m, 0) or d[at(m, 0).replace('\\', r'\\')], x)
    res.d = d
    return res

sub_R = build_sub({'ää': 'ǣ', 'th': 'þ', 'ä': 'æ', 'yy': 'ȳ', 'ee': 'ē', 'oo': 'ō', 'cc': 'ċ',
                   'aa': 'ā', 'ii': 'ī', 'uu': 'ū', 'gG': 'g', 'g': 'ġ', 'w': 'ƿ', 'tH': 'ð', 'gh': 'ȝ'}, upper=True)
sub_r = build_sub({'eɪ.ɪŋ': 'ᛖᛁᛝ',
                   'eɪɪŋ': 'ᛖᛁᛝ',
                   'eɪ.ɝ': 'ᛖᛁᚱ',
                   'eɪɚ': 'ᛖᛁᚱ',
                   'eɪr': 'ᛖᛁᚱ',
                   'eɪɹ': 'ᛖᛁᚱ',
                   'eɪŋ': 'ᚫᛝ',
                   'i.ɝ': 'ᛠᚱ',
                   'ɪɹ': 'ᛠᚱ',
                         'ɪr': 'ᛠᚱ',
                         'oʊ': 'ᚩ',
                         'əʊ': 'ᚩ',
                         'tʃ': 'ᚳ',
                         'ks': 'ᛉ',
                         'ɡz': 'ᛉ',
                         'gz': 'ᛉ',
                         'ɡz': 'ᛉ',
                         'ŋg': 'ᛝ',
                         'ŋɡ': 'ᛝ',
                         'ɔɪ': 'ᚩᛁ',
                         'dʒ': 'ᚳᚷ',
                         'ɪɝ': 'ᛁᚱ',
                         'ɪɹ': 'ᛁᚱ',
                         'ɪr': 'ᛁᚱ',
                         'eɪ': 'ᛖᛁ',
                         'ɛi': 'ᛖᛁ',
                         'aɪ': 'ᚪᛁ',
                         'əɪ': 'ᚪᛁ',
                         'aʊ': 'ᚫᚢ',
                         'ɛɝ': 'ᚫᚱ',
                         'ɛɹ': 'ᚫᚱ',
                         'ɛr': 'ᚫᚱ',
                         'æŋ': 'ᚫᛝ',
                         'f': 'ᚠ',
                         'v': 'ᚠ',
                         'u': 'ᚢ',
                         'ʊ': 'ᚢ',
                         'ɵ': 'ᚢ',
                         'θ': 'ᚦ',
                         'ð': 'ᚦ',
                         'ɹ̩': 'ᛖᚱ',
                         'ɹ': 'ᚱ',
                         'r': 'ᚱ',
                         'j': 'ᛡ',
                         'g': 'ᚸ',
                         'ɡ': 'ᚸ',
                         'w': 'ᚹ',
                         'h': 'ᚻ',
                         'n': 'ᚾ',
                         'ɪ': 'ᛁ',
                         'x': 'ᛇ',
                         'p': 'ᛈ',
                         's': 'ᛋ',
                         'z': 'ᛋ',
                         't': 'ᛏ',
                         'b': 'ᛒ',
                         'ɛ': 'ᛖ',
                         'e': 'ᛖ',
                         'm': 'ᛗ',
                         'l': 'ᛚ',
                         'ŋ': 'ᛝ',
                         'd': 'ᛞ',
                         'ʌ': 'ᛟ',
                         'ɒ': 'ᚪ',
                         'ɑ': 'ᚪ',
                         'ə': 'ᚪ',
                         'ɐ': 'ᚪ',
                         'o': 'ᚩ',
                         'æ': 'ᚫ',
                         'a': 'ᚫ',
                         'i': 'ᛠ',
                         'y': 'ᚣ',
                         'k': 'ᛣ',
                         'ʒ': 'ᚳᚷ',
                         'ʍ': 'ᚻᚹ',
                         'w': 'ᚹ',
                         'ʃ': 'ᛋᚳ',
                         'ɝ': 'ᛖᚱ',
                         'ɜ': 'ᛖᚱ',
                         'ɔː': 'ᚪ',
                         'ɔ': 'ᚪᚢ',
                         'ɚ': 'ᚪᚱ',
                         'ɾ': 'ᛏ',
                         ' ': '',
                         'ˈ': '',
                         'ː': '',
                         '̩': '', '͡': '', 'ˌ': ''})  # discarded IPA notation
sub_prelit = build_sub({"'": '',
                        '"': '',
                        'gG': 'g',
                        'GG': 'G',
                        'tH': 'th',
                        'TH': 'Th'})


def table_sub(sub):
    wk = max(map(len, sub.d.keys()))
    wv = max(map(len, sub.d.values()))
    cols = 50 // (wk + wv + 3)
    return '\n'.join(f'  {" ".join(f"{k:>{wk}}->{v:<{wv}}" for k,v in xs if k)}' for xs in zip_longest(
        *([iter(filter(lambda x:x[0] and x[1], sub.d.items()))] * cols), fillvalue=("", "")))
