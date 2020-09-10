#!/usr/bin/env python3
import sys
import math
import argparse
import fileinput
import collections

SPACE = '▁'
CHAR = 'justnotaspace'  # can be anything but not the SPACE
EMPTY = "<eps>"
SILENCE = "SIL"
HALF = -math.log(0.5)

# Start of word and end of word states:
AFTER_CHAR = 0  # Word has ended, but haven't seen space yet.
SIL_BRIDGE = 1
AFTER_SPACE = 2  # Word has ended, and we have seen a space.
# Inside word states:
INSIDE_WORD = 3
IN_WORD_BRIDGE = 4
# The next free state:
NEXT_STATE = 5

## NOTE: We will not support multiple consecutive space characters,
##  even though sentencepiece does. The reason is that when transcribing
##  speech, the number of spaces is by convention always just one.

parser = argparse.ArgumentParser()
parser.add_argument("disambig_no_sil", 
        help = "Disambiguation symbol for no silence")
parser.add_argument("disambig_sil", 
        help = "Disambiguation symbol for silence")
parser.add_argument("disambig_infix", 
        help = "Disambiguation symbol for infix")
parser.add_argument("--lexicon-file", default="-",
        help = "Path to lexicon file. If not given, read from stdin instead.")
parser.add_argument("--char-phone-map", 
        help = "Path to file mapping between characters and phones. "
        "File should contain two columns: char, mapped phone. "
        "Note that if a phone is not found in the mapping, it will be "
        "mapped to itself. "
        "This script only supports character based lexica, "
        "but sometimes e.g. utf-8 characters are mapped to ASCII symbols.")
args = parser.parse_args()

# Handle the mapping:
class UnityDict(collections.UserDict):
    # if queried with unknown key, returns key
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return key
mapping = UnityDict()
if args.char_phone_map is not None:
    # Load file here
    with open(args.char_phone_map) as fi:
        for line in fi:
            phone, mapped = line.strip().split()
            mapping[phone] = mapped

# A couple of printing helpers
def print_edge(from_state, to_state, consume, output, cost = 0.):
    print("{from_state}\t{to_state}\t{consume}\t{output}\t{cost}".format(
        from_state=from_state, to_state=to_state, consume=consume, 
        output=output, cost=cost))
def print_end(state):
    print("{state}".format(state=state))

def handle_one_connection(from_state, to_state, word, disambig, starts, ends):
    """
    Handles one position (complete, infix, prefix, suffix) for a subword.
    May need to be called multiple times for a subword.
    starts, ends should be True when the connections starts from beginning of
    word or ends at end of word (needed for proper _B and _E handling)
    """
    global NEXT_STATE
    # First, figure out the phone placement labels (_B, _E, _I, _S)
    labels = []
    before = SPACE if starts else CHAR
    after = SPACE if ends else CHAR
    groups = zip([before,] + list(word[0:-1]),
        list(word),
        list(word[1:]) + [after,])
    for left, curr, right in groups:
        if curr == SPACE:
            labels.append("")
        elif left == SPACE and right == SPACE:
            labels.append("_S")
        elif left == SPACE:
            labels.append("_B")
        elif right == SPACE:
            labels.append("_E")
        else:
            labels.append("_I")
    # Disambig symbols go in the end, and they have no label
    to_consume = list(word) + list(disambig)
    for disambig_symbol in disambig:
        labels.append("")
    # So there is now a label for each char and disambig symbol
    # i.e. every symbol to be consumed
    # (spaces and disambig symbols have empty labels)

    # Also make the outputs:
    to_output = [EMPTY] * len(to_consume)
    to_output[0] = word

    # Create the states:
    froms = []; tos = []
    froms.append(from_state)
    for _ in range(len(to_consume) - 1):
        tos.append(NEXT_STATE)
        froms.append(NEXT_STATE)
        NEXT_STATE += 1
    tos.append(to_state)

    # Finally, print out edges:
    for inp, label, out, fr, to in zip(to_consume, labels, to_output, froms, tos):
        if inp == SPACE:
            # Two paths for the optional silence
            print_edge(fr, to, SILENCE, SPACE, HALF)
            print_edge(fr, to, args.disambig_no_sil, SPACE, HALF)
        else:
            # Do the mapping here (sorry it's a little ugly)
            mapped = mapping[inp]
            print_edge(fr, to, mapped + label, out)

# First, establish the basic connections (optional silence, in word disambig)
print_edge(AFTER_CHAR, AFTER_SPACE, args.disambig_no_sil, SPACE, HALF)
print_edge(AFTER_CHAR, SIL_BRIDGE, SILENCE, SPACE, HALF)
print_edge(SIL_BRIDGE, AFTER_SPACE, args.disambig_sil, EMPTY)
print_edge(INSIDE_WORD, IN_WORD_BRIDGE, args.disambig_infix, EMPTY)

# Iterate on stdin
for line in fileinput.input(args.lexicon_file):
    word, prob, *phones = line.strip().split()

    # First extract the disambig phones from the end:
    disambig = []
    while len(phones) > 0 and phones[-1].startswith("#"):
        disambig.insert(0,phones[-1])
        phones = phones[:-1]
    # Sanity checks:
    # make sure no disambig phones were hiding somewhere else in the sequence
    assert not any(p.startswith("#") for p in phones)
    # make sure there are no consecutive spaces:
    assert SPACE*2 not in word

    if word == SPACE:
        # Handled separately.
        # Note that other single character subwords are handled properly
        # by handle_one_connection already.
        continue  

    # last_char and first_char can refer to the same (single) char
    first_char = word[0] 
    last_char = word[-1]
    if first_char == SPACE and last_char == SPACE:  # _sub_word_
        # Can only appear as complete
        handle_one_connection(AFTER_CHAR, AFTER_SPACE, 
                word, disambig, 
                starts = True, ends = True)
    elif first_char == SPACE:  # _sub_word
        # Can appear as complete:
        handle_one_connection(AFTER_CHAR, AFTER_CHAR, 
                word, disambig, 
                starts = True, ends = True)
        # Or can appear as prefix:
        handle_one_connection(AFTER_CHAR, INSIDE_WORD, 
                word, disambig, 
                starts = True, ends = False)
    elif last_char == SPACE:  # sub_word_
        # Can appear as complete:
        handle_one_connection(AFTER_SPACE, AFTER_SPACE, 
                word, disambig, 
                starts = True, ends = True)
        # Or can appear as suffix:
        handle_one_connection(IN_WORD_BRIDGE, AFTER_SPACE,
                word, disambig,
                starts = False, ends = True)
    else:  # sub_word
        # Can appear as complete:
        handle_one_connection(AFTER_SPACE, AFTER_CHAR,
                word, disambig,
                starts = True, ends = True)
        # Or can appear as prefix:
        handle_one_connection(AFTER_SPACE, INSIDE_WORD,
                word, disambig,
                starts = True, ends = False)
        # Or can appear as infix:
        handle_one_connection(IN_WORD_BRIDGE, INSIDE_WORD,
                word, disambig,
                starts = False, ends = False)
        # Or can appear as suffix:
        handle_one_connection(IN_WORD_BRIDGE, AFTER_CHAR,
                word, disambig,
                starts = False, ends = True)


# Finally, output the final states:
print_end(AFTER_SPACE)
print_end(AFTER_CHAR)
