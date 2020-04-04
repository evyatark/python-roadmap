# Python Roadmap

In this project I investigate some programming challenges and architectural styles, while excercising writing Python code.

## Web scraping

These scripts perform web scraping, using BeautifulSoup python library.

### Haaretz

The `bs.py` sub-project demonstrates web scraping of haaretz.co.il site (bypassing the paywall...)

First, a list of all articles of today is created (by following links inside the site, starting from several main web-pages of the site). Then, each article is retrieved, processed, and saved as a seperate file.
Finally, an index page is generated, supplying a convenient list of all articles of the day.

The script runs periodically, typically once a day, or once every 6 hours.

All generated web pages are committed, so they can be available for browsing, using github-pages as a host.

## Executing the Code

* clone
* add a virtual env
* open with PyCharm
* set a correct value to `base_dir`
* run `bs.py`
* open `base_dir`/index.html in a browser

or 
* commit and push `base_dir`/* to a github-pages branch, then open the index.html using a github-pages URL (for example https://evyatark.github.io/github-pages-hello-world/haaretz/index.html)
