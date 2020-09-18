#!/usr/bin/env python3
import argparse
import subprocess
import tempfile

SPACE = '▁'
PLACEHOLDER = "(S)"

parser = argparse.ArgumentParser(description = "Takes a list of sentencepiece units and produces a lexicon file for them, "
        "using an external G2P command. Essentially takes care of the special space character. Meant for use with "
        "make_lfst_spm.py and needs to be called twice: once for the Kaldi lang prep, and again with the "
        "--add-placeholders option.\n"
        "If called without --add-placeholders, the space characters do not produce any phones in the lexicon. "
        "This corresponds to the paths where optional silences are not used. This should be the case which requires "
        "most disambiguation symbols. We of course need to use the maximum of disambiguation symbols to make sure "
        "the resulting FST is determinizable.")
parser.add_argument("units_file",
        help = "Path to file containing all sentencepiece units, one per line")
parser.add_argument("--g2p-cmd",
        help = "A shell command which takes a path to a file containing "
        "one word per line, and produces a pronunciation for each, in the format: "
        "<word> <phone1> <phone2> <phone3>\n "
        "NOTE: the g2p input file will be input in the position {filepath}",
        default = "phonetisaurus-g2pfst --model=g2p_wfsa --print_scores=false --wordlist={filepath} | sed 's/\t$/\tSPN/'"
        )
parser.add_argument("--add-placeholders",
        help = "Add a special symbol as a placeholder for the space character.",
        action = "store_true"
        )

args = parser.parse_args()

# Read the units and figure out all unit parts which need a pronunciation
units = []
parts = []
with open(args.units_file, encoding='utf-8') as fi:
    for line in fi:
        unit = line.strip()
        units.append(unit)
        unit_parts = filter(None, unit.split(SPACE))  # filter leaves out empty parts
        parts.extend(unit_parts)
parts = list(set(parts))  # Uniquefy

# Get a pronunciation for each part
with tempfile.NamedTemporaryFile(mode="w+t", encoding="utf-8") as tmpf:
    tmpf.write("\n".join(parts))
    tmpf.flush()
    proc_out = subprocess.run(args.g2p_cmd.format(filepath=tmpf.name), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            shell=True,
            encoding="utf-8")
    if proc_out.returncode != 0:
        raise RuntimeError("G2P cmd failed!\nSTDOUT:\n"+str(proc_out.stdout)+"\nSTDERR:\n"+str(proc_out.stderr))

part_lexicon = {}
for line in proc_out.stdout.split("\n"):
    if not line:
        continue
    part, *pronunciation = line.strip().split()
    part_lexicon[part] = pronunciation
# Add an empty pronunciation for an empty part:
part_lexicon[""] = []

# Produce the lexicon file 
for unit in units:
    pronunciation = []
    build_part = ""
    for char in unit:
        if char == SPACE:
            pronunciation.extend(part_lexicon[build_part])
            if args.add_placeholders:
                pronunciation.append(PLACEHOLDER)
            build_part = ""
        else:
            build_part += char
    pronunciation.extend(part_lexicon[build_part])
    print(unit, " ".join(pronunciation))
