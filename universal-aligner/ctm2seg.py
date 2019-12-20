# -*- coding: utf-8 -*
import numpy as np
from loguru import logger

TARGET_DURATION = 10.0  # seconds


class Seg:
    def __init__(self, words, start_time_s, end_time_s, speech_dur_s=None, splits=None, segid=''):
        self.segid = segid
        if isinstance(words, list):
            self.words = words
        else:
            self.words = [words]
        self.start_time_s = start_time_s
        self.end_time_s = end_time_s
        if speech_dur_s is None:
            self.speech_dur_s = end_time_s - start_time_s  # should be true at initialization
        else:    
            self.speech_dur_s = speech_dur_s

        if splits is None:  # times at which words can be split, thought I might needs this.. turns out no
            self.splits = []
        else:
            self.splits = splits

    def __add__(self, otherseg):
        words = self.words + otherseg.words
        speech_dur_s = self.speech_dur_s + otherseg.speech_dur_s
        splits = self.splits
        splits.append((self.end_time_s + otherseg.start_time_s) / 2) 
        return Seg(words, self.start_time_s, otherseg.end_time_s, speech_dur_s, splits)

    def __radd__(self, otherseg):
        words = otherseg.words + self.words
        speech_dur_s = self.speech_dur_s + otherseg.speech_dur_s
        splits = [(otherseg.end_time_s + self.start_time_s) / 2]
        splits.extend(self.splits)
        return Seg(words, otherseg.start_time_s, self.end_time_s, speech_dur_s, splits)
        

def gainfunc(lst_segs):
    """ Minimum of the two speech durations (from 2 segs) plus 1, 
        plus optimal segment length minus segment lengths,
        minus distance between segs squared plus distance
    """
    gains = []
    for seg1, seg2 in zip(lst_segs[:-1], lst_segs[1:]):
        speech_term = min(seg1.speech_dur_s, seg2.speech_dur_s) + 1
        length_term = (TARGET_DURATION - (seg1.end_time_s - seg1.start_time_s) - (seg2.end_time_s - seg2.start_time_s))
        diff_ = - ((seg2.start_time_s - seg1.end_time_s) ** 2 + abs(seg2.start_time_s - seg1.end_time_s))
        
        gain = speech_term + \
               length_term + \
               diff_
        gains.append(gain)
    return gains


def join_at_indcs(lst_segs, indcs_in):
    """ Idx points as seg2 if [seg1, seg2] are to be joined. 
    I hate this approach.
    """

    if not indcs_in:
        return lst_segs

    indcs_in = sorted(indcs_in)  # safety

    # Get indices of segs that will be untouched from joining
    segindcs_untouched = [i for i in range(len(lst_segs)) if i not in indcs_in and i + 1 not in indcs_in]
    len_segindcs_untouched = len(segindcs_untouched)

    # Group indices so consecutive are in the same.
    indcs_grped = []
    curr_grp = [indcs_in[0]]
    for idx in indcs_in[1:]:
        if idx - 1 == curr_grp[-1]:
            curr_grp.append(idx)
        else:
            indcs_grped.append(curr_grp)
            curr_grp = [idx]
    if len(indcs_grped) == 0:  # never entered for loop
        indcs_grped = [curr_grp]
    else:  # appending last grp
        indcs_grped.append(curr_grp)

    lst_segs_new = []
    idx_segindcs_untouched = 0
    if len_segindcs_untouched > 0:
        idx_seg_untouched = segindcs_untouched[idx_segindcs_untouched]
    else:
        idx_seg_untouched = len(lst_segs)

    for indcs in indcs_grped:
        idx_start = indcs[0] - 1
        if idx_seg_untouched < idx_start:
            while idx_seg_untouched < idx_start:
                lst_segs_new.append(lst_segs[idx_seg_untouched])
                idx_segindcs_untouched += 1
                if idx_segindcs_untouched == len_segindcs_untouched:
                    idx_seg_untouched = len(lst_segs)  # setting high so while won't trigger (would remain at last number otherwise)
                    break
                idx_seg_untouched = segindcs_untouched[idx_segindcs_untouched]

        newseg = lst_segs[idx_start]  # left Seg (seg1 from the docstring)
        for idx in indcs:
            newseg += lst_segs[idx]
        lst_segs_new.append(newseg)

    if idx_segindcs_untouched < len_segindcs_untouched:
        while idx_segindcs_untouched < len_segindcs_untouched:
            lst_segs_new.append(lst_segs[idx_seg_untouched])
            idx_segindcs_untouched += 1
            if idx_segindcs_untouched == len_segindcs_untouched:
                break
            idx_seg_untouched = segindcs_untouched[idx_segindcs_untouched]

    return lst_segs_new


def get_best_split(lst_segs):
    # First join where distance is basically 0 between segments
    assert len(lst_segs) != 0
    if len(lst_segs) == 1:
        return lst_segs
    indcs = []
    for i, (seg1, seg2) in enumerate(zip(lst_segs[:-1], lst_segs[1:])):
        d = seg2.start_time_s - seg1.end_time_s
        if d < 0.005:
            indcs.append(i+1)

    lst_segs = join_at_indcs(lst_segs, indcs)
    
    if len(lst_segs) == 1:
        return lst_segs

    gains = gainfunc(lst_segs)
    idx = np.argmax(gains)
    while gains[idx] > 0:
        lst_segs = join_at_indcs(lst_segs, [idx+1])

        if len(lst_segs) == 1:
            break
        gains = gainfunc(lst_segs)
        idx = np.argmax(gains)

    return lst_segs


def finalise_segs(lst_segs):
    """ If possible increases the boundaries of the segments. """
    for i in range(len(lst_segs) - 1):
        diff_ = (lst_segs[i+1].start_time_s - lst_segs[i].end_time_s) / 2
        diff_ = min(diff_, 0.15)  # capping at padding of 0.15s
        lst_segs[i].end_time_s = lst_segs[i].end_time_s + diff_
        lst_segs[i+1].start_time_s = lst_segs[i+1].start_time_s - diff_


def ctm2seg(fpath_ctm, fpath_seg, wavid):
    lst_segs = []
    skipped, total = 0, 0
    logger.info(f'Creating segments file from ctm: {fpath_ctm}')
    with open(fpath_ctm) as fh:
        for line in fh:
            if '<unk>' in line:
                continue
            try:
                line = line.split()
                duration = float(line[3])
                total += 1
                if duration > 5.0:
                    skipped += 1
                    continue
                lst_segs.append(Seg([line[4]], float(line[2]), float(line[2])+float(line[3])))
            except:
                print(line)
                raise

    if skipped > 0:
        logger.info(f'Skipped {skipped} / {total} words because their duration was too long (>5s) for file {fpath_ctm}!')

    lst_segs = get_best_split(lst_segs)

    finalise_segs(lst_segs)

    with open(fpath_seg, 'w') as fh_new:
        for i, seg in enumerate(lst_segs):
            words = ' '.join(seg.words)
            segid = f'{wavid}_{i+1}'
            fh_new.write(f'{segid} {seg.start_time_s:.2f} {seg.end_time_s:.2f} {words}\n')
    logger.info(f'Created segments file: {fpath_seg}')


if __name__ == '__main__':
    import plac
    plac.call(ctm2seg)
