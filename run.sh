#!/bin/bash

USAGE="Usage: run.sh <url> [--recurse]
    where --recurse = Fech web pages recursively

It excludes URLs listed in excludes.txt.

Files created:
- links.txt - List of web pages that were fetched
- data.txt - Web page data all in this file
"

start_date=$(date)

if [ $# -eq 0 ]; then
    echo "$USAGE" >&2
    exit 2
fi

url="$1"
shift

python extract.py "$url" -x excludes.txt -o data.txt --ol links.txt $@

echo "Start: $start_date"
echo "End:   $(date)"
