# Python Idioms and Recipes

Below are some Python Cookbook recipes that I collected along the way. It is not enough to know the programming language. There are many small everyday programming tasks that you should know. And they can be achieved only through experience. I list mine below, and this list will grow as I gain experience.

## Date and time

#### How to display the date of today (as a String)?
```
Python 3.6.7 (default, Oct 22 2018, 11:32:17) [GCC 8.2.0] on linux
>>> import datetime
>>> str(datetime.date.today())
'2020-04-04'
>>> 
```

#### How to print debug messages?
You can of course use print(), but this becomes a burden if you have a lot of them. Arriving from the Java world, I decided it is better to start from the beginning with a decent Logger.

```Python
import logging
...

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
...

    logger.debug("[%s] loading %s...", id, url)

```

you get a log like this:
```
2020-04-05 00:12:41,235 - __main__ - INFO - [1.8735773] 2020-04-03 added to index of today with key דעות2020-04-03T00:01:00+03001.8735773
2020-04-05 00:12:44,742 - __main__ - INFO - publishedDateAsStr=2020-03-30 minimalAllowedDateAsStr=2020-04-02
2020-04-05 00:12:44,742 - __main__ - INFO - stopped processing this article - too old
```

#### Saving text to a file

Here is my solution:
```Python
def saveToFile(id, htmlText):
    fileName = base_dir + "h" + id + ".html"
    f = open(fileName, "w")
    f.write(htmlText)
    f.close()
```

#### How to retry a function call if it resulted with an exception?
I use `tenacity`. There are several other libraries that do similar things.

```Python
import tenacity

@tenacity.retry(wait=tenacity.wait_fixed(1), stop=tenacity.stop_after_delay(30))
def process_page(url, limit):
    logger.info("loading url %s...", url)
    try:
        response = urlopen(request)
        ...
```



