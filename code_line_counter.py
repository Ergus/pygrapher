#!/usr/bin/env python3

# Copyright (C) 2022  Jimmy Aguilar Mena

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, re

text :str = ""

try:
    with open(sys.argv[1], 'r') as f:
        text = f.read()

except IOError:
    print("File not accessible")

# Pattern for function
func :str = r'^void\s+((?:\w+)(?:_ompss2|_mpi))\s*\([^)]*\)\s*({(?s:.+?)^})'
re_func = re.compile(func, flags=re.MULTILINE)

matches = re.findall(re_func, text)

for i in matches:
    tmp :str = re.sub(r'\t', ' ', i[1])                      # replace all tabs with 1 space
    #tmp = re.sub(r' *\\\n *', ' ', tmp)                      # join lines ending with \
    tmp = re.sub(r'//.*\n', '\n', tmp)                       # comments //
    tmp = re.sub(r'/\*(?s:.+?)\*/', "", tmp)                 # comments /**/
    tmp = re.sub(r'(assert|myassert|modcheck)\s*\(.+\);', "", tmp)  # no keywords
    tmp = re.sub(r' +if +\(.+== *0\) *\{[^}]*\}', "", tmp)   # if {print....}
    tmp = re.sub(r'\n *(?=\n)', '', tmp)                     # no empty lines

    print (tmp)
    print("Lines: ", len(re.findall(r'\n', tmp)), '\n')
