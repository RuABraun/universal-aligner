""" Get pronunciations for arbitrary language using espeak-ng. """
import locale
import multiprocessing as mp
import subprocess as sp
import tempfile
from os.path import abspath

import regex as re
from loguru import logger

JOBS = mp.cpu_count()
ptn_punct = re.compile("[ˌːˈ]")
ptn_brack = re.compile("\([a-z]+\)")
espeak_mappings = {'b̥': 'b', 'ʔ': 't', 'ɾ': 't', 'd̥': 'd', 't͡ʃ': 'ch', 'tʃ': 'ch',
                    'd͜ʒ̊': 'j', 'd͡ʒ': 'j', 'dʒ': 'j', 'ɡ': 'g', 'ɡ̊': 'g', 'v̥': 'v', 'θ': 'th', 't̪': 'th',
                    'ð': 'dh', 'ð̥': 'dh', 'd̪': 'dh', 'z̥': 'z', 'ʃ': 'sh', 'ʒ̊': 'j',
                    'ʒ': 'j', 'ɦ': 'h', 'ɱ': 'm', 'ŋ': 'ng', 'ɫ': 'l', 'l': 'l', 'l̥': 'l',
                    'ɫ̥': 'l', 'ɤ': 'l', 'ɹ': 'r', 'ɻ': 'r', 'ɹ̥': 'r', 'ɻ̊': 'r', 'n̩': 'n', 'ᵻ': 'i',
                    'w̥': 'w', 'ʍ': 'hw', 'χ': 'x', 'nʲ': 'n', 'ɔ̃': 'ɔ', 'ɑ̃': 'ɑ', 'j': 'y', 'oʊ': 'oh', 'æ': 'a', 'ææ': 'a', 'ɚ': 'er', 'ç': 'h'}  # some look the same but are not !!

compound_splitting = {'iə': ('i', 'ə',), 'aɪʊɹ': ('aɪ', 'ʊ', 'ɹ',), 'aɪə': ('aɪ', 'ə',), 'ɪɹ': ('ɪ', 'ɹ',), 'ɑɹ': ('ɑ', 'ɹ',),
                    'ɔɹ': ('ɔ', 'ɹ',), 'ʊɹ': ('ʊ', 'ɹ',), 'oɹ': ('o', 'ɹ',), 'ɛɹ': ('ɛ', 'ɹ',), 'aɪɚ': ('aɪ', 'ɚ',), 'aʊə': ('aʊ', 'ə',),
                    'aɪʊ': ('aɪ', 'ʊ',), 'əɹ': ('ə', 'ɹ',), 'ʊɐ': ('oo', 'r',), }

toascii_mappings = {'əʊ': 'oh', 'ʊə': 'oo', 'ɑ': 'a', 'ɐ': 'a', 'ɒ': 'o', 'ə': 'uh',
                    'ɛ': 'e', 'ɜ': 'er', 'ɣ': 'g', 'ɪ': 'i', 'eə': 'er', 'ɔɪ': 'oi', 'əl': 'l', 'eɪ': 'ay',
                    'aɪ': 'ai', 'ʌ': 'uh', 'aʊ': 'ow', 'ʊ': 'oo', 'ɔ': 'aw', 'u': 'oo', 'ɹ': 'r', 'ɚ': 'er', 'ø': 'oo', 'ɲ': 'n', 'ɬ': 'sh', 'β': 'b',
                    'ɡʲ': 'g', 'ɔø': 'oi', 'ʏ': 'ue', 'œ': 'oe', 'ɛɪ': 'ay', 'œ̃': 'a', '1': None}  #  gh == glottal stop

final_mappings = {'er': 'r'}

valid_prons = set('ai th ch ay er oh oi oo aw sh ow uh dh a b d e f g h i j ng k sil l m n o p r s t v w x z y ts ue oe pf'.split())
eng_model_prons = set('a ai aw ay b ch d dh e f g h i j jnk k l m n ng o oh oi oo ow p r s sh sil t th uh v w x y z'.split())


def call_espeak(fpath_in, fpath_out, lang):
    cmd = f'cat {fpath_in} | while read w; do printf $w" "; espeak-ng -v {lang} -x -q --ipa=1 --stdout $w; done > {fpath_out}'
    sp.check_output(cmd, shell=True).decode('utf-8')


