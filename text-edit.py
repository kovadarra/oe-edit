import os
import pickle
import re
import subprocess
import tkinter as tk
from itertools import chain, zip_longest

if __package__ is None or __package__ == '':
    import HtmlClipboard
    from subs import *
else:
    from . import HtmlClipboard
    from .subs import *

from collections import deque

import PySimpleGUI as sg


def data_path(*args):
    return os.path.join(os.getenv('APPDATA'), 'OE Edit', *args)


if not os.path.isdir(data_path()):
    os.mkdir(data_path())
try:
    with open(data_path('user_data'), 'rb') as f:
        ses, espeak, geom, state = pickle.load(f)
except BaseException:
    ses, espeak, geom, state = deque(), '', None, None

def save_ses():
    with open(data_path('user_data'), 'wb') as f:
        pickle.dump((ses, espeak, geom, state), f)
    print('Saved session')

# [1] ? ᛬ : [4] ? ᛫ : [2] ? '' : [0]
ppunct = re.compile(
    r'((?<=[^\s\.:])[;,]?[^\S\n]+(?=\S))|([,;]$)|[\.!?]([^\S\n]*\n){2}|([\?!:\.][^\S\n]*)|[!\?\.\,;\*\n]',
    flags=re.MULTILINE)
prune = re.compile(r'\$r<([\s\S]*?):([\s\S]*?)>')

def transliterate(x: str, accent: str = 'en-us') -> str:
    global espeak
    if not os.path.isfile(espeak):
        if not (espeak := sg.popup_get_file('', no_window=True,
                                            file_types=(('Espeak Executable', '*.exe'),))):
            return None
    ipa = subprocess.check_output([espeak, '-q', '--ipa', '-m', '-v', accent,
                                   f'<emphasis>{ppunct.sub("<br>", x)}</emphasis>']).decode('U8')
    lns = ipa.splitlines()
    return ''.join(chain.from_iterable(zip(lns[:-1], map(
        lambda m: '᛬' if m[1] else '' if m[2] else '\n\n' if m[3] else '᛫' if m[4] else m[0], ppunct.finditer(x))))) + lns[-1]

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

wsubRk = max(map(len, sub_R.d.keys()))
wsubRv = max(map(len, sub_R.d.values()))
wsubrk = max(map(len, sub_r.d.keys()))
wsubrv = max(map(len, sub_r.d.values()))
lf = '\n'
subRcols = 50 // (wsubRk + wsubRv + 3)
subrcols = 50 // (wsubrk + wsubrv + 3)
print(f"""Welcome to OE Edit! This is an experimental text editor that's meant to streamline the writing of Old English texts.

Shortcuts
  Ctrl+C          Copy selected text
  Ctrl+X          Copy and delete selected text
  Ctrl+V          Paste copied text
  Ctrl+A          Select all text
  Ctrl+Z          Undo (file switch clears history)

  Ctrl+Left       Previous non-whitespace chunk begin
  Ctrl+Right      Next non-whitespace chunk begin
  Home            Beginning of line
  Ctrl+Home       Beginning of file
  End             End of line
  Ctrl+End        End of file
  Shift+<Motion>  Select from cursor to move location

  Ctrl+N          New file
  Ctrl+Tab,       Next file
  Ctrl+PgDn
  Ctrl+Shift+Tab, Previous file
  Ctrl+PgUp
  Ctrl+F4         Delete file

  Ctrl+Shift+C    Make a Google doc-friendly copy
  Ctrl+Shift+T    Transcribe to runic script

Latinized rendition character conversion rules
{lf.join(f'  {" ".join(f"{k:>{wsubRk}}->{v:<{wsubRv}}" for k,v in xs if k)}' for xs in grouper(filter(lambda x:x[0] and x[1],sub_R.d.items()),subRcols,("","")))}

Runic rendition character conversion rules
{lf.join(f'  {" ".join(f"{k:>{wsubrk}}->{v:<{wsubrv}}" for k,v in xs if k)}' for xs in grouper(filter(lambda x:x[0] and x[1],sub_r.d.items()),subrcols,("","")))}

Recognized markup
  One can use the notation $r<a:b> to change the output based on whether runic (a) or latinized (b) output is being generated.

  The notation *expression* is on gdoc-copy turned to red and the asterisks are removed.""")

filehash = hash(tuple(ses))

sg.theme('DarkAmber')
sg.theme_background_color('#151515')
layout = [[sg.Multiline(ses[0], font='Consolas', enable_events=True, key='-IN-', background_color='#333', border_width=0),
           sg.Multiline(sub_R(prune.sub(r'\2', ses[0])), disabled=True, font='Consolas', key='-OUT-', background_color='#151515', border_width=0)]]
