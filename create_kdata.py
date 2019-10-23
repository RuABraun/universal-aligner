""" Create kaldi style data dir from lst of wavpaths and seg file created from alignment script """
import os
import shutil
import subprocess as sp
from os.path import join, exists, basename, splitext

from loguru import logger

from util.io_funcs import readl


def create_kdata(fpath_seg, lst_wavs, dir_new):
    logger.info('Assumes basename of wav (excluding .wav) is contained in matching utterance IDs.')
    if exists(dir_new):
        shutil.rmtree(dir_new)
    os.makedirs(dir_new)

    wavids = []
    for wavpath in lst_wavs:
        wavids.append(splitext(basename(wavpath))[0])
    wavids = set(wavids)

    uttids = []
    fh_kseg = open(join(dir_new, 'segments'), 'w')
    fh_text = open(join(dir_new, 'text'), 'w')
    with open(fpath_seg) as fh:
        for line in fh:
            uttid, start, end, *words = line.split()
            wavid = '_'.join(uttid.split('_')[:-1])
            assert wavid in wavids
            fh_kseg.write(f'{uttid} {wavid} {start} {end}\n')
            words = ' '.join(words)
            fh_text.write(f'{uttid} {words}\n')

            uttids.append(uttid)
    fh_kseg.close()
    fh_text.close()

    wavids = list(wavids)
    with open(join(dir_new, 'wav.scp'), 'w') as fh:
        for wavid, wavpath in zip(wavids, lst_wavs):
            fh.write(f'{wavid} {wavpath}\n')

    with open(join(dir_new, 'utt2spk'), 'w') as fha, open(join(dir_new, 'spk2utt'), 'w') as fhb:
        for uttid in uttids:
            line = f'{uttid} {uttid}'
            fha.write(f'{line}\n')
            fhb.write(f'{line}\n')

    cmd = f'utils/fix_data_dir.sh {dir_new}'
    sp.check_output(cmd, shell=True)
    logger.info(f'Done creating new kaldi data dir: {dir_new}')


def main(fpath_seg, fpath_wav_lst, dir_new):
    lst_wavs = readl(fpath_wav_lst)
    create_kdata(fpath_seg, lst_wavs, dir_new)


if __name__ == '__main__':
    import plac
    plac.call(main)