def get_prons_for_words(fpath_in, fpath_out, lang):
    call_espeak(fpath_in, fpath_out, lang)


def strip_espeak(fpath_in, lang, fpath_unknown_phones):
    assert locale.getlocale()[1] == 'UTF-8', 'Should be using UTF-8 locale!'

    with open(fpath_in) as fh:
        text = fh.read()
    lst_word_n_prons = text.splitlines()
    newtext = []
    set_unknown_prons = set()
    cnt_words_with_unknown_prons = 0
    for line in lst_word_n_prons:
        line = ptn_punct.sub('', line)
        line = line.replace('_', ' ')
        line = ptn_brack.sub('', line)
        line = re.sub("\([a-z-]+\)", "", line)
        line = line.split()
        word, phones = line[0], line[1:]
        tmp = []
        for c in phones:
            if lang == 'de':
                if c == 'ɾ':
                    c = 'r'
            else:
                if c == 'ɾ':
                    c = 't'
            c = espeak_mappings.get(c, c)
            cs = compound_splitting.get(c, [c])
            for c in cs:
                tmp.append(c)
        phones = []
        for c in tmp:
            c = toascii_mappings.get(c, c)
            c = final_mappings.get(c, c)
            if c is not None:
                phones.append(c)

        for c in phones:
            if c not in valid_prons:
                logger.info(f'Unknown pron {c}')
            if c not in eng_model_prons:
                if fpath_unknown_phones is None:
                    logger.warn(f'New unknown pron {c}, not using word: {word}')
                    break
                else:
                    cnt_words_with_unknown_prons += 1
                    if c not in set_unknown_prons:
                        set_unknown_prons.add(c)
        else:
            line = word + ' ' + ' '.join(phones)
            if word == '<unk>':
                line = word + ' jnk'
                newtext.append(line)
            else:
                newtext.append(line)
    logger.info(f'Num words with unknown prons / Num words total: {cnt_words_with_unknown_prons} / {len(lst_word_n_prons)}')
    logger.info(f'Num unknown prons found: {len(set_unknown_prons)}')

    newtext = list(set(newtext))
    return newtext, set_unknown_prons


def get_prons(fpath_in, fpath_out, lang, fpath_unknown_phones=None):

    assert locale.getlocale()[1] == "UTF-8", "Should be using UTF-8 locale!"
    logger.info(f'Getting prons for word list {abspath(fpath_in)}')
    with tempfile.NamedTemporaryFile() as tmp_fh:
        get_prons_for_words(fpath_in, tmp_fh.name, lang)
        lst_word_n_prons, set_unknown_prons = strip_espeak(tmp_fh.name, lang, fpath_unknown_phones)

    accepted_words = ["<unk> jnk", "<sil> sil"]  # default words with prons in vocab
    for word_n_prons in lst_word_n_prons:
        word, *pron = word_n_prons.split()
        pron = ' '.join(pron)

        accepted_words.append(f'{word} {pron}')
    accepted_words = list(set(accepted_words))

    with open(fpath_out, "w") as fh:
        for line in accepted_words:
            if line.strip():
                fh.write(f'{line}\n')

    with open(fpath_out.split('.')[0] + '_nounknown.' + fpath_out.split('.')[1], 'w') as fh:
        for line in accepted_words:
            if line.strip():
                word, *prons = line.split()
                final_prons = []
                for p in prons:
                    if p in set_unknown_prons:
                        final_prons.append('jnk')
                    else:
                        final_prons.append(p)
                line = ' '.join(final_prons)
                fh.write(f'{word} {line}\n')

    with open(fpath_unknown_phones, 'w') as fh:
        for p in set_unknown_prons:
            fh.write(f'{p}\n')
    logger.info(f'Done getting prons, written out to {abspath(fpath_out)}')


def main(fpath_in, fpath_out, lang, fpath_unknown_phones=None):
    """ Get pronunciations for file with a word on each line. """
    get_prons(fpath_in, fpath_out, lang, fpath_unknown_phones)


if __name__ == "__main__":
    import plac
    plac.call(main)
