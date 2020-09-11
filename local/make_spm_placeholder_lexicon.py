#!/usr/bin/env python3
import argparse
import subprocess
import tempfile

SPACE = '▁'
PLACEHOLDER = "(S)"

parser = argparse.ArgumentParser()
parser.add_argument("units_file",
        help = "Path to file containing all sentencepiece units, one per line")
parser.add_argument("--g2p-cmd",
        help = "A shell command which takes a path to a file containing "
        "one word per line, and produces a pronunciation for each, in the format: "
        "<word> <phone1> <phone2> <phone3>\n "
        "NOTE: leave a space at the end of the command if needed",
        default = "phonetisaurus-g2pfst --model=g2p_wfsa --print_scores=false --wordlist="
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
    proc_out = subprocess.run(args.g2p_cmd + tmpf.name, 
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
# Add an empty pronunciation for an emtpy part:
part_lexicon[""] = []

# Produce the intermediate lexicon (with placeholders)
for unit in units:
    pronunciation = []
    build_part = ""
    for char in unit:
        if char == SPACE:
            pronunciation.extend(part_lexicon[build_part])
            pronunciation.append(PLACEHOLDER)
            build_part = ""
        else:
            build_part += char
    pronunciation.extend(part_lexicon[build_part])
    print(unit, " ".join(pronunciation))
