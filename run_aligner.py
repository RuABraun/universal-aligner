import locale
import multiprocessing as mp
import os
from functools import partial

from util.io_funcs import readl
from getprons import get_prons
from align_file import align_file

def main(lang,
         fpath_wav_lst,
         fpath_txt_lst,
         dir_work,
         dir_am,
         fpath_vocab,
         fpath_mfcconf,
         num_jobs = mp.cpu_count()):
    assert locale.getlocale()[1] == "UTF-8", "Should be using UTF-8 locale!"

    lst_wavs = readl(fpath_wav_lst)
    lst_txts = readl(fpath_txt_lst)

    fpath_lex = os.path.join(dir_work, 'lexicon.txt')
    fpath_unknown_phones = os.path.join(dir_work, 'unknown_phone_ids')
    get_prons(fpath_vocab, fpath_lex, lang, fpath_unknown_phones)

    # Align files using eng model
    f = partial(align_file, lang=lang, dir_am=dir_am, fpath_mfcconf=fpath_mfcconf, fpath_lex=fpath_lex)
    with mp.Pool(num_jobs) as p:


    # Use segments to create language specific model


    # Align using language specific model


if __name__ == '__main__':
    import plac
    plac.call(main)
