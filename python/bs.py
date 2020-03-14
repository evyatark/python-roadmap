from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from datetime import date,timedelta
import glob
import logging
from time import time,strptime
from dateutil import parser
from queue import Queue
from threading import Thread


DELTA = 2   # in days. if article date is less than DELTA days ago, it will be added to index
LIMIT = 500
HTML_START = '<html dir="rtl" lang="he"><head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/></head><body>'
HTML_END = '</body></html>'
base_dir = '/home/evyatar/GitHub/github-pages-hello-world/haaretz/'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_queue_with_workers(number_of_workers, f):
    queue = Queue()
    # Create worker threads
    for x in range(number_of_workers):
        worker = f(queue)
        #worker = DownloadWorker(queue)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    return queue

class ArticleWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            article = self.queue.get()
            try:
                do_with_article(article)
            finally:
                self.queue.task_done()

articles_queue = start_queue_with_workers(8, lambda x: ArticleWorker(x))

def send_article_to_queue(article):
    articles_queue.put(article)


class DownloadWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            id, url = self.queue.get()
            try:
                article = readAndProcess(id, url)
                send_article_to_queue(article)
            finally:
                self.queue.task_done()





class Article:
    def __init__(self, id, header, publishedAt, updatedAt, fullHtml, subject, sub_subject):
        self.id = id
        self.header = header
        self.publishedAt = publishedAt
        self.updatedAt = updatedAt
        self.fullHtml = fullHtml
        self.subject = subject
        self.sub_subject = sub_subject

    # other fields: subject


def construct_html(body, existing_body):
    return HTML_START + body + existing_body + HTML_END


def omit(tag):
    omitted = BeautifulSoup("<div>omitted " + tag + "</div>", "html.parser")
    return omitted

def load_html(request):
    response = urlopen(request)
    html = response.read()
    return html


def readAndProcess(id, url):
    ts = time()
    logger.info("loading %s...", url)
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    ##
    #
    html = load_html(request)
    #
    ##
    logger.info('[%s] loading completed in %s seconds', id, time() - ts)
    ts = time()
    logger.info("[%s] souping...", id)
    bs = BeautifulSoup(html, 'html.parser')
    try:
        header = bs.article.header.h1.contents[-1]
    except:
        header = "@@@"

    logger.info('[%s] souping completed in %s seconds', id, time() - ts)
    ts = time()
    logger.info("[%s] processing...", id)
    sections = bs.article.findAll(name='section', class_='b-entry')
    if len(sections) == 0:
        return Article(id, header, '', '', '', '', '')
    first = sections[0]
    publishedAt = ""
    updatedAt = ""
    try:
        logger.debug("1")
        published = bs.article.find(name='meta', attrs={"property": "article:published"})
        if (published is not None):
            logger.debug("1.1")
            publishedAt = bs.article.find(name='meta', attrs={"property": "article:published"}).attrs['content']
        if bs.article.find(name='meta', attrs={"property": "article:modified"}) is not None:
            logger.debug("1.2")
            updatedAt = bs.article.find(name='meta', attrs={"property": "article:modified"}).attrs['content']
    except:
        pass
    if (publishedAt=='' and updatedAt==''):
        try:
            logger.debug("1.3")
            updatedAt = bs.html.find(lambda tag: tag.name == "time" and "datetime" in tag.attrs.keys()).attrs['datetime']
            publishedAt = updatedAt
        except:
            pass

    #sections[0].replace_with(omit('section 0'))

    header_crumbs_root = bs.article.find(name='ol', class_='c-article-header__crumbs')
    header_crumbs = header_crumbs_root.find_all('li', class_='c-article-header__crumb')
    subject = ''
    sub_subject = ''
    if len(header_crumbs) > 0:
        subject = header_crumbs[0].text.rstrip().lstrip()
    if len(header_crumbs) > 1:
        sub_subject = header_crumbs[1].text.rstrip().lstrip()

    logger.debug("2")
    if first.find(class_='c-quick-nl-reg') is not None:
        first.find(class_='c-quick-nl-reg').replace_with(omit('c-quick-nl-reg'))
    logger.debug("3")
    if first.find(class_='c-related-article-text-only-wrapper') is not None:
        first.find(class_='c-related-article-text-only-wrapper').replace_with(omit('c-related-article-text-only-wrapper'))
    logger.debug("4")
    all_figures = first.find_all(name='figure')
    while (len(all_figures) > 0):
        first.find(name='figure').replace_with(omit('figure'))
        all_figures = first.find_all(name='figure')

    logger.debug("5")
    while (first.find(class_="c-dfp-ad") is not None):
        first.find(class_="c-dfp-ad").replace_with(omit("c-dfp-ad"))

    logger.debug("6")
    bs.html.find(name='div',attrs={"hidden":""}).replace_with(omit('hidden'))
    bs.html.find(attrs={"id":"amp-web-push"}).replace_with(omit('amp-web-push'))
    #bs.html.find(name='section',attrs={"amp-access":"TRUE"}).replace_with(omit('amp-access'))
    logger.debug("7")
    bs.html.find(name='amp-sidebar').replace_with(omit('amp-sidebar'))
    while (bs.html.find(name='div', attrs={"class":"delayHeight"}) is not None):
        bs.html.find(name='div', attrs={"class": "delayHeight"}).replace_with(omit("delayHeight"))

