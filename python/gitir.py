from lp import save_to_file, add, BASE_DIR
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


courses = [
    ['https://git.ir/linkedin-learn-apache-kafka-for-beginners/', 'Apache Kafka Training for Beginners', 'kafka1']
]


def name_from_link(link):
    sindex = 1 + str(link).rindex('/')
    bindex = str(link).rindex('git') - 1
    result = link[sindex:bindex]
    return result


def readAndProcess(url, dir_name):
    result = ''
    print("loading", url, '...')
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers=
    {'User-Agent': user_agent,
     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q = 0.8',
    'Accept-Encoding': 'deflate, br',
     'Accept-Language':'en-US,en;q=0.9,he;q=0.8'})
    response = urlopen(request)
    html = response.read()
    print("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    all = bs.find_all(name='li', class_='ml-3')
    sections = bs.find_all(name='h2')
    linksToAllParts = [x.div.a.attrs['href'] for x in all]
    names = [name_from_link(x) for x in linksToAllParts]
    #sourceLines = [x.div.a.sourceline for x in all]

    result = ''
    for command in ['#!/bin/sh',
                    'cd ' + "'" + BASE_DIR + "'" ,
                    'mkdir ' + "'" + dir_name + "'" ,
                    'cd ' + "'" + dir_name+ "'" ]:
        result = add(command, result)

    for i in range(0,len(linksToAllParts)):
        command = "curl '" + linksToAllParts[i] + "' -o '" + names[i] + "'"
        result = add(command, result)
    return result


def process(num):
    file_name = str(num).rjust(3, '0') + '_' + courses[num][2]
    if not (file_name.endswith('.sh')):
        file_name = file_name + '.sh'
    save_to_file(readAndProcess(courses[num][0], courses[num][1]), file_name)


if __name__ == "__main__":
    for i in range(0, len(courses)):
        process(i)

