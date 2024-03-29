'''

This project demonstrates web scraping of Haaretz site,
generating an index of all articles of today.

This version of the script uses 2 queues in order to split the work
and thus increase performance by
1. execute the retrieval from WEB in several concurrent threads
2. separate retrieval from the processing

run as a docker container:
docker build -t pythonroadmap/scraping:v01 .
docker run -p 5001:5000 -v /home/evyatar/GitHub/github-pages-hello-world/haaretz/:/out/ --rm --name scraping pythonroadmap/scraping:v01


'''
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from datetime import date,timedelta
import glob
import logging
from time import time, sleep
from dateutil import parser
from queue import Queue
from threading import Thread
import tenacity
from utils import remove_duplicates
import os
import subprocess
import json

'''
 static variables:
'''
DEBUG_LEVEL=logging.DEBUG
DELTA = 3   # in days. if article date is less than DELTA days ago, it will be added to index
LIMIT = 5000
SLEEP=10
# if os.environ.get('LIMIT_ARTICLES'):
#     LIMIT = int(os.environ.get('LIMIT_ARTICLES'))

# increasing number of download threads above 30 does not increase throughput.
# increasing number of processing threads above 80 does not increase throughput.
NUMBER_OF_Q1_WORKERS=5 #30      # number of threads that download from a URL
NUMBER_OF_Q2_WORKERS=5 #80      # number of threads that process an article
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

HTML_END = '''
    <script src="https://cdn.metroui.org.ua/v4/js/metro.min.js"></script>
    <script>

        function setDisplay(element, val) {
            if (element.style) {
                element.style.display = val;
            }
        }

        function toggleAllSiblingChildren(buttons, element, key) {
            const children = element.nextElementSibling.children;
            const size = children.length;
            for (index = 0 ; index < size; index++) {
                if (buttons[key] == true) {                    
                    setDisplay(children[index], "none");
                }
                else {
                    setDisplay(children[index], "block");
                }
            }
        }

        function initButtonsArray(numberOfButtons) {
            let b = {};
            for (index = 1 ; index <= numberOfButtons; index ++) {
                b['collapse_toggle_'+index] = false;
            }
            return b;
        }

        const numberOfButtons = document.getElementsByTagName("button").length;
        if (!sessionStorage.getItem("buttons")) {
            sessionStorage.setItem("buttons",JSON.stringify(initButtonsArray(numberOfButtons)));
        }

        const buttons = JSON.parse(sessionStorage.getItem("buttons"));
        keys = Object.keys(buttons);
        keys.forEach(key => {
            const element = document.getElementById(key);
            element.onclick = () => {
                buttons[key] = !buttons[key];
                sessionStorage.setItem("buttons",JSON.stringify(buttons));
            }
            toggleAllSiblingChildren(buttons, element, key);
        });
    </script>
    </body>
</html>'''