# convert every <section amp-access="NOT ampConf.activation OR currentViews &lt; ampConf.maxViews OR subscriber">
# to     <section amp-access="TRUE">
    logger.debug("8")
    list_of_sections = bs.html.findAll(
        lambda tag: tag.name == "section" and "amp-access" in tag.attrs.keys() and tag.attrs['amp-access'] != "TRUE")
    for section in list_of_sections:
        logger.debug(".", end='')
        section.attrs['amp-access'] = "TRUE"

    logger.debug("9")
    bs.html.body.attrs['style'] = "border:2px solid"
    # assuming that 3rd child of <head> is not needed and can be changed...
    bs.html.head.contents[3].attrs={"name":"viewport","content":"width=device-width, initial-scale=1"}
    htmlText=bs.html.prettify()
    logger.info('[%s] processing completed in %s seconds', id, time() - ts)
    logger.debug("!")
    return Article(id, header, publishedAt, updatedAt, htmlText, subject, sub_subject)






article_ids = []

#urls = [ 'https://www.haaretz.co.il/amp/1.8600567',


def saveToFile(id, htmlText):
    name = "h" + id + ".html"
    fileName = base_dir + name
    f = open(fileName, "w")
    f.write(htmlText)
    f.close()

    logger.info("[%s] file: %s", id, fileName)
    return name, fileName


def generate_index(articles):
    body = ''
    for key in reversed(sorted(articles.keys())):
        articleObject = articles[key]
        body = body + articleObject.link
    return construct_html(body, "")



def send_urls_to_queue(ids):
    logger.info("starting queue 1")
    queue = start_queue_with_workers(8, lambda x: DownloadWorker(x))
    for id in ids:
        url = 'https://www.haaretz.co.il/amp/' + id
        logger.info("[%s] inserting id %s in queue 1", id, id)
        queue.put((id, url))    # will cause calling readAndProcess(id, url)
    logger.info("completed inserting all IDs to queue")
    queue.join()
    logger.info("queue 1 joined")

def do_with_article(articleObject):
    try:
        today = date.today()
        #url = 'https://www.haaretz.co.il/amp/' + id
        #articleObject = readAndProcess(id, url)
        #so_far = so_far + 1
        #logger.info("completed %d out of %d", so_far, numberOfIds)
        if articleObject.fullHtml == '':
            return
        file_relative_path, file_full_path = saveToFile(articleObject.id, articleObject.fullHtml)
        time = articleObject.updatedAt
        if (time == ''):
            time = articleObject.publishedAt
        articleObject.link = '<p>[' + articleObject.subject + '/' + articleObject.sub_subject + ']<b>' + articleObject.publishedAt + '</b><a href="' + file_relative_path + '">' + str(
            articleObject.header) + '</a></p>'
        #body = body + articleObject.link
        logger.info("[%s] published at %s, updated at: %s", articleObject.id, articleObject.publishedAt, articleObject.updatedAt)

        # delta = today.day - parser.parse(articleObject.publishedAt).day
        if (articleObject.publishedAt.startswith('2020-') and
                today.day - parser.parse(articleObject.publishedAt).day < DELTA):
            key = generate_key(articleObject)
            add_article(key, articleObject)      #articles[key] = articleObject
            logger.info("[%s] article added to index of today", articleObject.id)
            #counter = counter + 1
            #if counter > LIMIT:
            #    break
    except:
        logger.error("some exception with id %s", id)

articles = {}
def add_article(key, article):
    articles[key] = article
    logger.info("[%s] article added to index of today with key %s", article.id, key)


def doSomeIds(ids):
    articles = {}
    counter = 0
    so_far = 0
    body = ''
    today = date.today()
    numberOfIds = len(ids)
    send_urls_to_queue(ids)
    for id in ids:
        try:
            url = 'https://www.haaretz.co.il/amp/' + id
            articleObject = readAndProcess(id, url)
            so_far = so_far + 1
            logger.info("completed %d out of %d", so_far, numberOfIds)
            if articleObject.fullHtml=='':
                continue
            file_relative_path, file_full_path = saveToFile(articleObject.id, counter, articleObject.fullHtml)
            time = articleObject.updatedAt
            if (time == ''):
                time = articleObject.publishedAt
            articleObject.link = '<p>['+articleObject.subject+'/'+articleObject.sub_subject +']<b>' + articleObject.publishedAt + '</b><a href="' + file_relative_path + '">' + str(articleObject.header) + '</a></p>'
            body = body + articleObject.link
            logger.info("published at %s, updated at: %s", articleObject.publishedAt, articleObject.updatedAt)
            if (articleObject.publishedAt.startswith('2020-') and
                    today.day - parser.parse(articleObject.publishedAt).day < DELTA):
                key = generate_key(articleObject)
                articles[key] = articleObject
                logger.info("article added to index of today")
                counter = counter + 1
                if counter > LIMIT:
                    break
        except:
            logger.error("some exception with id %s", id)
    when_all_articles_added()


