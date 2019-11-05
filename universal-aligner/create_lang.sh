#!/bin/bash -e


if [ $# != 4 ]; then
	echo "Wrong number of arguments!"
	echo "Required: lexicon workdir amdir newdir"
	exit 1
fi

lex=$1
work=$2
am=$3
lang=$4

local=$work/local
tmplang=$work/tmplang

mkdir -p $tmplang
mkdir -p $local
mkdir -p $lang

echo "sil" > $local/silence_phones.txt
echo "sil" > $local/optional_silence.txt
cat $local/silence_phones.txt| awk '{printf("%s ", $1);} END{printf "\n";}' > $local/extra_questions.txt || exit 1;

awk '{for(i=2;i<=NF;i++) a[$i];} END {for(w in a) print w}' $lex | grep -v 'sil' > $local/nonsilence_phones.txt
cp $lex $local/lexicon.txt

utils/prepare_lang.sh --phone-symbol-table $am/phones.txt $local "<unk>" $tmplang $lang 2>&1 > $work/preplang.log