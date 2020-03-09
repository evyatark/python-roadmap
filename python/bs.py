from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from datetime import date
import glob

LIMIT = 500
HTML_START = '<html dir="rtl" lang="he"><head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/></head><body>'
HTML_END = '</body></html>'

def construct_html(body, existing_body):
    return HTML_START + body + existing_body + HTML_END

class Article:
    def __init__(self, id, header, publishedAt, updatedAt, fullHtml):
        self.id = id
        self.header = header
        self.publishedAt = publishedAt
        self.updatedAt = updatedAt
        self.fullHtml = fullHtml

base_dir = '/home/evyatar/GitHub/github-pages-hello-world/haaretz/'

def omit(tag):
    omitted = BeautifulSoup("<div>omitted " + tag + "</div>", "html.parser")
    return omitted


def readAndProcess(id, url):
    print("loading", url, '...')
    html = urlopen(url, )
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    print("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    try:
        header = bs.article.header.h1.contents[-1]
    except:
        header = "@@@"

    #print(header)
    #print(bs.html.prettify)
    # sections = bs.article.findAll(name='section', class_='c-article-entry', attrs='{"class":"b-entry"}')
    sections = bs.article.findAll(name='section', class_='b-entry')
    if len(sections) == 0:
        return Article(id, header, '', '', '')
    first = sections[0]
    publishedAt = ""
    updatedAt = ""
    try:
        published = bs.article.find(name='meta', attrs={"property": "article:published"})
        if (published is not None):
            publishedAt = bs.article.find(name='meta', attrs={"property": "article:published"}).attrs['content']
        if bs.article.find(name='meta', attrs={"property": "article:modified"}) is not None:
            updatedAt = bs.article.find(name='meta', attrs={"property": "article:modified"}).attrs['content']
    except:
        dummy=0
    if (publishedAt=='' and updatedAt==''):
        try:
            updatedAt = bs.html.find(lambda tag: tag.name == "time" and "datetime" in tag.attrs.keys()).attrs['datetime']
            publishedAt = updatedAt
        except:
            dummy = 0

    #sections[0].replace_with(omit('section 0'))
    if first.find(class_='c-quick-nl-reg') is not None:
        first.find(class_='c-quick-nl-reg').replace_with(omit('c-quick-nl-reg'))
    if first.find(class_='c-related-article-text-only-wrapper') is not None:
        first.find(class_='c-related-article-text-only-wrapper').replace_with(omit('c-related-article-text-only-wrapper'))
    all_figures = first.find_all(name='figure')
    while (len(all_figures) > 0):
        first.find(name='figure').replace_with(omit('figure'))
        all_figures = first.find_all(name='figure')

    while (first.find(class_="c-dfp-ad") is not None):
        first.find(class_="c-dfp-ad").replace_with(omit("c-dfp-ad"))

    bs.html.find(name='div',attrs={"hidden":""}).replace_with(omit('hidden'))
    bs.html.find(attrs={"id":"amp-web-push"}).replace_with(omit('amp-web-push'))
    #bs.html.find(name='section',attrs={"amp-access":"TRUE"}).replace_with(omit('amp-access'))
    bs.html.find(name='amp-sidebar').replace_with(omit('amp-sidebar'))
    while (bs.html.find(name='div', attrs={"class":"delayHeight"}) is not None):
        bs.html.find(name='div', attrs={"class": "delayHeight"}).replace_with(omit("delayHeight"))

# convert every <section amp-access="NOT ampConf.activation OR currentViews &lt; ampConf.maxViews OR subscriber">
# to     <section amp-access="TRUE">
    list_of_sections = bs.html.findAll(
        lambda tag: tag.name == "section" and "amp-access" in tag.attrs.keys() and tag.attrs['amp-access'] != "TRUE")
    for section in list_of_sections:
        section.attrs['amp-access'] = "TRUE"

    bs.html.body.attrs['style'] = "border:2px solid"
    # assuming that 3rd child of <head> is not needed and can be changed...
    bs.html.head.contents[3].attrs={"name":"viewport","content":"width=device-width, initial-scale=1"}
    htmlText=bs.html.prettify()
    return Article(id, header, publishedAt, updatedAt, htmlText)






article_ids = []

#urls = [ 'https://www.haaretz.co.il/amp/1.8600567',


def saveToFile(id, counter, htmlText):
    name = "h" + id + ".html"
    fileName = base_dir + name
    f = open(fileName, "w")
    f.write(htmlText)
    f.close()

    print("file: ", fileName)
    return name, fileName


def generate_index(articles):
    body = ''
    for key in reversed(sorted(articles.keys())):
        articleObject = articles[key]
        body = body + articleObject.link
    return construct_html(body, "")

def doSomeIds(ids, existing_body):
    articles = {}
    counter = 0
    body = ''
    today = date.today()
    for id in ids:
        try:
            url = 'https://www.haaretz.co.il/amp/' + id
            articleObject = readAndProcess(id, url)
            if articleObject.fullHtml=='':
                continue
            file_relative_path, file_full_path = saveToFile(articleObject.id, counter, articleObject.fullHtml)
            time = articleObject.updatedAt
            if (time == ''):
                time = articleObject.publishedAt
            articleObject.link = '<p><b>' + articleObject.publishedAt + '</b><a href="' + file_relative_path + '">' + str(articleObject.header) + '</a></p>'
            body = body + articleObject.link
            if (articleObject.publishedAt.startswith(str(today))):
                articles[articleObject.publishedAt + articleObject.id] = articleObject
                counter = counter + 1
                if counter > LIMIT:
                    break
        except:
            print("some exception with id", id)

    print('generating index for',len(articles), 'articles...')
    html = generate_index(articles)
    # html = '<html dir="rtl" lang="he"><head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/></head><body>' + \
    #        body + existing_body + '</body></html>'
    f = open(base_dir +'index.html', "w")
    f.write(html)
    f.close()

def first_page():
    url = 'https://www.haaretz.co.il'
    print("loading first page", url, '...')
    html = urlopen(url, )
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    print("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    #bs.find_all("article")
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
        print(id)
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
        #print("file", relative_path, "header", header)
        link = '<p><a href="h' + relative_path + '">' + str(header) + '</a></p>'
        body = body + link
    #html = '<html dir="rtl" lang="he"><head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1" name="viewport"/></head><body>' + body + '</body></html>'
    return body

def process_page(url):
    print("loading url", url, '...')
    try:
        html = urlopen(url, )
    except:
        return []
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    print("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    #bs.find_all("article")
    list_of_articles = bs.html.find_all(
        lambda tag: (tag.name == "a") and ('href' in tag.attrs.keys()) and ("1.86" in tag.attrs['href']), recursive=True)
    links = {"1"}
    for href in list_of_articles:
        #print(href)
        links.add(href.attrs["href"])
        #hrefs = div.find_all("a")
        #for href in hrefs:
        #    print (href.attrs["href"])
        #    links.add(href.attrs["href"])
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
        print(id)
    return ids


existing_body = ""
#existing_body = find_existing_articles('/home/evyatar/GitHub/github-pages-hello-world/haaretz')
article_ids = first_page()
#print(len(article_ids))
urls = ['https://www.haaretz.co.il/news'
    , 'https://www.themarker.com/allnews'
    , 'https://www.themarker.com/wallstreet'
    , 'https://www.themarker.com/misc/all-headlines'
    , 'https://www.themarker.com/realestate'
    , 'https://www.themarker.com/technation'
    , 'https://www.themarker.com/magazine'
    ,'https://www.haaretz.co.il/magazine'
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

for url in urls:
    more_article_ids = process_page(url)
    article_ids.extend(more_article_ids)
    article_ids = remove_duplicates(article_ids)
print("now reading",len(article_ids),"articles")
doSomeIds(article_ids, existing_body)