def when_all_articles_added():
    logger.info('generating index for %d articles...', len(articles))
    html = generate_index(articles)
    f = open(base_dir + 'index.html', "w")
    f.write(html)
    f.close()


def generate_key(articleObject):
    return articleObject.subject + articleObject.sub_subject + articleObject.publishedAt + articleObject.id

def first_page():
    url = 'https://www.haaretz.co.il'
    logger.info("loading first page %s...", url)
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    logger.info("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    list_of_articles = bs.html.findAll(
        lambda tag: tag.name == "article" and "id" in tag.attrs['class'])
    links = {"1"}
    for article in list_of_articles:
        hrefs = article.find_all("a")
        for href in hrefs:
            #print (href.attrs["href"])
            links.add(href.attrs["href"])
    links.remove("1")
    #print("links:")
    ids = []
    for link in links:
        #print(link)
        if "1.86" in link:
            start = link.find("1.86")
            id = link[start:]
            ids.append(id)
    for id in ids:
        logger.debug(id)
    return ids


def scan(name):
    bs = BeautifulSoup(urlopen("file://" + name), 'html.parser')
    if (bs.html==None):
        return "",""
    header = bs.html.body.find("h1")
    h = header.text.lstrip().rstrip()
    return name, h


def find_existing_articles(path):
    files = [f for f in glob.glob(path + "**/h1*.html", recursive=False)]
    body = ''
    for f in files:
        name, header = scan(f)
        if name=="":
            continue
        relative_path = name.lstrip(path)
        link = '<p><a href="h' + relative_path + '">' + str(header) + '</a></p>'
        body = body + link
    return body

def process_page(url):
    logger.info("loading url %s...", url)
    try:
        user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        request = Request(url, headers={'User-Agent': user_agent})
        response = urlopen(request)
        html = response.read()
    except:
        logger.error("some exception when trying to retrieve URL %s", url)
        return []
    logger.info("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    list_of_articles = bs.html.find_all(
        lambda tag: (tag.name == "a") and ('href' in tag.attrs.keys()) and ("1.86" in tag.attrs['href']), recursive=True)
    links = {"1"}
    for href in list_of_articles:
        links.add(href.attrs["href"])
    links.remove("1")
    #print("links:")
    ids = []
    for link in links:
        #print(link)
        if "1.86" in link:
            start = link.find("1.86")
            id = link[start:]
            ids.append(id)
    for id in ids:
        logger.debug(id)
    return ids


def remove_duplicates(article_ids):
    set = {'0'}
    for id in article_ids:
        if ('#' in id):
            id = id[:id.find('#')]
        if ('?' in id):
            id = id[:id.find('?')]
        set.add(id)
    set.remove('0')
    return list(set)


def urls():
    return [    'https://www.haaretz.co.il/magazine'
    ,   'https://www.haaretz.co.il/news'
    , 'https://www.themarker.com/allnews'
    , 'https://www.themarker.com/wallstreet'
    , 'https://www.themarker.com/misc/all-headlines'
    , 'https://www.themarker.com/realestate'
    , 'https://www.themarker.com/technation'
    , 'https://www.themarker.com/magazine'
    ,'https://www.haaretz.co.il/sport'
    ,'https://www.haaretz.co.il/news/elections'
    ,'https://www.haaretz.co.il/news/world'
    ,'https://www.haaretz.co.il/news/education'
    ,'https://www.haaretz.co.il/news/politics'
    ,'https://www.haaretz.co.il/news/law'
    ,'https://www.haaretz.co.il/news/health'
    ,'https://www.haaretz.co.il/news/local'
    ,'https://www.haaretz.co.il/gallery'
    ,'https://www.haaretz.co.il/gallery/television'
    ,'https://www.haaretz.co.il/opinions'
    ,'https://www.haaretz.co.il/captain'
    , 'https://www.haaretz.co.il/science'
    , 'https://www.haaretz.co.il/literature'
       ]

if __name__ == "__main__":
    article_ids = first_page()
    for url in urls():
        more_article_ids = process_page(url)
        article_ids.extend(more_article_ids)
        article_ids = remove_duplicates(article_ids)
    logger.info("now sending %d articles",len(article_ids))
    send_urls_to_queue(article_ids)
    # at this point queue1 was joined (done inside send_urls_to_queue)

    articles_queue.join()   # this will wait for queue2 completing?
    logger.info("articles queue joined")
    when_all_articles_added()
