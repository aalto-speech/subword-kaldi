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



