#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import scipy.io.wavfile as wav

import numpy as np
from pyAudioAnalysis import audioSegmentation as aS

PAD_SZ = 2

def vad(wav_in, wav_out):

    results, a, b, c = aS.mtFileClassification(wav_in, '/home/seni/git/pyAudioAnalysis/data/svmSM', 'svm', False)
    results = [(val + 1) % 2 for val in results]  # flipping 1 and 0s

    fs, data = wav.read(wav_in)

    num_segments = len(results)
    padded_results = [1, 1]
    padded_results.extend(results)
    padded_results.extend([1, 1])
    speech_data = []  # hopefully
    for i in range(2, num_segments+2):
        #print(padded_results[i])
        segment = data[(i-2)*fs: (i-1)*fs]  # -2
        if sum(padded_results[i - 2: i + 3]) == 0:
            continue
        else:
            speech_data.extend(segment)

    speech_data = np.array(speech_data)
    wav.write(wav_out, fs, speech_data)

def main():
    parser = argparse.ArgumentParser(description='Strip non speech from wav file.')
    parser.add_argument('wav_in', type=str)
    parser.add_argument('wav_out', type=str)
    args = parser.parse_args()
    vad(args.wav_in, args.wav_out)

main()
