import os
import subprocess as sp
from loguru import logger

from ctm2seg import ctm2seg
from util.useful_funcs import getbname


def align_file(fpath_work, fpath_audio, fpath_text, dir_am, fpath_mfccconf, fpath_seg, fpath_lex, fpath_unknown_phones=""):
    os.makedirs(fpath_work, exist_ok=True)

    fpath_ctm = os.path.join(fpath_work, 'out.ctm')
    done_file = os.path.join(fpath_work, 'done')
    if not os.path.exists(done_file):
        cmd = f'LC_ALL=C ./force_align.sh {fpath_work} {fpath_audio} {fpath_text} {dir_am} {fpath_lex} {fpath_unknown_phones} {fpath_mfccconf} > {fpath_work}/force_align.log 2>&1'
        retcode = sp.call(cmd, shell=True)
    else:
        retcode = 0
        logger.info(f'Skipping alignment as {done_file} exists.')

    if retcode == 0:
        wavid = getbname(fpath_audio)
        ctm2seg(fpath_ctm, fpath_seg, wavid)
    else:
        logger.info(f'Alignment failed with audio {fpath_audio} work dir: {fpath_work}')


def align_file_wrapper(variable_args, dir_am, fpath_mfccconf, fpath_lex, fpath_unknown_phones):
    fpath_audio, fpath_text, fpath_work, fpath_seg = variable_args
    align_file(fpath_work, fpath_audio, fpath_text, dir_am, fpath_mfccconf, fpath_seg, fpath_lex, fpath_unknown_phones)


if __name__ == '__main__':
    import plac
    plac.call(align_file)
