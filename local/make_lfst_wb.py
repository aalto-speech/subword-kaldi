#!/usr/bin/env python3
import sys
import math

# Three base states.
# 0, start-state, all arcs from _E phones
# 1, all arcs to _B phones (connected with 1 through <w>)
# 2, all arcs from and to _I phones
next_state=5

def print_word(word, phones, start, end, from_state, to_state):
    global next_state
    cur_state = from_state
    
    phones = list(phones)

    disambig = []
    while len(phones) > 0 and phones[-1].startswith("#"):
        disambig.insert(0,phones[-1])
        phones = phones[:-1]
        
    #make sure no disambig phones were hiding somewhere else in the sequence
    assert not any(p.startswith("#") for p in phones)

    phones = [p.split('_')[0] for p in phones]
    labels = ["I"] * len(phones)    
    
    if start: 
        labels[0] = "B" 
    if end:
        labels[-1] = "E"
    if len(phones) == 1 and start and end:
        labels[0] = "S"

    phones = ["{}_{}".format(p,l) for p,l in zip(phones, labels)] + disambig

    assert len(phones) > 0

    while len(phones) > 1:
        print("{}\t{}\t{}\t{}".format(cur_state,next_state,phones[0],word))
        cur_state = next_state
        next_state += 1
        word = "<eps>" 
        phones = phones[1:] 
   
    print("{}\t{}\t{}\t{}".format(cur_state,to_state,phones[0],word))

disambig_symbol = sys.argv[1]
disambig_symbol2 = sys.argv[2]
disambig_symbol3 = sys.argv[3]
print("{}\t{}\t{}\t{}\t{}".format(0,4,"SIL","<w>", -math.log(0.5)))
print("{}\t{}\t{}\t{}".format(4,1,disambig_symbol ,"<eps>"))
print("{}\t{}\t{}\t{}\t{}".format(0,1,disambig_symbol3,"<w>", -math.log(0.5)))

print("{}\t{}\t{}\t{}".format(2,3,disambig_symbol2,"<eps>"))

for line in sys.stdin:
    word, prob, phones = line.strip().split(None, 2)
    phones = phones.split()
    
    assert len(phones) > 0 
    if word == "<w>": continue 
    print_word(word, phones, True, True, 1, 0)
    if word == "<UNK>": continue
    print_word(word, phones, False, True, 3, 0)
    print_word(word, phones, True, False, 1, 2)
    print_word(word, phones, False, False, 3, 2)
   
print("{}\t0".format(1)) 
