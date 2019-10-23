# -*- coding: utf-8 -*
import regex as re
import locale

CHAR_MAPPINGS = {'υ': 'u', '…': '.', '\u2025': '.', '\u2024': '.', '\u03BD': 'v', 'º': '°',
                 chr(8208): '-', chr(8209): '-', chr(8210): '-', chr(8212): ' ', chr(8211): ' ', chr(8213): ' '}
BAD_SYMBOLS = re.compile(r'[&_"=\%@,;<>\[\]\(\)\+*“”„‟\u201D\.?!:\u2018\u2019\u02BC]')
PTN_BRACKET = re.compile(r'[(\[]{1}[\p{L}[:punct:]\s\d]*?[)\]]{1}')


def normalise_text(text, remove_hyphens=True):
    lst = []
    for c in text:
        lst.append(CHAR_MAPPINGS.get(c, c))
    text = ''.join(lst)
    text = PTN_BRACKET.sub(' ', text)
    text = text.replace('&gt;', '')
    text = BAD_SYMBOLS.sub(' ', text)
    if remove_hyphens:
        text = text.replace('-', ' ')
    return text.lower()


def normalise_file(fpath_in, fpath_out=None, remove_hyphens=True):
    assert locale.getlocale()[1] == "UTF-8", "Should be using UTF-8 locale!"

    with open(fpath_in) as fh:
        text = fh.read()

    text = normalise_text(text, remove_hyphens)

    if fpath_out is None:
        fpath_out = fpath_in
    with open(fpath_out, 'w') as fh:
        fh.write(text)


if __name__ == '__main__':
    import plac
    plac.call(normalise_file)