logging.basicConfig(filename='1.log',level=DEBUG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#filename='1.log',
logger = logging.getLogger(__name__)
logger.debug('====================> started!')
logger.debug ('/home/evyatar/work/python/Github/GitHub/PythonRoadmap/python-roadmap/python/bs.py')
# base_dir - assuming that the script is run in a docker container.
# when running on local machine - define BASE_DIR as a real dir on the machine (like /home/evyatar/out/)
# this dir is mapped to a directory on the host (for example '/home/evyatar/GitHub/github-pages-hello-world/haaretz/')
base_dir = os.environ.get('BASE_DIR')
if not base_dir:
    base_dir = '/out/'
    logger.warning('BASE_DIR not defined, using default %s', base_dir)
if (not base_dir.endswith("/") ):
    base_dir = base_dir + "/"
logger.info('using base_dir=%s', base_dir)

minimalAllowedDateAsStr = str(date.today())
user_agent = 'Mozilla/5.0 (compatible; adidxbot/2.0;  http://www.bing.com/bingbot.htm)'
#user_agent='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36'
#user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

count_articles_added = 0


'''
A Queue of activities, each activity is executed by one of the worker threads from the thread pool.
The pool size is defined when initializing the queue.
The activity takes an item from the queue and execute it.
'''
def start_queue_with_workers(number_of_workers, f):
    queue = Queue()
    # Create worker threads
    for x in range(number_of_workers):
        worker = f(queue)        #f could be DownloadWorker() or ArticleWorker
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    return queue
#
#                    | articles dictionary  | ---> generates the index.html document and saves it to file
#                    +----------------------+
# ====='''
#
#
def fix_article_id(article_id):
#     """
#     article_id should be like 00000182-e081-dc3e-abf7-e09ded090000
#     but sometimes it is like /gallery/television/tv-review/2022-09-05/ty-article/.premium/00000183-09fe-dd6f-abdb-7fff8d7d0000
#     :param article_id:
#     :return:
#     """
    fixed_id = article_id
    index = article_id.find("0000018")
    if index >= 0:
        fixed_id = article_id[index:]
    #print("article id=", article_id, ", fixed=", fixed_id)
    return fixed_id
#
#
class ArticleWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        try:
            while True:
                article_id = ""
                try:
                    #Get the work from the queue and expand the tuple
                    article = self.queue.get()
                    article_id = str(article.id)
                    article_id = fix_article_id(article_id)
                    article.id = article_id
                    logger.debug('ArticlesQueue: get article ' + article.id + ' from queue')
                    if not article.fullHtml:
                        logger.debug('===> article fullHtml already empty at this stage')

                    result = do_with_article(article)
                    logger.debug('ArticlesQueue: article ' + article.id + ' processing completed with result ' + str(result))
                finally:
                    self.queue.task_done()
                    logger.debug('ArticlesQueue: task done (' + article.id + ')')
        finally:
            pass
#
# '''=========================================
# ====='''
class DownloadWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        try:
             while True:
                #Get the work from the queue and expand the tuple
                id = '0'
                try:
                    id, url = self.queue.get()
                    logger.debug('DownloadQueue: get item ' + id + ' from queue')
                    article = readAndProcess(id, url)
                    logger.debug('DownloadQueue: item ' + id + ' readAndProcess completed')
                    if article.fullHtml:
                        logger.debug('fullHtml has length ' + str(len(article.fullHtml)))
                #        continue to articles queue only if html not empty
                        send_article_to_queue(article)
                        logger.debug('DownloadQueue: item ' + id + ' send_article_to_queue completed')
                    else:
                        logger.warning('===> already empty fullHTML for id ' + id)
                        send_article_to_queue(article)
                        logger.debug('DownloadQueue: item ' + id + ' send_article_to_queue completed')
                except:
                    logger.debug("unknown exception 4 in DownloadWorker for id " + id)
                    pass
                finally:
                    self.queue.task_done()
                    logger.debug('DownloadQueue: item ' + id + ' task done')
        finally:
            logger.debug("unknown exception 5 in DownloadWorker outside loop")
            pass

'''=========================================
====='''

articles_queue = start_queue_with_workers(NUMBER_OF_Q2_WORKERS, lambda x: ArticleWorker(x))
ids_queue = start_queue_with_workers(NUMBER_OF_Q1_WORKERS, lambda x: DownloadWorker(x))


'''=========================================
====='''

def send_article_to_queue(article):
    articles_queue.put(article)


class Article:
    def __init__(self, id, header, publishedAt, updatedAt, fullHtml, subject, sub_subject, author):
        self.id = id
        self.header = header
        self.publishedAt = publishedAt
        self.updatedAt = updatedAt
        self.fullHtml = fullHtml
        self.subject = subject
        self.sub_subject = sub_subject
        self.href = ''
        self.author = author

    # other fields: subject


def construct_html(body, existing_body):
    return HTML_START + body + existing_body + HTML_END


def omit(tag):
    omitted = BeautifulSoup("<div>omitted " + tag + "</div>", "html.parser")
    return omitted

def load_html(request):
    response = urlopen(request)
    html = response.read()
    # convert from bytes to String:
    htmlText = html.decode(encoding='UTF-8')
    return htmlText


def fast_find_times(bs):
    try:
        publishedAt = bs.head.find(name='meta', attrs={"property": "og:pubdate"}).attrs['content']
        return publishedAt
    except:
        return ''

def find_alternative_authors(bs):
    author = ''
    try:
        contents = bs.head.find(name='script', attrs={"type": "application/ld+json"}).contents[0]
        asJson = json.loads(contents)
        if "author" in asJson.keys():
            authors = asJson["author"]
            logger.debug("=== %s ===", authors)
            author0 = authors[0]
            author_name = author0["name"]
            logger.debug("=== %s ===", author_name)
            author = author_name
    except:
        pass
    return author


def find_author(bs):
    logger.debug("starting find_author.")
    author = ''
    try:
        author = bs.head.find(name='meta', attrs={"name": "author"}).attrs['content']
    except:
        pass
    logger.debug("find_author completed, author=%s", author)
    return author


def find_times(bs):
    publishedAt = ""
    updatedAt = ""
    author = "++"
    try:
        #logger.debug("1")
        elements = bs.find_all('time')
        if (elements is not None) and (len(elements) > 0):
            publishedAt = elements[0]['datetime']
            updatedAt = elements[1]['datetime']
        else:
            published = bs.head.find(name='meta', attrs={"property": "article:published"})
            if (published is not None):
                #logger.debug("1.1")
                publishedAt = bs.head.find(name='meta', attrs={"property": "article:published"}).attrs['content']
            if bs.head.find(name='meta', attrs={"property": "article:modified"}) is not None:
                #logger.debug("1.2")
                updatedAt = bs.head.find(name='meta', attrs={"property": "article:modified"}).attrs['content']
    except:
        pass
    if (publishedAt=='' and updatedAt==''):
        try:
            publishedAt = bs.head.find(name='meta', attrs={"property": "og:pubdate"}).attrs['content']
            #logger.debug("1.3")
            updatedAt = bs.html.find(lambda tag: tag.name == "time" and "datetime" in tag.attrs.keys()).attrs['datetime']
            #publishedAt = updatedAt
        except:
            pass
    if (publishedAt == ''):
        publishedAt = todayAsStr()  #'2020-03-25T00:01:00+0200'
    if (updatedAt == ''):
        updatedAt = todayAsStr() # '2020-03-25T00:01:00+0200'
    #author = find_author(bs)
    author = find_alternative_authors(bs)
    return publishedAt, updatedAt, author


def remove_parts_of_article(section, parts):
    for part in parts:
        #logger.debug("2")
        while section.find(class_=part) is not None:
            section.find(class_=part).replace_with(omit(part))


def readAndProcess(id, url):
    ts = time()
    logger.debug("[%s] loading %s...", id, url)
    
    request = Request(url, headers={'User-Agent': user_agent})

    ##
    #
    html = load_html(request)
    #
    ##
    logger.debug('[%s] loading completed in %s seconds', id, time() - ts)
    if html:
        logger.debug(' html of article ' + id + ' has length ' + str(len(html)))
    else:
        logger.warning('!!!!!==> empty html for article ' + id)

    ts = time()
    logger.debug("[%s] souping...", id)
    bs = BeautifulSoup(html, 'html.parser')
    if (bs.article is None):
        logger.debug('bs.article is NONE for id ' + id)
        return Article(id, HEADER_OF_UNKNOWN, '', '', '', '', '', '')
    else:
        logger.debug('Surprise!!! article ' + id)

    # first find publish time, if too old, we don't need to continue parsing
    if not decide_include_article(fast_find_times(bs)):
        logger.debug("stopped processing this article - too old")
        return Article(id, HEADER_OF_UNKNOWN, '', '', '', '', '', '')

    try:
        header = bs.article.header.h1.contents[-1]
    except:
        header = HEADER_OF_UNKNOWN

    logger.debug('[%s] souping completed in %s seconds, header=%s', id, time() - ts, header)
    ts = time()
    logger.debug("[%s] processing...", id)
    #sections = bs.article.findAll(name='section', class_='b-entry')
    sections = bs.findAll(name='div', attrs={'data-test': 'articleBody'})

    if (sections is None) or len(sections) == 0:
        logger.debug("bs.article.findAll(name='section', class_='b-entry') produced 0 results for id " + id)
        return Article(id, header, '', '', '', '', '', '')
    else:
        logger.debug("[%s] bs.article.findAll(name='section', class_='b-entry') produced " + str(len(sections)), id)
    first = sections[0]

    logger.debug("[%s] before find_times", id)
    publishedAt, updatedAt, author = find_times(bs)
    logger.debug("[%s] after find_times. publishedAt=%s, updatedAt=%s, author=%s", id, publishedAt, updatedAt, author)

    # header_crumbs_root = bs.article.find(name='ol', class_='c-article-header__crumbs')
    # header_crumbs = header_crumbs_root.find_all('li', class_='c-article-header__crumb')
    # subject = ''
    # sub_subject = ''
    # if len(header_crumbs) > 0:
    #     subject = header_crumbs[0].text.rstrip().lstrip()
    # if len(header_crumbs) > 1:
    #     sub_subject = header_crumbs[1].text.rstrip().lstrip()

    article = bs.find(name='main', id='pageRoot').article
    subject = '1'
    sub_subject = '2'
    if len(article.findAll('nav')) > 0:
        subs = article.findAll('nav')[0].findAll('a')
        if len(subs) > 0:
            subject = subs[0].text.rstrip().lstrip()
            if len(subs) > 1:
                sub_subject = subs[1].text.rstrip().lstrip()

    logger.debug("[%s] after header_crumbs. subject=%s, sub_subject=%s", id, subject, sub_subject)

## remove()
    try:
        remove_parts_of_article(first, ['c-quick-nl-reg', 'c-related-article-text-only-wrapper', 'c-dfp-ad'])
        # logger.debug("2")
        # if first.find(class_='c-quick-nl-reg') is not None:
        #     first.find(class_='c-quick-nl-reg').replace_with(omit('c-quick-nl-reg'))
        # logger.debug("3")
        # if first.find(class_='c-related-article-text-only-wrapper') is not None:
        #     first.find(class_='c-related-article-text-only-wrapper').replace_with(omit('c-related-article-text-only-wrapper'))
        #logger.debug("4")
        all_figures = first.find_all(name='figure')
        # while (len(all_figures) > 0):
        #     first.find(name='figure').replace_with(omit('figure'))
        #     all_figures = first.find_all(name='figure')
        while (first.find(name='figure') is not None):
            first.find(name='figure').replace_with(omit('figure'))

        # logger.debug("5")
        # while (first.find(class_="c-dfp-ad") is not None):
        #     first.find(class_="c-dfp-ad").replace_with(omit("c-dfp-ad"))

        #logger.debug("6")
        #bs.html.find(name='div',attrs={"hidden":""}).replace_with(omit('hidden'))
        #bs.html.find(attrs={"id":"amp-web-push"}).replace_with(omit('amp-web-push'))
        #bs.html.find(name='section',attrs={"amp-access":"TRUE"}).replace_with(omit('amp-access'))
        # logger.debug("7")
        # bs.html.find(name='amp-sidebar').replace_with(omit('amp-sidebar'))
        #remove_parts_of_article(bs.html, ['amp-sidebar'])
        #while (bs.html.find(name='div', attrs={"class":"delayHeight"}) is not None):
        #    bs.html.find(name='div', attrs={"class": "delayHeight"}).replace_with(omit("delayHeight"))

    # convert every <section amp-access="NOT ampConf.activation OR currentViews &lt; ampConf.maxViews OR subscriber">
    # to     <section amp-access="TRUE">
        #logger.debug("8")
        list_of_sections = bs.html.findAll(
            lambda tag: tag.name == "section" and "amp-access" in tag.attrs.keys() and tag.attrs['amp-access'] != "TRUE")
        for section in list_of_sections:
            #logger.debug(".", end='') # causes exception (why?)
            section.attrs['amp-access'] = "TRUE"

        #logger.debug("9")
        bs.html.body.attrs['style'] = "border:2px solid"
        # assuming that 3rd child of <head> is not needed and can be changed...
        bs.html.head.contents[3].attrs={"name":"viewport","content":"width=device-width, initial-scale=1"}
        htmlText=bs.html.prettify()
        if not htmlText:
            logger.warning('!!!!!!!==> empty HTML for article ' + id)
            logger.debug('[%s] processing completed in %s seconds.')
        else:
            logger.debug('[%s] processing completed successfully in %s seconds. html=%s', id, time() - ts, htmlText[:50])
    except:
        print("readAndProcess: absorbing unknown exception 2 when removing parts of article")
        pass
    finally:
        pass

    #logger.debug("!")
    return Article(id, header, publishedAt, updatedAt, html, subject, sub_subject, author)


# def remove():
#     remove_parts_of_article(first, ['c-quick-nl-reg', 'c-related-article-text-only-wrapper', 'c-dfp-ad'])
#     # logger.debug("2")
#     # if first.find(class_='c-quick-nl-reg') is not None:
#     #     first.find(class_='c-quick-nl-reg').replace_with(omit('c-quick-nl-reg'))
#     # logger.debug("3")
#     # if first.find(class_='c-related-article-text-only-wrapper') is not None:
#     #     first.find(class_='c-related-article-text-only-wrapper').replace_with(omit('c-related-article-text-only-wrapper'))
#     # logger.debug("4")
#     all_figures = first.find_all(name='figure')
#     # while (len(all_figures) > 0):
#     #     first.find(name='figure').replace_with(omit('figure'))
#     #     all_figures = first.find_all(name='figure')
#     while (first.find(name='figure') is not None):
#         first.find(name='figure').replace_with(omit('figure'))
#
#     # logger.debug("5")
#     # while (first.find(class_="c-dfp-ad") is not None):
#     #     first.find(class_="c-dfp-ad").replace_with(omit("c-dfp-ad"))
#
#     # logger.debug("6")
#     bs.html.find(name='div', attrs={"hidden": ""}).replace_with(omit('hidden'))
#     bs.html.find(attrs={"id": "amp-web-push"}).replace_with(omit('amp-web-push'))
#     # bs.html.find(name='section',attrs={"amp-access":"TRUE"}).replace_with(omit('amp-access'))
#     # logger.debug("7")
#     # bs.html.find(name='amp-sidebar').replace_with(omit('amp-sidebar'))
#     remove_parts_of_article(bs.html, ['amp-sidebar'])
#     while (bs.html.find(name='div', attrs={"class": "delayHeight"}) is not None):
#         bs.html.find(name='div', attrs={"class": "delayHeight"}).replace_with(omit("delayHeight"))
#
#     # convert every <section amp-access="NOT ampConf.activation OR currentViews &lt; ampConf.maxViews OR subscriber">
#     # to     <section amp-access="TRUE">
#     # logger.debug("8")
#     list_of_sections = bs.html.findAll(
#         lambda tag: tag.name == "section" and "amp-access" in tag.attrs.keys() and tag.attrs['amp-access'] != "TRUE")
#     for section in list_of_sections:
#         logger.debug(".", end='')
#         section.attrs['amp-access'] = "TRUE"
#
#     # logger.debug("9")
#     bs.html.body.attrs['style'] = "border:2px solid"
#     # assuming that 3rd child of <head> is not needed and can be changed...
#     bs.html.head.contents[3].attrs = {"name": "viewport", "content": "width=device-width, initial-scale=1"}
#     htmlText = bs.html.prettify()
#     if not htmlText:
#         logger.warning('!!!!!!!==> empty HTML for article ' + id)
#         logger.debug('[%s] processing completed in %s seconds.')
#     else:
#         logger.debug('[%s] processing completed successfully in %s seconds. html=%s', id, time() - ts, htmlText[:50])
#     return htmlText


def todayAsStr():
    return str(date.today())



article_ids = []

#urls = [ 'https://www.haaretz.co.il/amp/1.8600567',


def decide_year_month():
    month = str(date.today())[5:7]
    year = str(date.today())[0:4]
    return year + "_" + month    


def decide_file_location(directory):
    if not directory:
        # directory is empty string
        directory = "archive/" + decide_year_month() + "/"
    return base_dir + directory

def saveToFile(id, htmlText):
    try:
        #print("saveToFile: id=", id)
        # index_file_name='index_20200615', directory='archive/2020_06/'
        name = "h" + id + ".html"
        dir = decide_file_location('')
        #logger.debug("trying to create dir if not exist: %s", dir)
        os.makedirs(dir, exist_ok=True)
        #logger.debug("created")
        fileName = dir + name
        #logger.debug("trying to save file, id [%s] file: %s", id, fileName)
        f = open(fileName, "w")
        #htmlAsString = htmlText.decode(encoding='UTF-8')
        f.write(htmlText)
        f.close()
        #logger.debug("saved")
        #logger.debug("[%s] file: %s", id, fileName)
        return name, fileName
    except Exception as inst:
        logger.error("saveToFile: some exception with id %s: %s", id, inst)
        return '',''

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
    if (len(articles_with_subject_not_in_list) > 0):
        subjects_not_in_list = [x.subject for x in articles_with_subject_not_in_list]
        logger.warning("unknown subjects: %s", str(subjects_not_in_list).strip('[]'))

    return sorted, existing_subjects

def generate_index(articles):
    if articles:
        logger.debug('generate_index started, ' + str(len(articles)) + ' articles')
    else:
        logger.warning("!!!!!!!!!!!!!!!!!!!===>   no articles will be inserted to index!!")
    body = ''
    sortedBySubject, existing_subjects = sort_by_subject(articles)
    if existing_subjects:
        logger.debug('sorted, ' + str(len(existing_subjects)) + ' existing subjects')

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
        , 'משפחה'
        , 'הארץ'
        , 'סביבה ובעלי חיים'
        , 'טיולים'
        , 'הזירה - الساحة'
        # , ''
        # , ''
    ]
    for i in range(0, len(list)):
        priorities[list[i]] = i
    return priorities


