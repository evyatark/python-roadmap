from lp import save_to_file, add, BASE_DIR, fix_chars
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

# TODO implement creating separate dir for each module (same as lcrux)

courses = [
    #['https://git.ir/linkedin-learn-apache-kafka-for-beginners/', 'Apache Kafka Training for Beginners', 'kafka1']
    #,['https://git.ir/linkedin-essentials-of-css-for-react-developers/','Linkedin Learning - Essentials of Using CSS in React','reactcss']
    #, ['https://git.ir/codewithmosh-the-complete-nodejs-course/', 'Codewithmosh - The Complete Node.js Course', 'moshnode0']
    # , ['https://git.ir/skillshare-scrapy-python-web-scraping-crawling-for-beginners/', 'SkillShare - Scrapy Python Web Scraping and Crawling for Beginners', '']
    # Yandex-as03 , ['https://git.ir/linkedin-introducing-jupyter/', 'Linkedin Learning - Introducing Jupyter', 'jup1']
    #, ['https://git.ir/linkedin-cloud-native-development-with-node-js-docker-and-kubernetes/', 'Linkedin Learning - Cloud Native Development with Node.js Docker and Kubernetes', 'nodek8s']
    #ek3011 , ['https://git.ir/linkedin-introducing-postman/', '', '']
     ['https://git.ir/teamtreehouse-user-authentication-with-express-and-mongo/', 'TreeHouse - User Authentication with Express and Mongo', 'mongo1']
    # , ['https://git.ir/linkedin-building-a-small-business-website-with-wordpress/', 'Linkedin Learning - Building a Small Business Website with WordPress', 'wp1']
    # , ['https://git.ir/linkedin-installing-and-running-wordpress-local-by-flywheel/', 'Linkedin Learning - Installing and Running WordPress Local by Flywheel', 'wp2']
    #,['https://git.ir/linkedin-wordpress-backing-up-your-site/','Linkedin Learning - WordPress Backing Up Your Site','wp3']
    #,['https://git.ir/linkedin-cloud-native-development-with-node-js-docker-and-kubernetes/','Linkedin Learning - Cloud Native Development with Node.js Docker and Kubernetes','node1']
    #,['https://git.ir/codewithmosh-complete-sql-mastery/','CodeWithMosh - Complete SQL Mastery','sql1']
    # ,['https://git.ir/linkedin-building-vue-and-node-apps-with-authentication/','Linkedin Learning - Learn How to Build Vue and Node Applications with Authentication','vue1']
    # , ['https://git.ir/packtpub-creating-smart-contracts-with-ethereum/', 'Packt - Creating Smart Contracts with Ethereum', 'blockchain1']
    # , ['https://git.ir/packtpub-blockchain-and-bitcoins-a-complete-package/', 'Packt - Blockchain and Bitcoins A Complete Package', 'blockchain2']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
]


def name_from_link(link):
    sindex = 1 + str(link).rindex('/')
    bindex = str(link).rindex('git') - 1
    result = link[sindex:bindex] + '.mp4'
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
    dl = bs.find_all(name='a', class_='download-link')
    download_link = ''
    if (len(dl) > 0):
        download_link = dl[0].attrs['href']

    result = ''
    for command in ['#!/bin/sh',
                    'cd ' + "'" + BASE_DIR + "'" ,
                    'mkdir ' + "'" + dir_name + "'" ,
                    'cd ' + "'" + dir_name+ "'" ]:
        result = add(command, result)

    # download sources
    if len(download_link) > 0:
        name = 'exercise_files.zip'
        sindex = download_link.rindex('git.ir') + len('git.ir')
        name = download_link[sindex:]
        name = fix_chars(name)
        command = "curl '" + download_link + "' -o '" + name + "'"
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

