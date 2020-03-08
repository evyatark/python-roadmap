
# https://www.freetutorials.ca/course/creating-web-applications-with-go-2


from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

BASE_DIR = '/home/evyatar/Downloads/video/lp';


def fix(x):
    y = str(x)
    z = y.replace('/video','https://www.learningcrux.com/play') + '?type=hard -L -o '
    return z


def fix_chars(originalStr):
    name = originalStr.translate({ord(i): None for i in '?:/!&'})
    return name


def readAndProcess(url, dir_name):
    result = ''
    #print("loading", url, '...')
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    request = Request(url, headers={'User-Agent': user_agent})
    response = urlopen(request)
    html = response.read()
    #print("souping...")
    bs = BeautifulSoup(html, 'html.parser')
    #bs = BeautifulSoup(html, 'lxml')
    all = bs.find_all(name='a', class_='list-brief__item__content')
    linksToAllParts = [fix(x.attrs['href']) for x in all]
    names = [x.text.rstrip().lstrip() for x in all]
    sourceLines = [x.sourceline for x in all]
    modules = bs.find_all(name='div', class_='list-brief__top__section')
    module_names = bs.find_all(name='div', class_='list-brief__top__title')
    module_dir_names = [x.text for x in module_names]
    # add lines in beginning of sh file:
    for command in ['#!/bin/sh',
                    'cd ' + "'" + BASE_DIR + "'" ,
                    'mkdir ' + "'" + dir_name + "'" ,
                    'cd ' + "'" + dir_name+ "'" ]:
        result = add(command, result)

    currentModule = -1
    last_module = False
    for i in range(0, len(names)):
        if (not last_module):
            # print(currentModule)
            # print(modules[currentModule+1])
            # print(modules[currentModule+1].sourceline)
            if (modules[currentModule+1].sourceline is None) or (modules[currentModule+1].sourceline < sourceLines[i]):
                currentModule = currentModule + 1
                if currentModule == len(modules) - 1:
                    last_module = True
                proto_dir_name = "'" + str(currentModule+1).rjust(2,'0') + ' ' + module_dir_names[currentModule] + "'"
                dir_name = fix_chars(proto_dir_name)
                if currentModule > 0:
                    result = add ('cd ..', result)
                result = add('mkdir ' + dir_name, result)
                result = add('cd ' + dir_name, result)
        if (currentModule <= len(modules)):
            # if we have 10 files, width is 2. if we have 100 files, width is 3.
            width = len(str(len(names)))
            # pad 0 to str(i)
            chapter_number = str(i).rjust(width, '0')
            # remove problematic chars from name (?, :, /, etc)
            name = fix_chars(names[i])
            command = 'curl ' + linksToAllParts[i] + " '" + chapter_number + ' ' + name + ".mp4'"
            result = add(command, result)
    result = add('cd ' + "'" + BASE_DIR + "'", result)
    return result


def add(command, result):
    result = result + command + '\n'
    print(command)
    return result


courses = [
    ['https://www.freetutorials.ca/course/creating-web-applications-with-go-2', 'Pluralsight - Creating Web Applications with Go', 'go2.sh']
    ,['https://www.freetutorials.ca/course/advanced-javascript-2', 'Pluralsight - Advanced JavaScript', 'js2.sh']
    ,['https://www.freetutorials.ca/course/kotlin-fundamentals-2', 'Pluralsight - Kotlin Fundamentals', 'kf.sh']
    ,['https://www.freetutorials.ca/course/shifting-javascript-into-high-gear-with-web-workers-2','Pluralsight - Shifting JavaScript into High Gear with Web Workers', 'jsww2.sh']
    ,['https://www.freetutorials.ca/course/getting-started-with-kubernetes-2','Pluralsight - Getting Started with Kubernetes','k8s.sh']
    , ['https://www.freetutorials.ca/course/creating-offline-first-mobile-apps-with-html5-pluralsight-2', 'Pluralsight - Creating Offline first Mobile Apps with HTML5', 'off.sh']
    , ['https://www.freetutorials.ca/course/socket-io-building-real-time-applications-2', 'Pluralsight - Building Real time Applications with Socket.io', 'sock.sh']
    , ['https://www.freetutorials.ca/course/angular-cli-pluralsight', 'Pluralsight - Angular CLI', 'angcli.sh']
    , ['https://www.freetutorials.ca/course/ux-big-picture-2', 'Pluralsight - User Experience The Big Picture', 'ux2.sh']
    , ['https://www.freetutorials.ca/course/ux-driven-software-design-2', 'Pluralsight - UX driven Software Design', 'uxd.sh']
    , ['https://www.freetutorials.ca/course/windows-how-its-hacked-how-to-protect-2', 'Pluralsight - Windows How Its Hacked How to Protect It', 'win.sh']
    , ['https://www.freetutorials.ca/course/realtime-web-with-nodejs', 'Frontend Masters - Real Time Web with Node.js', 'fm1.sh']
    , ['https://www.freetutorials.ca/course/objectoriented-python', 'Treehouse - Object Oriented Python', 'oop']
    , ['https://www.freetutorials.ca/course/learning-amazon-web-services-aws-for-developers', 'Linkedin Learning - Learning AWS for Developers', 'aws1']
    , ['https://www.freetutorials.ca/course/unit-testing-in-java', 'Treehouse - Unit Testing in Java', 'utj']
    , ['https://www.freetutorials.ca/course/implementing-ai-to-play-games-video', 'Packt - Implementing AI to Play Games', 'ai1']
    , ['https://www.freetutorials.ca/course/docker-deep-dive', 'Linux Academy - Docker Deep Dive', 'ddd']
    , ['https://www.freetutorials.ca/course/go-the-complete-bootcamp-course-golang', 'Udemy - Go The Complete Bootcamp Course', 'go3']
    , ['https://www.freetutorials.ca/course/build-a-javafx-application', 'Treehouse - Build a JavaFX Application', 'jfx']
    , ['https://www.freetutorials.ca/course/blockchain-fundamentals-pluralsight', 'Pluralsight - Blockchain Fundamentals', 'bch1']
    , ['https://www.freetutorials.ca/course/advanced-puppet-techniques-video', 'Packt - Advanced Puppet Techniques', 'ppt']
    , ['https://www.freetutorials.ca/course/learn-redis-and-utilize-jedis-with-spring-data-redis', 'Udemy - Learn Redis And Utilize Jedis With Spring Data Redis', 'redis1']
    , ['https://www.freetutorials.ca/course/http-basics', 'Treehouse - HTTP Basics', 'http0']
    , ['https://www.freetutorials.ca/course/nginx-web-server-deep-dive', 'Linux Academy - NGINX Web Server Deep Dive', 'ngnx']
    # , ['', '', '']
    # , ['', '', '']
    # , ['', '', '']
]


def save_to_file(content, file_name):
    print('saving to file', file_name, '...')
    f = open(BASE_DIR + '/' + file_name, "w")
    f.write(content)
    f.close()
    print('done!')


def process(num):
    file_name = str(num).rjust(3, '0') + '_' + courses[num][2]
    if not (file_name.endswith('.sh')):
        file_name = file_name + '.sh'
    save_to_file(readAndProcess(courses[num][0], courses[num][1]), file_name)


for i in range(0, len(courses)):
    process(i)