def extract_id(link):
    idd = link
    if '00182' in link:
        idd = link.split("/")[-1]
    return idd


def send_url_to_queue(ids_queue, link):
    url = 'https://www.haaretz.co.il/amp' + link
    idd = extract_id(link)
    logger.debug("[%s] inserting id %s in ids queue", link, idd)
    ids_queue.put((idd, url))  # will cause calling readAndProcess(id, url)


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
                        <p class="p-2">{4}</p>
                </div>
            </div>
        </div>'''.format(articleObject.publishedAt, articleObject.header, articleObject.href, articleObject.subject, articleObject.author)


def decide_include_article(publishTime):
    try:
        logger.debug("decide_include_article started   " + str(publishTime))
        if (publishTime == ''):
            return True         # could not find publishedTime in HTML, so include it in results
        publishedDateAsStr = ''
        if ('IST' in publishTime):
            #print("publishTime=" + publishTime)
            publishedDateAsStr = publishTime.split('IST', 2)[0]
            #print("publishedDateAsStr=" + publishedDateAsStr)
        else:
            publishedDateAsStr = str(parser.parse(publishTime).date())
        # minimalAllowedDateAsStr was already calculated in main()
        logger.debug("publishedDateAsStr=%s minimalAllowedDateAsStr=%s", publishedDateAsStr, minimalAllowedDateAsStr)
        decide = (publishedDateAsStr >= minimalAllowedDateAsStr)
        logger.debug(" decide=" + str(decide))
        return decide
    except:
        print("decide_include_article: absorbing unknown exception 3, publishTime=" + publishTime)
        return True


def print_if_count(number_of_articles):
    if number_of_articles%10==0:
        print("", str(number_of_articles), "articles added to index")


def do_with_article(articleObject):
    global count_articles_added
    try:
        today = date.today()  # str(date.today()) returnes '2020-03-27'
        #url = 'https://www.haaretz.co.il/amp/' + id
        #articleObject = readAndProcess(id, url)
        #so_far = so_far + 1
        #logger.info("completed %d out of %d", so_far, numberOfIds)
        if articleObject.fullHtml == '':
            logger.debug('==================>  empty full HTML for article ' + articleObject.id)
            return 0
        logger.debug('do_with_article: html not empty for article ' + articleObject.id +
                     ' with header=' + str(articleObject.header) +
                     ', updatedAt=' + str(articleObject.updatedAt) +
                     ', publishedAt=' + str(articleObject.publishedAt) +
                     ', subject=' + str(articleObject.subject) +
                     ', sub_subject=' + str(articleObject.sub_subject) +
                    ', author=' + str(articleObject.author))

        file_relative_path, file_full_path = saveToFile(articleObject.id, articleObject.fullHtml)
        time = articleObject.updatedAt
        if (time == ''):
            time = articleObject.publishedAt
        articleObject.link = '<p>[' + \
                             articleObject.subject + \
                             '/' + articleObject.sub_subject + \
                             ']<b>' + articleObject.publishedAt + \
                             '</b><a href="' + file_relative_path + \
                             '">' + str(articleObject.header) + '[' + str(articleObject.author) + ']' + '</a></p>'
        logger.debug('do_with_article: article ' + articleObject.id +
                     ' the link is: ' + articleObject.link)
        articleObject.link = create_link(articleObject)
        logger.debug('do_with_article: article ' + articleObject.id +
                     ' the revised link is: ' + articleObject.link)
        #body = body + articleObject.link
        logger.debug("[%s] published at %s, updated at: %s", articleObject.id, str(articleObject.publishedAt), str(articleObject.updatedAt))

        if decide_include_article(articleObject.publishedAt):
            key = generate_key(articleObject)
            add_article(key, articleObject)      #articles[key] = articleObject
            logger.debug("[%s] article %s added", articleObject.id, key)
            count_articles_added = count_articles_added + 1
            print_if_count(count_articles_added)
            return 1
        else:
            logger.info("[%s] %s not added to index, subject=%s", articleObject.id, articleObject.publishedAt[:10], articleObject.subject + articleObject.sub_subject)

    except Exception as inst:
        #print(type(inst))  # the exception instance
        #print(inst.args)  # arguments stored in .args
        #print(inst)
        #logger.error("Unexpected error: %s", inst)  # + sys.exc_info()[0])
        logger.error("do_with_article: some exception with id %s: %s", articleObject.id, inst)
    return 0


articles = {}
def add_article(key, article):
    articles[key] = article
    date = article.publishedAt[:10]
    logger.debug("[%s] %s added to index of today with key %s", article.id, date, key)



#
# <div id="begin_index_links"></div>
#             <div><a href="archive/2020_06/index_20200615.html">2020-06-15</a></div>
#
def create_index_file(index_file_name, directory):
    logger.info('generating index for %d articles...', len(articles))
    print('generating index for', len(articles), 'articles...')
    html = generate_index(articles)
    logger.info("...done. writing to file...")
    dir = decide_file_location(directory)
    full_index_file_name = dir + index_file_name + '.html'
    if os.path.exists(full_index_file_name) and os.path.isfile(full_index_file_name):
        logger.warning('file %s already exists, it will be overwritten!!', full_index_file_name)
    logger.info('to file ' + full_index_file_name)
    f = open(full_index_file_name, "w")
    f.write(html)
    f.close()
    logger.info("...done.")
    print('index file written to', full_index_file_name)


def generate_key(articleObject):
    return articleObject.subject + articleObject.publishedAt + articleObject.id
           # articleObject.sub_subject + \




def is_link(link):
    #return ((link.find("1.8") >= 0) or (link.find("1.9") >= 0) or (link.find("1.10") >= 0))
    return (link.find("00181") >= 0) or (link.find("00182") >= 0) or (link.find("00183") >= 0)

def start_link(link):
    index = link.find("1.8")
    if index >= 0:
        return index
    index = link.find("1.9")
    if index >= 0:
        return index
    index = link.find("1.10")
    if index >= 0:
        return index
    else:
        return link.find("1.")

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


def fix_link(orig_link):
    """
    link should be like /news/elections/2022-08-24/ty-article/00000182-d09b-d765-adf3-db9b3d0a0000
    but sometimes link is https://www.themarker.com/dynamo/2022-08-01/ty-article-magazine/.premium/00000182-393f-dfe2-abab-797ff6720000
    and then we want it to be /dynamo/2022-08-01/ty-article-magazine/.premium/00000182-393f-dfe2-abab-797ff6720000
    :param orig_link:
    :return:
    """
    #print("fix_link", orig_link)
    result = orig_link
    possible_prefixes = ["https://www.themarker.com", 'https://www.haaretz.com', 'https://www.haaretz.co.il']
    for prefix in possible_prefixes:
        index = orig_link.find(prefix)
        if index == 0:
            link = orig_link[len(prefix):]
            result = link
            break
    #print("fix_link", orig_link, " ==> result=", result)
    return result


@tenacity.retry(wait=tenacity.wait_fixed(1),
                stop=tenacity.stop_after_delay(30))
def process_page(url, limit):
    logger.info("process_page - loading url %s...", url)
    try:
        # for some reason, using user_agent as header causes exception in urlopen???
        #user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        request = Request(url, headers={'User-Agent': user_agent})
        #request = Request(url)
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
    #links = {"1"}
    links = []
    for href in list_of_articles:
        logger.debug("considering url %s", str(href))
        link = href.attrs["href"]
        link = fix_link(link)
        if is_link(link):
            #links.add(link)
            links.append(link)
            limit = limit - 1
            if (limit <= 0):
                logger.error("reached limit in process_page()")
                break
    #links.remove("1")
    #print("links:")
    ids = []
    for link in links:
        #print(link)
        if is_link(link):
            # from July 2022: link is like '/magazine/panim/ty-article-face/.premium/00000182-38ee-ddb5-ad8e-fbeffee80000'
            ids.append(link)
            # start = start_link(link)
            # id = link[start:]
            # ids.append(id)
    for id in ids:
        logger.debug(id)
    print("processed", len(ids), "articles")
    return ids


# def remove_duplicates(article_ids):
#     set = {'0'}
#     for id in article_ids:
#         newId = id
#         if ('#' in id):
#             newId = id[:id.find('#')]
#         if ('?' in id):
#             newId = id[:id.find('?')]
#         set.add(newId)
#         if ('?' in newId):
#             logger.warn("url %s still contains ?, original was %s", newId, id)
#     set.remove('0')
#     return list(set)

'''
A static list of URLs that are semi-index pages inside the site,
so they are a good starting point to collect links to articles
'''
def urls():
    return [
          'https://www.haaretz.co.il'
    ,'https://www.haaretz.co.il/magazine'
    ,'https://www.haaretz.co.il/news'
   , 'https://www.themarker.com/allnews'
   , 'https://www.themarker.com/wallstreet'
   , 'https://www.themarker.com/misc/all-headlines'
, 'https://www.themarker.com/realestate'
, 'https://www.themarker.com/technation'
, 'https://www.themarker.com/magazine'
        , 'https://www.themarker.com/news/education'
        , 'https://www.themarker.com/opinion'
        , 'https://www.themarker.com/markets'
        , 'https://www.themarker.com/markets/yourmoney'
        , 'https://www.themarker.com/blogs'
        , 'https://www.themarker.com/consumer'
        , 'https://www.themarker.com/career'
        , 'https://www.themarker.com/dynamo'
        , 'https://www.themarker.com/dynamo/cars'
        , 'https://www.themarker.com/consumer'
        ,'https://www.haaretz.co.il/sport'
,'https://www.haaretz.co.il/news/elections'
,'https://www.haaretz.co.il/news/world'
,'https://www.haaretz.co.il/news/politics'
,'https://www.haaretz.co.il/news/law'
,'https://www.haaretz.co.il/news/health'
,'https://www.haaretz.co.il/news/local'
        ,'https://www.themarker.com/news/education'
,'https://www.haaretz.co.il/gallery'
,'https://www.haaretz.co.il/gallery/television'
, 'https://www.haaretz.co.il/gallery/architecture'
, 'https://www.haaretz.co.il/gallery/fashion'
, 'https://www.haaretz.co.il/gallery/art'
, 'https://www.haaretz.co.il/gallery/events'
, 'https://www.haaretz.co.il/gallery/music'
, 'https://www.haaretz.co.il/gallery/cinema'
, 'https://www.haaretz.co.il/gallery/theater'
, 'https://www.haaretz.co.il/gallery/night-life'
,'https://www.haaretz.co.il/opinions'
,'https://www.haaretz.co.il/captain'
, 'https://www.haaretz.co.il/captain/net'
, 'https://www.haaretz.co.il/captain/viral'
, 'https://www.haaretz.co.il/captain/gadget'
, 'https://www.haaretz.co.il/captain/software'
, 'https://www.haaretz.co.il/captain/games'
, 'https://www.haaretz.co.il/science'
, 'https://www.haaretz.co.il/literature'
, 'https://www.haaretz.co.il/blogs'
, 'https://www.haaretz.co.il/nature'
    , 'https://www.haaretz.co.il/travel'
    , 'https://www.haaretz.co.il/misc/all-headlines'

        #'https://www.haaretz.co.il/binge'
       ]


def remove_same(article_ids, more_article_ids):
    for id in more_article_ids:
        if (id in article_ids):
            more_article_ids.remove(id)
    return more_article_ids


def edit_master_index(index_file_name, directory, the_date):
    # index_file_name='index_20200615', directory='archive/2020_06/', the_date='2020-06-15'
    master_index_file = base_dir + 'index.html'
    added_link = directory + index_file_name + ".html"
    if os.path.exists(master_index_file) and os.path.isfile(master_index_file):
        file = open(master_index_file, "r")
        html = file.read()
        bs = BeautifulSoup(html, 'html.parser')
        link_to_today = bs.find(name='a', attrs={"href": added_link})
        if link_to_today:
            # link already exists, no need to create it!!
            logger.warning("link to %s already exists in master index file", added_link)
            file.close()
            return
        #<div        id = "begin_index_links" > < / div >
        div_wrapper = bs.find(name='div', attrs={"id": "begin_index_links"})
        div = bs.new_tag('div')
        a = bs.new_tag('a', href=added_link)    # "archive/2020_06/index_20200615.html")
        div.append(a)
        a.string = the_date
        div_wrapper.insert(0, div)
        content = bs.prettify()
        file.close()
        logger.warning("write original to file: %s .old", master_index_file)
        old = open(master_index_file+'.old', "w")
        old.write(html)
        old.close()
        logger.warning("write HTML to file: \n%s", content)
        file = open(master_index_file, "w")
        file.write(content)
        file.close()
        logger.warning("done!")
    else:
        logger.warning("master index file %s not found!", master_index_file)


def push_to_github(directory, the_date):
    if base_dir == '/out/':
        logger.warning("running inside docker, skip commit and push to GitHub")
        return
    git_repo_password = os.environ.get('GIT_PASSWORD')
    repo_with_credentials = "'https://USER:PASSWORD@github.com/evyatark/news.git'"
    repo_with_credentials = repo_with_credentials.replace('USER', 'evyatark')
    repo_with_credentials = repo_with_credentials.replace('PASSWORD', git_repo_password)

    # directory='archive/2020_06/', the_date='2020-06-15'
    archive_dir = base_dir + directory

# cd ~/work/roadmap/githubPagesNews/news/news/haaretz
# cd archive/2020_06/

    os.chdir(archive_dir)

    #print(subprocess.run("ls index*.html -al", check=True, shell=True))
    logger.info('=============')
    logger.info("performing git status... (archive_dir=" + archive_dir)
    logger.info(subprocess.run("git status", check=True, shell=True))

    logger.info('=============')
    logger.info("performing git add...")
    command = "git add *.html"
    cp = subprocess.run(command, check=True, shell=True)
    logger.info(cp)

    logger.info(subprocess.run("git status", check=True, shell=True))

    command = 'git commit -m"automated commit of ' + the_date + '"'
    try:
        logger.info('=============')
        logger.info("performing git commit...")
        cp = subprocess.run(command, check=True, shell=True)
        logger.info("command=" + command + ", cp=")
        logger.info(cp)
    except subprocess.CalledProcessError as ex:
        # no changes added to commit (use "git add" and/or "git commit -a")
        #print('absorbing: ' + str(ex))
        logger.warning('absorbing: ' + str(ex))

    #return

    os.chdir(base_dir)

    logger.info('=============')
    logger.info("performing git add...")
    command = 'git add index.html'
    cp = subprocess.run(command, check=True, shell=True)
    logger.info(cp)

    try:
        logger.info('=============')
        logger.info("performing git commit...")
        command = 'git commit -m"automated add of ' + the_date + ' to master index"'
        cp = subprocess.run(command, check=True, shell=True)
        logger.info("command=" + command + ", cp=")
        logger.info(cp)
    except subprocess.CalledProcessError as ex:
        # nothing to commit, working tree clean
        logger.info('absorbing: ' + str(ex))

        logger.info('=============')
        logger.info(subprocess.run("git status", check=True, shell=True))


    #git push 'https://evyatark:password@myrepository.biz/file.git'
    logger.info('=============')
    try:
        logger.info("performing git push...")
        command = 'git push ' + repo_with_credentials
        cp = subprocess.run(command, check=True, shell=True)
        ## do NOT print cp, because it prints the password to the git repository
        logger.info('git push. return-code=' + str(cp.returncode))
    except Exception as ex:
        # nothing to commit, working tree clean
        logger.info('absorbing: ' + str(ex))

    return


def main():
    logger.debug("starting queue 1")
    today = date.today()
    global minimalAllowedDateAsStr
    minimalAllowedDateAsStr = str(date.today() - timedelta(days=DELTA)) # change value of global scope variables defined at beginning of file
    # ids_queue is defined in globalscope (queue of NUMBER_OF_Q1_WORKERS DownloadWorkers)
    article_ids = []
    for url in urls():
        try:
            if (len(article_ids) > LIMIT):
                logger.error("number of article_ids " + str(len(article_ids)) + " reached limit " + str(LIMIT) + " in main()")
                break
            more_article_ids = process_page(url, LIMIT - len(article_ids))
            more_article_ids = remove_same(article_ids, more_article_ids)
            logger.debug("after removing duplicates, url %s has %d ids", url, len(more_article_ids))
            logger.debug("now sending %d articles", len(more_article_ids))
            # ids_queue is defined in globalscope (queue of NUMBER_OF_Q1_WORKERS DownloadWorkers)
            send_urls_to_queue(ids_queue, more_article_ids)

            #updating list of all IDs
            article_ids.extend(more_article_ids)
            article_ids = remove_duplicates(article_ids)
        except:
            print("unknown exception 1")
        finally:
            print("for url " + str(url))

    logger.info("all %d articles were sent",len(article_ids))
    print("all", len(article_ids), "articles were sent, sleeping ", str(SLEEP), "minutes...")
    #ids_queue.join()
    #logger.debug("ids queue joined")
    logger.info("sleeping %s minutes...", str(SLEEP))
    sleep(60 * SLEEP)
    logger.info("completed sleeping %s minutes.", str(SLEEP))
    print("completed sleeping")
    #articles_queue.join()   # this will wait for queue2 completing?
    #logger.debug("articles queue joined")
    year = str(today)[0:4]
    month = str(today)[5:7]
    day = str(today)[8:10]
    new_index_file_name = 'index_' + year + month + day
    archive_directory = 'archive/' + year + '_' + month + '/'
    logger.info("create_index_file, archive_directory=" + archive_directory + ", the_date=" + str(today))

    create_index_file(index_file_name=new_index_file_name, directory=archive_directory)     # after all articles have been added to the articles dictionary
    #create_index_file(index_file_name='index_20200615', directory='archive/2020_06/')     # after all articles have been added to the articles dictionary
    logger.info("edit_master_index")
    edit_master_index(index_file_name=new_index_file_name, directory=archive_directory, the_date=str(today))    # change master index
    #push_to_github(directory='archive/2020_06/', the_date='2020-06-16')
    logger.info("pushing to github...           (archive_directory=" + archive_directory + ", the_date=" + str(today) + ")")
    push_to_github(directory=archive_directory, the_date=str(today))
    logger.info("pushing to github completed!")
    print("main completed")


def test1(id):
    articleObj = readAndProcess(id, 'https://www.haaretz.co.il/amp/' + id)
    #assertThat:
    conditions = [True
        ,articleObj.header is not None
        ,articleObj.id == id
        ,articleObj.subject is not None
        ,articleObj.sub_subject is not None
         ]
    counter = 0
    incorrect = 0 ;
    for condition in conditions:
        if not condition:
            incorrect = incorrect + 1
            logger.error("condition %d not correct", counter)
        counter = counter + 1
    if (incorrect > 0):
        logger.error("found %d incorrect conditions", incorrect)
    else:
        logger.info("%s - all is ok", id)
    return counter

def test_ids(ids):
    c=0
    for id in ids:
        c=c + test1(id)
    return c

if __name__ == "__main__":
    main()

