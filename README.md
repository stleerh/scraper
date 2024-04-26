# Scraper
Scrape web pages to be used for Retrieval-Augmented Generation (RAG).

## Usage
1. Update **exclude.txt** to exclude any external links that you don't want to scrape.
2. Do a test run.<br>
`./run.sh <url>`<br><br>
This fetches the web page for the URL only.  The data is stored in the file **data.txt** and the URL retrieved is stored in **links.txt**.
3. To recursively fetch all the web pages starting from a URL, enter:<br>
`./run.sh <url> --recurse`<br><br>
Please note that this script does not check for a **robots.txt** file, so do so only on sites that don't restrict web crawling.

### Chunk files
GPT models have a limit on the size of the context window.  This means, you might need to reduce the size of your data file.  To chunk your files into a smaller size, use the **chunk.py** script.  For example, to chunk files into 10M, enter:<br>
`./chunk.py -n 10M <data_file>`<br>

It chunks files on a web page boundary, so it's possible for a file to exceed the chunk size if the web page is larger than the chunk size.  Therefore, if you want each page to be its own file, just specify `-n 1`.  The chunk filenames will be based on the data filename.  If that is data.txt, then the chunk files are named data-001.txt, data-002.txt, and so on.

To see all options, use the -h option.
`./chunk.py -h`

### Preparse web page data
If you want to do some data cleaning, see the example in [**scrape.py**](https://github.com/stleerh/scraper/blob/main/scrape.py).  The script must be written in Python and it ultimately calls `extract_internal_links`, which is defined in **extract.py**.  Your script then implements a `parse` function that it calls each time it retrieves a web page.

```
def parse(html, url, fd):
   @param html  HTML page object (bs4.BeautifulSoup)
   @param url  Web page URL
   @param fd  Write the output using this file descriptor
```
[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) is the Python library used to parse HTML and create a Python structure.
