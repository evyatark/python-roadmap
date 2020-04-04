'''

This project demonstrates web scraping of Haaretz site,
generating an index of all articles of today.

This version of the script uses 2 queues in order to split the work
and thus increase performance by
1. execute the retrieval from WEB in several concurrent threads
2. separate retrieval from the processing

'''
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from datetime import date,timedelta
import glob
import logging
import time as time1
from time import time
from dateutil import parser
from queue import Queue
from threading import Thread
import tenacity

'''
 static variables:
'''
DELTA = 2   # in days. if article date is less than DELTA days ago, it will be added to index
LIMIT = 5000
NUMBER_OF_Q1_WORKERS=1
NUMBER_OF_Q2_WORKERS=50
HEADER_OF_UNKNOWN = "@@@"
HTML_START = '''
<!DOCTYPE html>
<html dir="rtl" lang="he">
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
        <!-- Metro 4 -->
        <link rel="stylesheet" href="https://cdn.metroui.org.ua/v4/css/metro-all.min.css"/>
    </head>
    <body>
'''
    #'<html dir="rtl" lang="he"><head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/></head><body>'
HTML_END = '''
    <script src="https://cdn.metroui.org.ua/v4/js/metro.min.js"></script>
    </body>
</html>'''
base_dir = '/home/evyatar/GitHub/github-pages-hello-world/haaretz/'
minimalAllowedDateAsStr = str(date.today())

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

'''=========================================
====='''
class ArticleWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            article = self.queue.get()
            try:
                result = do_with_article(article)
            finally:
                self.queue.task_done()


'''=========================================
====='''
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
            except:
                pass
            finally:
                self.queue.task_done()

'''=========================================
====='''

articles_queue = start_queue_with_workers(NUMBER_OF_Q2_WORKERS, lambda x: ArticleWorker(x))
ids_queue = start_queue_with_workers(NUMBER_OF_Q1_WORKERS, lambda x: DownloadWorker(x))


'''=========================================
====='''

def send_article_to_queue(article):
    articles_queue.put(article)


class Article:
    def __init__(self, id, header, publishedAt, updatedAt, fullHtml, subject, sub_subject):
        self.id = id
        self.header = header
        self.publishedAt = publishedAt
        self.updatedAt = updatedAt
        self.fullHtml = fullHtml
        self.subject = subject
        self.sub_subject = sub_subject
        self.href = ''

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


def fast_find_times(bs):
    try:
        publishedAt = bs.head.find(name='meta', attrs={"property": "og:pubdate"}).attrs['content']
        return publishedAt
    except:
        return ''

def find_times(bs):
    publishedAt = ""
    updatedAt = ""
    try:
        logger.debug("1")
        elements = bs.find_all('time')
        if (elements is not None) and (len(elements) > 0):
            publishedAt = elements[0]['datetime']
            updatedAt = elements[1]['datetime']
        else:
            published = bs.head.find(name='meta', attrs={"property": "article:published"})
            if (published is not None):
                logger.debug("1.1")
                publishedAt = bs.head.find(name='meta', attrs={"property": "article:published"}).attrs['content']
            if bs.head.find(name='meta', attrs={"property": "article:modified"}) is not None:
                logger.debug("1.2")
                updatedAt = bs.head.find(name='meta', attrs={"property": "article:modified"}).attrs['content']
    except:
        pass
    if (publishedAt=='' and updatedAt==''):
        try:
            publishedAt = bs.head.find(name='meta', attrs={"property": "og:pubdate"}).attrs['content']
            logger.debug("1.3")
            updatedAt = bs.html.find(lambda tag: tag.name == "time" and "datetime" in tag.attrs.keys()).attrs['datetime']
            #publishedAt = updatedAt
        except:
            pass
    if (publishedAt == ''):
        publishedAt = todayAsStr()  #'2020-03-25T00:01:00+0200'
    if (updatedAt == ''):
        updatedAt = todayAsStr() # '2020-03-25T00:01:00+0200'
    return publishedAt, updatedAt