win = sg.Window(
    'OE Edit',
    layout,
    finalize=True,
    margins=(
        0,
        0),
    resizable=True)

# Hotkeys
KEY_NEW_FILE = {}
KEY_UNDO = {}
KEY_DEL_FILE = {}
KEY_NEXT_FILE = {}
KEY_PREV_FILE = {}
KEY_GDOC_COPY = {}
KEY_TRANSLIT = {}
win.bind('<Control-Shift-Tab>', KEY_PREV_FILE)
win.bind('<Control-Prior>', KEY_PREV_FILE)
win.bind('<Control-Tab>', KEY_NEXT_FILE)
win.bind('<Control-Next>', KEY_NEXT_FILE)
win.bind('<Control-n>', KEY_NEW_FILE)
win.bind('<Control-F4>', KEY_DEL_FILE)
win.bind('<Control-z>', KEY_UNDO)
win.bind('<Control-Shift-C>', KEY_GDOC_COPY)
win.bind('<Control-Shift-T>', KEY_TRANSLIT)

# Auto-size
win['-IN-'].expand(True, True, True)
win['-OUT-'].expand(True, True, True)

# Geometry
def set_geom(e):
    global geom, state
    geom = win.TKroot.geometry()
    state = win.TKroot.state()
if geom:
    win.TKroot.geometry(geom)
    win.TKroot.state(state)
win.TKroot.bind('<Configure>', set_geom)

history = deque()
while True:
    event, values = win.read(60_000)
    if event == sg.TIMEOUT_KEY:
        if (curhash := hash(tuple(ses))) != filehash:
            save_ses()
            filehash = curhash
    elif event in (sg.WIN_CLOSED, 'Cancel'):
        save_ses()
        break
    elif event == {}:
        if event is KEY_NEW_FILE:
            ses.rotate(-1)
            ses.appendleft('')
        elif event is KEY_DEL_FILE:
            if not ses[0].strip() or sg.popup_ok_cancel(
                    'Are you sure?', 'Your data will be lost.', title='OE Edit') == 'OK':
                ses.popleft()
                if not ses:
                    ses.append('')
            else:
                continue
        elif event is KEY_GDOC_COPY:
            try:
                # Get selected text
                text = str(win['-OUT-'].Widget.get(tk.SEL_FIRST, tk.SEL_LAST))

                # Apply bold effect
                boldfmt = r'<span style="color:red;">\1</span>'
                text = re.sub(r'\*([^\*]+?)\*', boldfmt, text)

                # Apply paragraphs
                text = re.sub(
                    r'([\s\S]+?)(\n\n|$)',
                    r'<p>\1</p>',
                    text).replace(
                    '\n',
                    '\v')

                # Escape non-ASCII characters
                text = text.encode('ascii', 'xmlcharrefreplace').decode('ascii')

                HtmlClipboard.PutHtml(f'{text}')
            except Exception as e:
                print(f'Failed to doc-copy: {e}')
            continue
        elif event is KEY_TRANSLIT:
            win.TKroot.attributes('-alpha', 0.85)
            if text := transliterate(sub_prelit(prune.sub(r'\1', ses[0]))):
                win['-OUT-'](sub_r(text))
            else:
                print('Nothing was transliterated')
            win.TKroot.attributes('-alpha', 1)
            continue
        elif event is KEY_UNDO:
            if not history:
                continue
            ses[0], idx = history.pop()
            win['-IN-'](ses[0])
            win['-OUT-'](sub_R(prune.sub(r'\2', ses[0])))
            win['-IN-'].Widget.mark_set(tk.INSERT, idx)
            continue
        elif event is KEY_PREV_FILE:
            history.clear()
            ses.rotate(1)
        elif event is KEY_NEXT_FILE:
            history.clear()
            ses.rotate(-1)
        else:
            continue
        win['-IN-'](ses[0])
        win['-OUT-'](sub_R(prune.sub(r'\2', ses[0])))
        win['-IN-'].Widget.mark_set(tk.INSERT, '1.0')
    elif ses[0] != values['-IN-'][:-1]:
        # remove LF that is added to multilines in event reportings
        if len(history) > 15:
            history.pop()
        history.append((ses[0], win['-IN-'].Widget.index(tk.INSERT)))
        ses[0] = values['-IN-'][:-1]
        win['-OUT-'](sub_R(prune.sub(r'\2', ses[0])))


win.close()
