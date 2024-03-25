#!/bin/env python3
# Chunk the file into 10 MB per file
# Author: Steven Lee
# Date: 03/21/2024

# Note: It reads the entire file in memory.

import os
import re
import sys

text_flg = False
url = ''

USAGE = f'''\
Chunk the file into n bytes per file
Usage: {os.path.basename(__file__)} [-h|--help] <url>
  where <file> = file to chunk
        -n = max number of bytes per file unless the web page
               is larger; can use K for kilobytes and M for megabytes
        -h, --help = display usage

If -n is not specified, it will create a file for each web page.
'''

# Process arguments
nbytes = 0

idx = 1
filename = ''
while idx < len(sys.argv):
    arg = sys.argv[idx]
    if arg == '-n':
        idx += 1
        if idx == len(sys.argv):
            print('Missing number of bytes', file=sys.stderr)
            sys.exit(2)
        try:
            value = sys.argv[idx]
            value_idx = len(value)
            multiplier = 1

            if value.endswith('K') or value.endswith('KB'):
                multiplier = 1024
                if value.endswith('K'):
                    value_idx -= 1
                else:
                    value_idx -= 2

            if value.endswith('M') or value.endswith('MB'):
                multiplier = 1048576
                if value.endswith('M'):
                    value_idx -= 1
                else:
                    value_idx -= 2

            nbytes = int(sys.argv[idx][:value_idx]) * multiplier
            if nbytes < 1:
                print('Number of bytes must be a positive number.', file=sys.stderr)
                sys.exit(2)
        except ValueError:
            print('Must specify the number of bytes such as 512, 100K, or 10M.', file=sys.stderr)
            sys.exit(2)
    elif arg == '-h' or arg == '--help':
        print(USAGE)
        sys.exit(0)
    elif arg[0] != '-':
        filename = arg
    else:
        print('Unknown argument:', arg, file=sys.stderr)
        sys.exit(2)
    idx += 1

if filename == '':
    print('Filename must be specified.\n', file=sys.stderr)
    print(USAGE, file=sys.stderr)
    sys.exit(2)


# Real work starts here!
path_fn, ext = os.path.splitext(filename)
count = 1
cur_idx = 0
last_idx = -1

def write_file(content):
    global count

    if len(content) == 0:
        return

    chunk_fn = f'{path_fn}-{count:02}{ext}'
    try:
        with open(chunk_fn, 'w') as fw:
            print(f'Writing {chunk_fn}, {len(content)} bytes...')
            fw.write(content)
    except IOError as err:
        print(f'Error on file {chunk_fn}:', err)
        sys.exit(1)
    count += 1


try:
    with open(filename) as fr:
        data = fr.read()  # read entire file in memory
except FileNotFoundError:
    print(f'Unable to open file {filename}', file=sys.stderr)
    sys.exit(1)

# Search for the scraping file delimiter (defined in scrape.py), which
# begins with "---http".
for match in re.finditer(r'^---http', data, flags=re.MULTILINE):
    if match.start() - cur_idx > nbytes:
        if last_idx != -1:
            # Back off to previous match so it's less than nbytes.
            write_file(data[cur_idx:last_idx])
            cur_idx = last_idx
            last_idx = match.start()
        else:
            # Only one chunk so it may exceed nbytes
            write_file(data[cur_idx:match.start()])
            cur_idx = match.start()
            last_idx = -1
    else:
        last_idx = match.start()

# Handle last match
size = len(data)
if size - cur_idx > nbytes:
    if last_idx != -1:
        write_file(data[cur_idx:last_idx])
        cur_idx = last_idx

if size - cur_idx > 0:
    write_file(data[cur_idx:])