def readAndProcess(id, url):
    ts = time()
    logger.debug("[%s] loading %s...", id, url)
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    ##
    #
    html = load_html(request)
    #
    ##
    logger.debug('[%s] loading completed in %s seconds', id, time() - ts)
    ts = time()
    logger.debug("[%s] souping...", id)
    bs = BeautifulSoup(html, 'html.parser')

    # first find publish time, if too old, we don't need to continue parsing
    if not decide_include_article(fast_find_times(bs)):
        logger.info("stopped processing this article - too old")
        return Article(id, HEADER_OF_UNKNOWN, '', '', '', '', '')


    try:
        header = bs.article.header.h1.contents[-1]
    except:
        header = HEADER_OF_UNKNOWN

    logger.debug('[%s] souping completed in %s seconds', id, time() - ts)
    ts = time()
    logger.debug("[%s] processing...", id)   # TODO use bs.find_all('time')[0]['datetime'] and bs.find_all('time')[1]['datetime']
    if (bs.article is None):
        return Article(id, header, '', '', '', '', '')
    sections = bs.article.findAll(name='section', class_='b-entry')
    if (sections is None) or len(sections) == 0:
        return Article(id, header, '', '', '', '', '')
    first = sections[0]

    publishedAt, updatedAt = find_times(bs)

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
    logger.debug('[%s] processing completed in %s seconds', id, time() - ts)
    logger.debug("!")
    return Article(id, header, publishedAt, updatedAt, htmlText, subject, sub_subject)


def todayAsStr():
    return str(date.today())



article_ids = []

#urls = [ 'https://www.haaretz.co.il/amp/1.8600567',


def saveToFile(id, htmlText):
    name = "h" + id + ".html"
    fileName = base_dir + name
    f = open(fileName, "w")
    f.write(htmlText)
    f.close()

    logger.debug("[%s] file: %s", id, fileName)
    return name, fileName


def sort_by_subject(articles):
    sorted = []
    existing_subjects = []
    # list_of_subjects = [article.subject for article in articles.values() if article.subject is not None]
    # list_of_subjects_without_duplicates = list(set(list_of_subjects))
    # list_of_subjects_without_duplicates.sort()
    for subject in subjects().keys():
        keys_of_articles_with_that_subject = [key for key in articles.keys() if articles[key].subject==subject]
        if len(keys_of_articles_with_that_subject) > 0:
            existing_subjects.append(subject)
        keys_of_articles_with_that_subject.sort(reverse=True)
        articles_with_that_subject = [articles[key] for key in keys_of_articles_with_that_subject]
        sorted.extend(articles_with_that_subject)
    articles_with_subject_not_in_list = [article for article in articles.values() if article.subject not in subjects().keys()]
    sorted.extend(articles_with_subject_not_in_list)
    if (len(articles_with_subject_not_in_list) == 0):
        logger.warn("unknown subjects: %s", str(articles_with_subject_not_in_list).strip('[]'))

    return sorted, existing_subjects

def generate_index(articles):
    body = ''
    sortedBySubject, existing_subjects = sort_by_subject(articles)

    #assume for now that existing_subjects is sorted correctly
    counter = 0
    for subject in existing_subjects:
        counter = counter + 1
        idStr = "collapse_toggle_" + str(counter)
        # before each subject add this:
        body = body + '<button class="button" id="' + idStr + '">[' \
           + subject + ''']</button>
            <div class="pos-relative w-75 border border-size-4 bd-black">    
            '''

        for articleObject in sortedBySubject:
            if (articleObject.subject == subject):
                # for all items inside:
                # the value of data-toggle-element should be same as the id of button above
                # and the id should change for each subject: collapse_toggle_1, collapse_toggle_2, ...
                # <div class=" w-100" data-role="collapse" data-toggle-element="#collapse_toggle_2">
                #replace "COLLAPSE_ID" with idStr
                link = str(articleObject.link).replace("COLLAPSE_ID", idStr)
                body = body + link

        # after each subject add this:
        body = body + '</div>'
    # end of outer for loop


    return construct_html(body, "")

