import ctypes
import os
import pickle
import re
import subprocess
from collections import deque
from itertools import chain
from time import time_ns

import PySimpleGUI as sg
from pkg_resources import resource_filename

from oe_edit.subs import *
from oe_edit.wordbook import *


def data_path(*args):
    return os.path.join(os.getenv('APPDATA'), 'OE Edit', *args)

# Set icon
# https://stackoverflow.com/a/34547834
myappid = 'mycompany.myproduct.subproduct.version'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
sg.set_global_icon(resource_filename('oe_edit.resources', 'icon.ico'))

start = time_ns()
wb = get_wordbook(data_path('wordbook.csv'))
print(f'wordbook loaded in {(time_ns()-start)/1_000_000:.0f}ms')

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
    print('Session saved')

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

print(f"""Welcome to OE Edit! This is an experimental text editor that's meant to streamline the writing of Old English texts. For IPA transliteration, external program is needed:
  http://espeak.sourceforge.net/

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
  Ctrl+W,         Delete file
  Ctrl+F4

  Ctrl+Shift+C    Make a Google doc-friendly copy
  Ctrl+Shift+T    Transcribe to runic script
  Ctrl+Space      Apply suggested wordbook entry

Latinized rendition character conversion rules
{table_sub(sub_R)}

Runic rendition character conversion rules
{table_sub(sub_r)}

Recognized markup
  One can use the notation $r<a:b> to change the output based on whether runic (a) or latinized (b) output is being generated.

  The notation *expression* is on gdoc-copy turned to red and the asterisks are removed.""")

filehash = hash(tuple(ses))

sg.theme('DarkAmber')
sg.theme_background_color('#151515')
sg.theme_element_background_color('#151515')
sg.theme_text_element_background_color('#151515')
layout = [[sg.T('<wordbook entries appear here>', key='-TIP-', size=(120, 1))],
          [sg.Multiline(ses[0], font='Consolas', enable_events=True, key='-IN-', background_color='#222', border_width=0),
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
KEY_AUTOCOMPLETE = {}
win.bind('<Control-Shift-Tab>', KEY_PREV_FILE)
win.bind('<Control-Prior>', KEY_PREV_FILE)
win.bind('<Control-Tab>', KEY_NEXT_FILE)
win.bind('<Control-Next>', KEY_NEXT_FILE)
win.bind('<Control-n>', KEY_NEW_FILE)
win.bind('<Control-w>', KEY_DEL_FILE)
win.bind('<Control-F4>', KEY_DEL_FILE)
win.bind('<Control-z>', KEY_UNDO)
win.bind('<Control-space>', KEY_AUTOCOMPLETE)
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
suggesting = None
inw = win['-IN-'].Widget
tipw = win['-TIP-'].Widget
inw.config(insertbackground='white')
inw.config(selectbackground='#474747')

pword = re.compile(r"[\w'\-]+")
def get_cur_word():
    if ws := pword.findall(inw.get('insert -1c wordstart', 'insert wordend')):
        return ws[-1]
    return ''

def get_cur_word_bounds():
    ins = inw.get('insert -1c wordstart', 'insert wordend')
    if ws := list(map(re.Match.span, pword.finditer(ins))):
        if ins[-1] == '\n':
            idx, n = inw.index('insert -1c wordend'), len(ins) - 1
        else:
            idx, n = inw.index('insert wordend'), len(ins)
        ln, col = idx.split('.')
        a, b = ws[-1]
        return f'{ln}.{int(col)-n+a}', f'{ln}.{int(col)-n+b}'

def read_wb():
    if w := get_cur_word().lower():
        if (wi := wb.bisect_left(w)) < len(wb):
            n = len(w)
            k, v = wb.peekitem(wi)
            if k[:n] == w:
                return v

def highlight():
    inw.tag_remove('suggest', '1.0', 'end')
    idx = '1.0'
    w = suggesting.word
    while idx := inw.search(w, idx, 'end', nocase=True):
        ln, col = idx.split('.')
        last = f'{idx}+{len(w)}c'
        def ok(x): return not x.isalpha()
        if col == '0' or ok(inw.get(f'{ln}.{int(col)-1}')):
            if ok(inw.get(last)):
                inw.tag_add('suggest', idx, last)
        idx = last
    inw.tag_config('suggest', background='#474747')

hlight = 3
def update_wb():
    global suggesting, hlight
    if v := read_wb():
        if v != suggesting:
            win['-TIP-'](f'{v.word}{f" ({v.kind})" if v.kind else ""}: {v.meaning}')
            suggesting = v
            highlight()
            hlight = 3
    elif suggesting:
        suggesting = None
        inw.tag_remove('suggest', '1.0', 'end')
        win['-TIP-']('')

def update_text():
    text = inw.get('1.0', 'end')[:-1]
    if history and text == ses[0]:
        return
    if len(history) > 15:
        history.pop()
    history.append((ses[0], inw.index('insert')))
    ses[0] = text
    win['-OUT-'](sub_R(prune.sub(r'\2', text)))

save = 400
while True:
    event, values = win.read(150)
    if event == sg.TIMEOUT_KEY:
        update_wb()
        if not (hlight := hlight - 1):
            hlight = 5
            if suggesting:
                highlight()
        if not (save := save - 1):
            save = 400
            if (curhash := hash(tuple(ses))) != filehash:
                save_ses()
                filehash = curhash
    elif event in (sg.WIN_CLOSED, 'Cancel'):
        save_ses()
        break
    elif event == {}:
        if event is KEY_NEW_FILE:
            history.clear()
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
                text = str(win['-OUT-'].Widget.get('sel.first', 'sel.last'))

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

                from oe_edit.HtmlClipboard import PutHtml
                PutHtml(f'{text}')
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
            win['-IN-'].Widget.mark_set('insert', idx)
            continue
        elif event is KEY_PREV_FILE:
            history.clear()
            ses.rotate(1)
        elif event is KEY_NEXT_FILE:
            history.clear()
            ses.rotate(-1)
        elif event is KEY_AUTOCOMPLETE:
            if suggesting:
                start, end = get_cur_word_bounds()
                inw.delete(start, end)
                inw.insert(start, suggesting.word)
                inw.tag_add('suggest', start, 'insert')
                update_text()
                continue
        else:
            continue
        win['-IN-'](ses[0])
        win['-OUT-'](sub_R(prune.sub(r'\2', ses[0])))
        win['-IN-'].Widget.mark_set('insert', '1.0')
    else:
        update_text()


win.close()
