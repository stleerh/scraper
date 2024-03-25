#!/bin/env python3

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import requests
import sys

text_flg = False
url = ''

USAGE = f'''\
Extract text from web pages
Usage: {os.path.basename(__file__)} [-h|--help] <url>
  where <url> = starting URL to scrape pages (https or http)
        -t, --text = get text
        -h, --help = display usage
'''

# Process arguments
idx = 1
while idx < len(sys.argv):
    arg = sys.argv[idx]
    if arg == '-t' or arg == '--text':
        text_flg = True
    elif arg == '-h' or arg == '--help':
        print(USAGE)
        sys.exit(0)
    elif arg[0] != '-':
        url = arg
    else:
        print('Unknown argument:', arg, file=sys.stderr)
        sys.exit(2)
    idx += 1

if url == '':
    print('Url must be specified\n', file=sys.stderr)
    print(USAGE, file=sys.stderr)
    sys.exit(2)

response = requests.get(url)
if response.status_code < 200 or response.status_code > 299:
    print(f'  Error {response.status_code}, {url}', file=sys.stderr)
    sys.exit(3)

if text_flg:
    html_page = BeautifulSoup(response.content, 'html.parser')
    print(html_page.body.get_text())
else:
    print(response.content.decode('utf-8'))