def subjects():
    priorities = {}
    list = [
        'חדשות'
        ,'ספורט'
        , 'TheMarker'
        , 'סוף שבוע'
        , 'דעות'
        , 'בריאות'
        , 'קפטן אינטרנט'
        , 'מדע'
        , 'בלוגים'
        , 'אוכל'
        , 'תרבות'
        , 'ספרים'
        # , ''
        # , ''
        # , ''
        # , ''
    ]
    for i in range(0, len(list)):
        priorities[list[i]] = i
    return priorities

def send_url_to_queue(ids_queue, id):
    url = 'https://www.haaretz.co.il/amp/' + id
    logger.debug("[%s] inserting id %s in ids queue", id, id)
    ids_queue.put((id, url))  # will cause calling readAndProcess(id, url)


def send_urls_to_queue(ids_queue, ids):
    for id in ids:
        send_url_to_queue(ids_queue, id)
    logger.debug("completed inserting %d IDs to queue", len(ids))


def create_link(articleObject):
    articleObject.href = "h" + articleObject.id + ".html"
    return '''<div class=" w-100" data-role="collapse" data-toggle-element="#COLLAPSE_ID">
            <div class="frame border border-size-1 pt-2 bd-black">
                <div class="p-2 d-inline">{0}</div>  
                <a href="{2}" class="h5 fg-green bg-white d-inline">{1}</a>
                <div class="content">
                        <p class="p-2">{3}</p>
                </div>
            </div>
        </div>'''.format(articleObject.publishedAt, articleObject.header, articleObject.href, articleObject.subject)


def decide_include_article(publishTime):
    if (publishTime == ''):
        return True         # could not find publishedTime in HTML, so include it in results
    # minimalAllowedDateAsStr was already calculated in main()
    publishedDateAsStr = str(parser.parse(publishTime).date())
    logger.info("publishedDateAsStr=%s minimalAllowedDateAsStr=%s", publishedDateAsStr, minimalAllowedDateAsStr)
    return (publishedDateAsStr >= minimalAllowedDateAsStr)


def do_with_article(articleObject):
    try:
        today = date.today()  # str(date.today()) returnes '2020-03-27'
        #url = 'https://www.haaretz.co.il/amp/' + id
        #articleObject = readAndProcess(id, url)
        #so_far = so_far + 1
        #logger.info("completed %d out of %d", so_far, numberOfIds)
        if articleObject.fullHtml == '':
            return 0
        file_relative_path, file_full_path = saveToFile(articleObject.id, articleObject.fullHtml)
        time = articleObject.updatedAt
        if (time == ''):
            time = articleObject.publishedAt
        articleObject.link = '<p>[' + \
                             articleObject.subject + \
                             '/' + articleObject.sub_subject + \
                             ']<b>' + articleObject.publishedAt + \
                             '</b><a href="' + file_relative_path + \
                             '">' + str(articleObject.header) + '</a></p>'
        articleObject.link = create_link(articleObject)
        #body = body + articleObject.link
        logger.debug("[%s] published at %s, updated at: %s", articleObject.id, articleObject.publishedAt, articleObject.updatedAt)

        if decide_include_article(articleObject.publishedAt):
            key = generate_key(articleObject)
            add_article(key, articleObject)      #articles[key] = articleObject
            return 1
        else:
            logger.info("[%s] %s not added to index, subject=%s", articleObject.id, articleObject.publishedAt[:10], articleObject.subject + articleObject.sub_subject)

    except:
        logger.error("some exception with id %s", id)
    return 0


articles = {}
def add_article(key, article):
    articles[key] = article
    date = article.publishedAt[:10]
    logger.info("[%s] %s added to index of today with key %s", article.id, date, key)




