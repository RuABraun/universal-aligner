# -*- coding: utf-8 -*
import locale
import multiprocessing as mp
import os
from functools import partial
from os.path import join

import regex as re
from loguru import logger

from util.useful_funcs import getbname

CHAR_MAPPINGS = {'υ': 'u', '…': '.', '\u2025': '.', '\u2024': '.', '\u03BD': 'v', 'º': '°',
                 chr(8208): '-', chr(8209): '-', chr(8210): '-', chr(8212): ' ', chr(8211): ' ', chr(8213): ' '}
BAD_SYMBOLS = re.compile(r'[&_"=\%@;<>\[\]\(\)\+*“”„‟\u201D\.?!:\u2018\u2019\u02BC]')
PTN_BRACKET = re.compile(r'[(\[]{1}[\p{L}[:punct:]\s\d]*?[)\]]{1}')
PTN_COMMA = re.compile(r'(?<!\d),(?!\d)')


def normalise_text(text, remove_hyphens=True):
    lst = []
    for c in text:
        lst.append(CHAR_MAPPINGS.get(c, c))
    text = ''.join(lst)
    text = PTN_BRACKET.sub(' ', text)
    text = PTN_COMMA.sub('', text)
    text = text.replace('&gt;', ' ')
    text = text.replace('&nbsp;', ' ')
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


def normalise_file_wrapper(variable_args, remove_hyphens):
    fpath_in, fpath_out = variable_args
    normalise_file(fpath_in, fpath_out, remove_hyphens)


def normalise_files(lst_files, nj, outdir):
    os.makedirs(outdir, exist_ok=True)
    func = partial(normalise_file_wrapper, remove_hyphens=True)
    logger.info(f'Starting to normalise {len(lst_files)} files.')
    lst_args = [(e, join(outdir, getbname(e) + '.txt')) for e in lst_files]
    with mp.Pool(nj) as pool:
        pool.map(func, lst_args)
    logger.info('Done normalisation.')
    lst_txts = [e[1] for e in lst_args]
    return lst_txts


if __name__ == '__main__':
    import plac
    plac.call(normalise_file)
