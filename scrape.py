#!/bin/env python3
# File: scrape.sh
# Author: Steven Lee
# Date: 03/21/2024

from extract import extract_internal_links
import os
import re
import sys

def parse(html, url, fd):
    '''Define my own parse function!
       @param html  HTML page object (bs4.BeautifulSoup)
    '''
    # Remove content in all <nav>.
    navs = html.find_all('nav')
    for nav in navs:
        nav.clear()

    # Remove Table of Content on right-hand side.
    toc = html.find(id='toc')
    if toc:
        toc.clear()

    version = html.find(id='version-selector')
    if version:
        version.clear()

    text = html.body.get_text()
    text = re.sub(r'\n(?:\s*\n)+', '\n', text)

    print(f'---{url}', file=fd)
    print(text, file=fd)
    #print(html.body.get_text(), file=fd)
    #print(html, file=fd)


if __name__ == '__main__':
    recurse = True
    link_file = 'in.txt'
    data_file = 'out.txt'
    exclude_file = 'excludes.txt'
    verbose = 0
    start_url = ''

    USAGE = f'''\
Scrape text from web pages
Usage: {os.path.basename(__file__)} [--recurse] [-x|--exclude-file <file>]
         [-v] [-vv] [-h|--help] <url>
  where <url> = starting URL to scrape pages (https or http)
        --recurse = scrape recursively
        -x, --exclude-file <file> = file containing list of URLs to exclude
        -v = verbose mode; displays all URLs
        -vv = more verbose
        -h, --help = display usage
'''

    # Process arguments
    idx = 1
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if arg == '--recurse':
            recurse = True
        elif arg == '-x' or arg == '--exclude-file':
            idx += 1
            if idx == len(sys.argv):
                print('Missing exclude filename', file=sys.stderr)
                sys.exit(2)
            exclude_file = sys.argv[idx]
        elif arg == '-v':
            verbose = 1
        elif arg == '-vv':
            verbose = 2
        elif arg == '-h' or arg == '--help':
            print(USAGE)
            sys.exit(0)
        elif arg[0] != '-':
            start_url = arg
        else:
            print('Unknown argument:', arg, file=sys.stderr)
            sys.exit(2)
        idx += 1

    if start_url == '':
        print('Starting URL must be specified\n', file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(2)

    # Scraping starts here!
    extract_internal_links(start_url, data_file, link_file, exclude_file,
          recurse, 0, verbose, parse)
