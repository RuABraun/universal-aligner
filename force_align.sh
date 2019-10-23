#!/bin/bash -e
set -o pipefail


opts="--transition-scale=1.0 --self-loop-scale=0.1 --batch-size=1"
shift=0.01

if [ $# != 7 ]; then
    echo "Wrong number of arguments."
    echo "Required: work-dir audiofile text am-dir lex unknown-phones-file mfcc-config"
    exit 1
fi

work=`readlink -f $1`
faudio=`readlink -f $2`
ftext=`readlink -f $3`
am=`readlink -f $4`
lex=`readlink -f $5`
f_unknown_jnk=`readlink -f $6`
mfcc_config=`readlink -f $7`

beam=512

echo "Work dir: $work"

echo "file $faudio" > $work/wav.scp

# Build data/lang
local=$work/local
tmplang=$work/tmplang
lang=$work/lang

if [ ! -f $work/prepdone ]; then
	mkdir -p $local
	mkdir -p $tmplang
	mkdir -p $lang

	echo "sil" > $local/silence_phones.txt
	echo "sil" > $local/optional_silence.txt
	cat $local/silence_phones.txt| awk '{printf("%s ", $1);} END{printf "\n";}' > $local/extra_questions.txt || exit 1;

	awk '{for(i=2;i<=NF;i++) a[$i];} END {for(w in a) print w}' $lex | grep -v 'sil' > $local/nonsilence_phones.txt
	cp $lex $local/lexicon.txt

	utils/prepare_lang.sh --phone-symbol-table $am/phones.txt $local "<unk>" $tmplang $lang 2>&1 > $work/preplang.log

	# Building HCLG
	textint=$work/text.int
	utils/sym2int.pl $lang/words.txt $ftext | tr '\n' ' ' > $textint
	echo "file $textint" > $work/text.scp

	compile-train-graphs $opts $am/tree $am/final.mdl $lang/L.fst scp:$work/text.scp ark:$work/HCLG.fst.ark

	# Feats prep
	compute-mfcc-feats --config=$mfcc_config scp,p:$work/wav.scp ark:- | \
	    copy-feats --compress=true ark:- ark,scp:$work/raw_mfcc.ark,$work/raw_mfcc.scp

	compute-cmvn-stats scp:$work/raw_mfcc.scp ark,scp:$work/cmvn.ark,$work/cmvn.scp
fi
cmnv_opts=$(cat $am/cmvn_opts)
feats="ark,s,cs:apply-cmvn $cmnv_opts scp:$work/cmvn.scp scp:$work/raw_mfcc.scp ark: | add-deltas ark:- ark:- |"

touch $work/prepdone

echo "Doing biased decoding"

gmm-latgen-faster --beam=$beam --lattice-beam=20 --max-active=3000 --min-active=200 --boost-likel=true --jnk_phone_ids_fpath=$f_unknown_jnk \
		--word-symbol-table=$work/lang/words.txt $am/final.mdl \
    ark:$work/HCLG.fst.ark "$feats" ark:- | \
lattice-align-words $lang/phones/word_boundary.int $am/final.mdl ark:- ark:- | \
    lattice-1best --acoustic-scale=0.1 ark:- ark:- | \
    nbest-to-ctm --frame-shift=0.01 --print-silence=false ark:- - | \
    utils/int2sym.pl -f 5 $lang/words.txt > $work/out.ctm

echo "Done"