def when_all_articles_added():
    logger.info('generating index for %d articles...', len(articles))
    html = generate_index(articles)
    logger.info("...done. writing to file...")
    f = open(base_dir + 'index.html', "w")
    f.write(html)
    f.close()
    logger.info("...done.")


def generate_key(articleObject):
    return articleObject.subject + articleObject.publishedAt + articleObject.id
           # articleObject.sub_subject + \


@tenacity.retry(wait=tenacity.wait_fixed(1))
def first_page(limit):
    url = 'https://www.haaretz.co.il'
    logger.debug("loading first page %s...", url)
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    logger.debug("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    list_of_articles = bs.html.findAll(
        lambda tag: tag.name == "article" and "id" in tag.attrs['class'])
    links = {"1"}
    for article in list_of_articles:
        if (limit <= 0):
            break
        hrefs = article.find_all("a")
        for href in hrefs:
            link = href.attrs["href"]
            links.add(link)
            if (is_link(link)):
                limit = limit - 1
                if (limit <= 0):
                    break
    links.remove("1")
    #print("links:")
    ids = []
    for link in links:
        #print(link)
        if is_link(link):
            start = start_link(link)
            id = link[start:]
            ids.append(id)
    for id in ids:
        logger.debug(id)
    return ids

def is_link(link):
    return (link.find("1.8") >= 0)

def start_link(link):
    return link.find("1.8")

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

@tenacity.retry(wait=tenacity.wait_fixed(1),
                stop=tenacity.stop_after_delay(30))
def process_page(url, limit):
    logger.info("loading url %s...", url)
    try:
        user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        request = Request(url, headers={'User-Agent': user_agent})
        response = urlopen(request)
        html = response.read()
    except:
        logger.error("some exception when trying to retrieve URL %s", url)
        return []
    logger.debug("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    list_of_articles = bs.html.find_all(
        lambda tag: (tag.name == "a") and
                    ('href' in tag.attrs.keys()) and
                    (is_link(tag.attrs['href'])), recursive=True)
    links = {"1"}
    for href in list_of_articles:
        link = href.attrs["href"]
        if is_link(link):
            links.add(link)
            limit = limit - 1
            if (limit <= 0):
                break
    links.remove("1")
    #print("links:")
    ids = []
    for link in links:
        #print(link)
        if is_link(link):
            start = start_link(link)
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
    return [
        'https://www.haaretz.co.il/magazine'
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


def remove_same(article_ids, more_article_ids):
    for id in more_article_ids:
        if (id in article_ids):
            more_article_ids.remove(id)
    return more_article_ids

if __name__ == "__main__":
    logger.debug("starting queue 1")
    minimalAllowedDateAsStr = str(date.today() - timedelta(days=DELTA)) # change value of global scope variables defined at beginning of file
    #defined in globalscope: ids_queue = start_queue_with_workers(NUMBER_OF_Q1_WORKERS, lambda x: DownloadWorker(x))
    article_ids = first_page(LIMIT)
    send_urls_to_queue(ids_queue, article_ids)
    for url in urls():
        if (len(article_ids) > LIMIT):
            break
        more_article_ids = process_page(url, LIMIT - len(article_ids))
        more_article_ids = remove_same(article_ids, more_article_ids)
        logger.debug("after removing duplicates, url %s has %d ids", url, len(more_article_ids))
        logger.debug("now sending %d articles", len(more_article_ids))
        send_urls_to_queue(ids_queue, more_article_ids)

        #updating list of all IDs
        article_ids.extend(more_article_ids)
        article_ids = remove_duplicates(article_ids)

    logger.debug("all %d articles were sent",len(article_ids))

    time1.sleep(10)
    ids_queue.join()
    logger.debug("ids queue joined")

    articles_queue.join()   # this will wait for queue2 completing?
    logger.debug("articles queue joined")
    when_all_articles_added()
