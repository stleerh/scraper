#!/bin/env python3
# Extract text from all internal links given a URL or a file containing a
#   list of links
# Author: Steven Lee
# Date: 03/20/2024, 03/21/2024

# Note: On Windows, you must set the encoding to utf-8.  If using Git Bash,
#   export PYTHONIOENCODING='utf-8'

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import requests
import sys

def extract_internal_links(url, data_fn=None, link_fn=None, exclude_fn=None,
      recurse=False, order=0, verbose=0, parse=None):
    '''Extract web text
       @paraam url  Starting URL to scrape
       @param data_fn  Write web text to this file
       @param link_fn  Write URLs that were scraped to this file
       @param exclude_fn  List of URLs to not scrape
       @param recurse  If false, scrape only the starting URL else recursively scrape.
       @param order  0 to scrape depth-first, 1 to scrape breadth-first
       @param verbose  0 for silent, 1 or 2 for level of verbosity
       @param parse  Parse web page function
    '''
    exclude_list = []
    if exclude_fn:
        try:
            with open(exclude_fn) as f:
                exclude_list = [ln.strip() for ln in f.readlines()]
        except FileNotFoundError:
            print('Exclude file not found:', exclude_list, file=sys.stderr)
            sys.exit(1)

    fd1 = None
    if data_fn:
        try:
            fd1 = open(data_fn, 'w', encoding='utf-8')
        except FileNotFoundError:
            print('Uanble to write to', data_fn, file=sys.stderr)
            sys.exit(1)

    fd2 = None
    if link_fn:
        try:
            fd2 = open(link_fn, 'w', encoding='utf-8')
        except FileNotFoundError:
            print('Uanble to write to', link_fn, file=sys.stderr)
            sys.exit(1)

    u = urlparse(url)
    start_url = f'{u.scheme}://{u.netloc}{u.path}'.rstrip('/')
    all_links = [start_url]

    if recurse:
        index = 0
        while index < len(all_links):
            html, url = handle_web_page(all_links[index], fd1, fd2, parse)
            if html:
                if url != all_links[index]: # url was redirected?
                    index += 1
                    all_links.insert(index, url) # insert redirected url

                add_links(html, all_links, index, exclude_list, order, verbose)

            index += 1
    else:
        handle_web_page(start_url, fd1, fd2, parse)

    if fd1:
        fd1.close()
    if fd2:
        fd2.close()


def extract_links_from_file(url_fn, data_fn=None, parse=None):
    '''Extract web text from a file containing URLs
       @paraam url_fn  File consisting of URLs to scrape
       @param data_file  Write web text to this file
       @param parse  Parse web page function
    '''
    fd = None
    if data_fn:
        try:
            fd = open(data_fn, 'w', encoding='utf-8')
        except FileNotFoundError:
            print('Uanble to write to ' + data_fn, file=sys.stderr)
            sys.exit(1)

    try:
        with open(url_fn) as f:
            for url in f.readlines():
                url = url.strip()
                handle_web_page(url, fd, None, parse)
    except FileNotFoundError:
        print('File not found: ' + url_fn, file=sys.stderr)
        sys.exit(1)

    if fd:
        fd.close()


def handle_web_page(url, fd1=None, fd2=None, parse=None):
    '''Handle web page at this url
       @param url  Scrape this URL
       @param fd1  File descriptor for data file
       @param fd2  File descriptor for URL file
       @param parse  Parse web page function
       @return HTML page object and url (may be redirected)
    '''
    print(url)
    if fd2:
        print(url, file=fd2)

    response = requests.get(url)
    if response.status_code < 200 or response.status_code > 299:
        print(f'  Error {response.status_code}, {url}', file=sys.stderr)
        return None, response.url

    html_page = BeautifulSoup(response.content, 'html.parser')
    if fd1:
        if parse is None:
            parse = parse_web_page  # default callback function
        parse(html_page, url, fd1)
    return html_page, response.url


def parse_web_page(html_page, url, data_fd=None):
    '''Default parse web page function
       @param html_page  HTML page object
       @param url  URL
       @param data_fd  File descriptor for data file
    '''
    print(html_page.body.get_text(), file=data_fd)


