import os
import subprocess as sp
from loguru import logger

from getprons import get_prons
from ctm2seg import ctm2seg


def align_file(lang, fpath_work, fpath_audio, fpath_text, dir_am, fpath_vocab, fpath_mfccconf, fpath_seg, fpath_lex=None):
    os.makedirs(fpath_work, exist_ok=True)
    if fpath_lex is None:
        fpath_lex = os.path.join(fpath_work, 'lexicon.txt')
        fpath_lex_unknown = os.path.join(fpath_work, 'lexicon_nounknown.txt')
        fpath_unknown_phones = os.path.join(fpath_work, 'phone_ids')
        if not os.path.exists(fpath_lex):
            get_prons(fpath_vocab, fpath_lex, lang, fpath_unknown_phones)
        else:
            logger.info(f'Skipping creation of lexicon because {fpath_lex} exists.')

    fpath_ctm = os.path.join(fpath_work, 'out.ctm')
    if not os.path.exists(fpath_ctm):
        cmd = f'./force_align.sh {fpath_work} {fpath_audio} {fpath_text} {dir_am} {fpath_lex_unknown} {fpath_unknown_phones} {fpath_mfccconf}'
        sp.check_output(cmd, shell=True)
    else:
        logger.info(f'Skipping alignment as {fpath_ctm} exists.')

    wavid = os.path.splitext(os.path.basename(fpath_audio))[0]
    ctm2seg(fpath_ctm, fpath_seg, wavid)


if __name__ == '__main__':
    import plac
    plac.call(align_file)
