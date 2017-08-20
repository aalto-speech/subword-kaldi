# Create a subword Lexicon FST for Kaldi

This is the code belonging to the paper [Improved subword modeling for WFST-based speech recognition](https://research.aalto.fi/en/publications/improved-subword-modeling-for-wfstbased-speech-recognition(ed43f22c-f5bd-45ad-99a7-628f82f2283c).html).


For each subword marking style (word boundary marker, left-right marked, left-marked, right-marked) a seperate script exists in `local/` that can create a L.fst.

The standard way to use this scripts is:
    
    extra=3
    utils/prepare_lang.sh --phone-symbol-table data/lang/phones.txt --num-extra-phone-disambig-syms $extra data/subword_dict "<UNK>" data/subword_lang/local data/subword_lang
    
    dir=data/subword_lang
    tmpdir=data/subword_lang/local

    # Overwrite L_disambig.fst
    common/make_lfst_wb.py $(tail -n$extra $dir/phones/disambig.txt) < $tmpdir/lexiconp_disambig.txt | fstcompile --isymbols=$dir/phones.txt --osymbols=$dir/words.txt --keep_isymbols=false --keep_osymbols=false | fstaddselfloops  $dir/phones/wdisambig_phones.int $dir/phones/wdisambig_words.int | fstarcsort --sort_type=olabel > $dir/L_disambig.fst 

For the other scripts (l/r/lr-marked ) the number of extra disambiguation symbols can be reduced to 1

## What type of marking style is the best?

This unfortunately depends on your language and dataset. We have seen different optimal values for different datasets and languages.

## Limitiations

 - The lexicon files are not updated in the lang directory, so lexicon-based alignment of lattices will not work (fix in progress)
 - At this moment all pronunciations will have probability 1 (which is common anyway for grapheme-based systems). If custom probabilities are required the `local/make_lfst_*.py` files should be updated to include them.


## Help

Feel free to make an issue or send me an email on peter.smit@aalto.fi if you have trouble getting these scripts to work.