def add_links(html_page, all_links, url_idx, exclude_list=[], order=0, verbose=0):
    '''Add unique links found in HTML document.
       @param html_page  HTML page object
       @param all_links  List of URLs that have or will be scraped
          *** all_links can change.
       @param url_idx  Index into 'all_links'.  This must be the 'html_page' object.
       @param exclude_list  List of URLs to not scrape
       @param order  0 = depth-first order, 1 = breadth-first order
       @param verbose  0 for silent, 1 or 2 for level of verbosity
    '''
    # See if HTML document defines a <base href>.
    base_href = None
    base = html_page.find_all('base')
    if base:
        base_href = base[-1].get('href')
        if base_href and len(base_href) > 0 and base_href[-1] != '/':
            base_href += '/'

    # If not, get it from the URL.
    if base_href is None:
        u = urlparse(all_links[url_idx])
        base_href = f'{u.scheme}://{u.netloc}{os.path.dirname(u.path)}'
        if base_href[-1] != '/':
            base_href += '/'

    # Find and add unique <a href> links.
    url_idx += 1  # add 1 to insert links after url_idx
    links = html_page.find_all('a')
    for link in links:
        link_url = link.get('href')
        if link_url: # <a> tag must have an href
            if verbose >= 2:
                print('  link =', link_url)

            u = urlparse(link_url)
            if link_url[0] == '#' or u.scheme not in ['', 'http', 'https']:
                continue

            if u.fragment:
                link_url = u._replace(fragment='').geturl() # remove fragment in URL

            new_url = None
            if u.scheme == '': # Relative link?
                # All relative links will be scraped.
                new_url = urljoin(base_href, link_url).rstrip('/')
                if verbose >= 1:
                    print(f'  {base_href}, {link_url} => {new_url}')
            elif link_url.startswith(base_href): # Same base URL?
                new_url = link_url.rstrip('/')

            if new_url and new_url not in exclude_list:
                if order == 0:  # depth-first order
                    add = False
                    try:
                        idx = all_links.index(new_url)
                        if idx >= url_idx:  # If found, delete it and add it earlier.
                            del all_links[idx]
                            add = True
                    except ValueError:
                        add = True

                    if add:
                        all_links.insert(url_idx, new_url)
                        url_idx += 1
                        if verbose >= 1:
                            print('  add =', new_url, flush=True)
                else:  # breadth-first order
                    if new_url not in all_links:
                        all_links.append(new_url)
                        if verbose >= 1:
                            print('  add =', new_url, flush=True)


# Start here
if __name__ == '__main__':
    recurse = False
    link_file = ''
    data_file = ''
    order = 0  # depth-first order
    exclude_file = ''
    verbose = 0
    start_url = ''
    url_file = ''

    USAGE = f'''\
Extract text from web pages
Usage: {os.path.basename(__file__)} [--recurse] [-o <data_file>] [--ol <link_file>]]
         [--breadth [-x|--exclude-file <exc_file>] [-v] [-vv] [-h|--help]
         <url>|<url_file>
  where <url> = starting URL to scrape pages (https or http)
        <url_file> = file containing list of URLs to scrape pages
        --recurse = scrape recursively
        -o <data_file> = write web text to this file
        --ol <link_file> = write list of URLs to this file
        --breadth = process URLs in breadth-first order (default: depth-first)
        -x, --exclude-file <exc_file> = file containing list of URLs to exclude
        -v = verbose mode; displays all URLs
        -vv = more verbose
        -h, --help = display usage

  One of url or file must be specified.
'''

    # Process arguments
    idx = 1
    while idx < len(sys.argv):
        arg = sys.argv[idx]
        if arg == '--recurse':
            recurse = True
        elif arg == '-o':
            idx += 1
            if idx == len(sys.argv):
                print('Missing filename to store web text', file=sys.stderr)
                sys.exit(2)
            data_file = sys.argv[idx]
        elif arg == '--ol':
            idx += 1
            if idx == len(sys.argv):
                print('Missing filename to store URLs', file=sys.stderr)
                sys.exit(2)
            link_file = sys.argv[idx]
        elif arg == '--breadth':
            order = 1  # breadth-first order
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
            if arg.startswith('https://') or arg.startswith('http://'):
                start_url = arg
            else:
                url_file = arg
        else:
            print('Unknown argument:', arg, file=sys.stderr)
            sys.exit(2)
        idx += 1

    if start_url == '' and url_file == '':
        print(USAGE, file=sys.stderr)
        sys.exit(2)

    # Scraping starts here!
    if start_url:
        # start_url = starting URL to scrape
        # data_file = write web text to this file
        # link_file = write URLs that were scraped to this file
        # exclude_file = list of URLs to not scrape
        # recurse = if false, scrape only the starting URL else recursively scrape
        # order = 0 to scrape depth-first, 1 to scrape breadth-first
        # verbose = 0 for silent, 1 or 2 for level of verbosity
        extract_internal_links(start_url, data_file, link_file, exclude_file,
              recurse, order, verbose)
    else:
        # url_file = File consisting of URLs to scrape
        # data_file  = write web text to this file
        extract_links_from_file(url_file, data_file)
