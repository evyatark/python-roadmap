from lp import save_to_file, add, BASE_DIR, fix_chars
from selenium1 import selenium_bs
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


courses = [
     ['https://www.learningcrux.com/course/apache-kafka-series-kafka-streams-for-data-processing', 'dud', 'dud']
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
    # user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    # request = Request(url, headers= {'User-Agent': user_agent})
    # response = urlopen(request)
    # html = response.read()
    # print("souping...")
    # bs = BeautifulSoup(html, 'html.parser')
    bs = selenium_bs(url, 1)
    try:
        title = bs.find(name='h1', class_='content-h1')
        dir_name = str(title.text).rstrip().lstrip()
    except:
        pass
    sections = bs.find_all(name='section', class_='sectionRow')
    section_titles = [header.text.rstrip().replace(':\n',' - ') for header in bs.find_all(name='h2', class_='h6')]
    all_chapter_links = [a.attrs['href'] for a in bs.find_all(name='a', class_='accOpener')]
    all_chapter_names = [fix_chars(x.span.text.replace('Video', '').rstrip().lstrip()) for x in bs.find_all(name='a', class_='accOpener')]
    # linksToAllParts = [x.div.a.attrs['href'] for x in all]
    #names = [name_from_link(x) for x in all_links]
    #sourceLines = [x.div.a.sourceline for x in all]
    # dl = bs.find_all(name='a', class_='download-link')
    # download_link = ''
    # if (len(dl) > 0):
    #     download_link = dl[0].attrs['href']

    result = ''
    for command in ['#!/bin/sh',
                    'cd ' + "'" + BASE_DIR + "'" ,
                    'mkdir ' + "'" + dir_name + "'" ,
                    'cd ' + "'" + dir_name+ "'" ]:
        result = add(command, result)

    # download sources
    # if len(download_link) > 0:
    #     name = 'exercise_files.zip'
    #     sindex = download_link.rindex('git.ir') + len('git.ir')
    #     name = download_link[sindex:]
    #     name = fix_chars(name)
    #     command = "curl '" + download_link + "' -o '" + name + "'"
    #     result = add(command, result)

    current_section = ''
    for i in range(0,len(all_chapter_links)):
        # assuming all links look like:
        #'/video/apache-kafka-series-kafka-streams-for-data-processing/0/0'
        # extract the section number:
        link = all_chapter_links[i]
        section_number = int(str(link).split('/')[-2])
        title = section_titles[section_number]
        if (title != current_section):
            if (current_section != ''):
                result = add("cd ..", result)
            result = add("mkdir '" + title + "'", result)
            result = add("cd '" + title + "'", result)
            current_section = title
        #name = title + '-' + str(i).rjust(3, '0') + ' ' + all_chapter_names[i]
        name = str(i).rjust(3, '0') + ' ' + all_chapter_names[i]
        command = "curl '" + all_chapter_links[i] + "' -o '" + name + "'"
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

