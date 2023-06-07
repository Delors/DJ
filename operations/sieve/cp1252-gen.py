#!/usr/bin/python3
# Author: Matthias Ulbrich

# Generates a file with all valid cp1252 chars to be used with sieve.

# How-to-use:
#
# ./cp1252-gen.py
# iconv -f cp1252 -t utf-8 cp1252_needs_conversion_to_utf8.txt > cp1252.txt

# 0x00-0x20 are non-printable special chars such as NUL,CR,...
# The code position 7F in the cp1252 table is the special char DEL.
# The following code positions in the cp1252 table are undefined(!): 0x81, 0x8D, 0x8F, 0x90, 0x9D

with open("cp1252.txt", "wb") as f:
    for x in  range(0x21, 0x100):
        if x in [0x7f, 0x81, 0x8D, 0x8F, 0x90, 0x9D]:
            continue
        f.write(bytearray([x]))
