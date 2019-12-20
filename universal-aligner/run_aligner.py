import locale
import multiprocessing as mp
import os
import shutil
import subprocess as sp
import sys
from functools import partial
from glob import glob
from os.path import join

from align_file import align_file_wrapper
from create_kdata import create_kdata
from getprons import get_prons
from loguru import logger
from normalise import normalise_files
from util.useful_funcs import readl, writel, getbname


def join_segs(lst_segs, fpath_seg):
    fhw = open(fpath_seg, 'w')
    for f in lst_segs:
        if os.path.exists(f):
            with open(f) as fh:
                for line in fh:
                    fhw.write(line)
    fhw.close()


def mute():
    sys.stdout = open(os.devnull, 'w')


def main(lang,
         fpath_wav_lst,
         fpath_txt_lst,
         dir_work,
         dir_am,
         fpath_mfccconf,
         fpath_vocab=None,
         num_jobs: ('Number of jobs to use', 'option', 'j') = 1):
    assert locale.getlocale()[1] == "UTF-8", "Should be using UTF-8 locale!"

    num_jobs = int(num_jobs)
    logger.info('Starting segmentation.')

    lst_txts = readl(fpath_txt_lst)

    dir_normalised_txt = join(dir_work, 'normed_text')
    if not os.path.exists(dir_normalised_txt):
        lst_txts = normalise_files(lst_txts, num_jobs, dir_normalised_txt)
    else:
        lst_txts = glob(join(dir_normalised_txt, '*'))

    if fpath_vocab is None:
        fpath_vocab = join(dir_work, 'vocab')
        if not os.path.exists(fpath_vocab):
            vocab = set()
            for f in lst_txts:
                with open(f) as fh:
                    for line in fh:
                        line_split = line.split()
                        for word in line_split:
                            vocab.add(word)
            writel(fpath_vocab, list(vocab))

    lst_wavs = readl(fpath_wav_lst)
    lst_work = [join(dir_work, getbname(wav)) for wav in lst_wavs]

    fpath_lex = os.path.join(dir_work, 'lexicon.txt')
    fpath_lex_unknown = os.path.join(dir_work, 'lexicon_nounknown.txt')
    fpath_unknown_phones = os.path.join(dir_work, 'unknown_phone_ids')
    if not os.path.exists(fpath_lex):
        get_prons(fpath_vocab, fpath_lex, lang, fpath_unknown_phones)

    logger.info('Aligning audio and text using ENG model.')
    f = partial(align_file_wrapper, dir_am=dir_am, fpath_mfccconf=fpath_mfccconf, fpath_lex=fpath_lex_unknown,
                fpath_unknown_phones=fpath_unknown_phones)
    lst_args = [(wav, txt, work, join(work, 'seg')) for wav, txt, work in zip(lst_wavs, lst_txts, lst_work)]
    with mp.Pool(num_jobs, initializer=mute) as p:
        p.map(f, lst_args)

    if not os.path.exists(f'{dir_work}/train_gmm_done'):
        logger.info('Done aligning, formatting data.')
        lst_segs = [e[3] for e in lst_args]
        fpath_seg = join(dir_work, 'all_seg')
        join_segs(lst_segs, fpath_seg)
        dir_train_init = join(dir_work, 'train_init')
        create_kdata(fpath_seg, lst_wavs, dir_train_init)

        fpath_log = f'{dir_work}/train_gmm.log'
        logger.info(f'Using alignment to train language specific model, log in {fpath_log}')
        shutil.copyfile(fpath_mfccconf, join(dir_work, 'mfcc.conf'))
        cmd = f'LC_ALL=C ./train_gmm.sh --nj {num_jobs} --work {dir_work} --language {lang} > {fpath_log} 2>&1'
        sp.check_output(cmd, shell=True)

    logger.info('Done training language specific model, aligning data using it.')

    f = partial(align_file_wrapper, dir_am=join(dir_work, 'exp', 'tri1'), fpath_mfccconf=fpath_mfccconf, fpath_lex=fpath_lex)
    lst_work = [e + f'_{lang}' for e in lst_work]
    lst_args = [(wav, txt, work, join(work, 'seg')) for wav, txt, work in zip(lst_wavs, lst_txts, lst_work)]
    with mp.Pool(num_jobs) as p:
        p.map(f, lst_args)

    lst_segs = [e[3] for e in lst_args]
    fpath_seg = join(dir_work, f'seg_final_{lang}')
    join_segs(lst_segs, fpath_seg)
    dir_train_final = join(dir_work, f'train_{lang}')
    create_kdata(fpath_seg, lst_wavs, dir_train_final)
    logger.info(f'Created new alignment, see file {fpath_seg} and kaldi train dir {dir_train_final}')


if __name__ == '__main__':
    import plac
    plac.call(main)
