#!/bin/bash -e

. path.sh
. cmd.sh

nj=1
stage=0
work=
language=

. utils/parse_options.sh

exp=$work/exp
data=$work/lang
lang=$work/lang_${language}

if [ $stage -le 0 ]; then
	create_lang.sh $work/lexicon.txt $work $lang
fi

if [ $stage -le 1 ]; then
	steps/make_mfcc.sh --nj 4 --mfcc-config $work/mfcc.conf --write-utt2num-frames true --cmd "$train_cmd" $data/train_init
	steps/compute_cmvn_stats.sh $data/train_init
	utils/fix_data_dir.sh $data/train_init
fi

if [ $stage -le 2 ]; then
	utils/subset_data_dir.sh $data/train_init 30000 $data/train_30k
	steps/train_mono.sh --nj $nj --cmd "$train_cmd" $data/train_30k $lang $exp/mono
	steps/align_si.sh --nj $nj --cmd "$train_cmd" $data/train_30k $lang $exp/mono $exp/mono_ali
fi

context_ops="--context-width=3 --central-position=1"
if [ $stage -le 3 ]; then
	steps/train_deltas.sh --context_opts "$context_ops" --cmd "$train_cmd" 5000 60000 $data/train_init $lang $exp/mono_ali \
		$exp/tri1
fi;