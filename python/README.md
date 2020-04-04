# Python Roadmap

In this project I investigate some programming challenges and architectural styles, while excercising writing Python code.

## web scraping

These scripts perform web scraping, using BeautifulSoup python library.

### Haaretz

The bs.py sub-project demonstrates web scraping of haaretz.co.il site (bypassing the paywall...)

First, a list of all articles of today is created (by following links inside the site, starting from several main web-pages of the site). Then, each article is retrieved, processed, and saved as a seperate file.
Finally, an index page is generated, supplying a convenient list of all articles of the day.

The script runs periodically, typically once a day, or once every 6 hours.

All generated web pages are committed, so they can be available for browsing, using github-pages as a host.
