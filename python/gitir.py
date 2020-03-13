from lp import save_to_file, add, BASE_DIR, fix_chars
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from lcrux import sleep

# TODO implement creating separate dir for each module (same as lcrux)
WAIT_EVERY_X_DOWNLOADS = 5
WAIT_INTERVAL_AFTER_DOWNLOADS = 10
WAIT_AFTER_SECTION = True
WAIT_INTERVAL_AFTER_SECTION = 30

courses = [
     ['https://git.ir/linkedin-building-a-small-business-website-with-wordpress/', 'Linkedin Learning - Building a Small Business Website with WordPress', 'wp1']
    ,['https://git.ir/linkedin-essentials-of-css-for-react-developers/','Linkedin Learning - Essentials of Using CSS in React','reactcss']
    , ['https://git.ir/linkedin-installing-and-running-wordpress-local-by-flywheel/', 'Linkedin Learning - Installing and Running WordPress Local by Flywheel', 'wp2']
    ,['https://git.ir/linkedin-wordpress-backing-up-your-site/','Linkedin Learning - WordPress Backing Up Your Site','wp3']
    ,['https://git.ir/linkedin-cloud-native-development-with-node-js-docker-and-kubernetes/','Linkedin Learning - Cloud Native Development with Node.js Docker and Kubernetes','node1']
    ,['https://git.ir/codewithmosh-complete-sql-mastery/','CodeWithMosh - Complete SQL Mastery','sql1']
    , ['https://git.ir/codewithmosh-the-complete-nodejs-course/', 'Codewithmosh - The Complete Node.js Course', 'moshnode0']
    ,['https://git.ir/linkedin-building-vue-and-node-apps-with-authentication/','Linkedin Learning - Learn How to Build Vue and Node Applications with Authentication','vue1']
    , ['https://git.ir/packtpub-creating-smart-contracts-with-ethereum/', 'Packt - Creating Smart Contracts with Ethereum', 'blockchain1']
    , ['https://git.ir/packtpub-blockchain-and-bitcoins-a-complete-package/', 'Packt - Blockchain and Bitcoins A Complete Package', 'blockchain2']

    #['https://git.ir/linkedin-learn-apache-kafka-for-beginners/', 'Apache Kafka Training for Beginners', 'kafka1']
    # , ['https://git.ir/skillshare-scrapy-python-web-scraping-crawling-for-beginners/', 'SkillShare - Scrapy Python Web Scraping and Crawling for Beginners', '']
    # Yandex-as03 , ['https://git.ir/linkedin-introducing-jupyter/', 'Linkedin Learning - Introducing Jupyter', 'jup1']
    #ek3011 , ['https://git.ir/linkedin-introducing-postman/', '', '']
     #,['https://git.ir/teamtreehouse-user-authentication-with-express-and-mongo/', 'TreeHouse - User Authentication with Express and Mongo', 'mongo1']
    # , ['https://git.ir/packtpub-learning-angular-for-django-developers/', 'Packt - Learning Angular for Django Developers', 'django1']
    # , ['https://git.ir/teamtreehouse-angular-basics/', 'TreeHouse - Angular Basics', 'ang1']
    # , ['https://git.ir/teamtreehouse-responsive-layouts/', 'TreeHouse - Responsive Layouts', 'web1']
    # , ['https://git.ir/teamtreehouse-practice-object-interaction/', 'TreeHouse - Practice Object Interaction', 'web2']
    # , ['https://git.ir/linkedin-more-css-selectors-for-react-developers/', 'Linkedin Learning - More CSS Selectors for React Developers', 'css2']
    # , ['https://git.ir/laracasts-modern-css-workflow/', 'Laracasts - Modern CSS Workflow', 'css3']
    # , ['https://git.ir/teamtreehouse-javascript-and-the-dom/', 'TreeHouse - JavaScript and the DOM', 'js3']
    # , ['https://git.ir/teamtreehouse-dom-scripting-by-example/', 'TreeHouse - DOM Scripting By Example', 'js4']
    # , ['https://git.ir/teamtreehouse-introduction-to-selenium/', 'TreeHouse - Introduction to Selenium', 'selenium2']
    # , ['https://git.ir/linkedin-wordpress-contact-forms/', 'Linkedin Learning - WordPress Contact Forms', 'wp4']
    # , ['https://git.ir/linkedin-introducing-postman/', 'Linkedin Learning - Introducing Postman', 'postman1']
    # , ['https://git.ir/linkedin-css-selectors/', 'Linkedin Learning - CSS Selectors', 'css4']
    # , ['https://git.ir/laracasts-testing-vue/', 'Laracasts - Testing Vue', 'vue2']
    # , ['https://git.ir/linkedin-learning-cloud-computing-core-concepts/', 'Linkedin Learning - Cloud Computing Core Concepts', 'cloud1']
    # , ['https://git.ir/linkedin-learning-cloud-computing-public-cloud-platforms/', 'Linkedin Learning - Cloud Computing Public Cloud Platforms', 'cloud2']
    # , ['https://git.ir/pluralsight-planning-and-configuring-a-cloud-solution-on-google-cloud/', 'Pluralsight - Planning and Configuring a Cloud Solution on Google Cloud', 'cloud3']
    # , ['https://git.ir/packtpub-full-javascript-masterclass-course-es6-modern-development/', 'Packt - Full JavaScript Masterclass Course ES6 Modern Development', 'js5']
    # , ['https://git.ir/javascript-tutorial-for-beginners-learn-javascript-basics-in-1-hour-2019/', 'Codewithmosh - JavaScript Tutorial for Beginners Learn JavaScript Basics in 1 Hour [2019]', 'js6']
    # , ['https://git.ir/laracasts-es2015-crash-course/', 'Laracasts - ES2015 Crash Course', 'js7']
    # , ['https://git.ir/linkedin-r-programming-in-data-science-dates-and-times/', 'Linkedin Learning - R Programming in Data Science', 'r1']
    # , ['https://git.ir/skillshare-big-data-analysis-with-apache-spark-pyspark-python/', 'Skillshare - Big data analysis with Apache spark PySpark Python', 'spark1']
    # , ['https://git.ir/skillshare-essentials-of-data-science/', 'Skillshare - Essentials of Data Science', 'ds1']
    # , ['https://git.ir/laracasts-learn-redis-through-examples/', 'Laracasts - Learn Redis Through Examples', 'redis1']
    # , ['https://git.ir/packtpub-learning-programmatic-access-to-mongodb/', 'Packt - Learning Programmatic Access to MongoDB', 'mongo2']
    # , ['https://git.ir/packtpub-learn-spring-and-spring-boot-10x-productive-java-development/', 'Learn Spring and Spring Boot 10x Productive Java Development', 'spring1']
    # , ['https://git.ir/packtpub-basic-relational-database-design/', 'Packt - Basic Relational Database Design', 'db1']
    # , ['https://git.ir/packtpub-professional-scala/', 'Packt - Professional Scala', 'scala1']
    # , ['https://git.ir/packtpub-hands-on-auto-devops-with-gitlab-ci/', 'Packt - Hands On Auto DevOps with GitLab CI', 'gitlab1']
    # , ['https://git.ir/skillshare-vagrant-masterclass/', 'Skillshare - Vagrant Masterclass', 'vagrant1']
    # , ['https://git.ir/linkedin-introduction-to-quantum-computing/', 'Linkedin Learning - Introduction to Quantum Computing', 'quantum']
    # , ['https://git.ir/linkedin-github-essential-training/', 'Linkedin Learning - GitHub Essential Training', 'git1']
    # , ['https://git.ir/pluralsight-aws-network-design-getting-started/', 'Pluralsight - AWS Network Design Getting Started', 'aws2']
    # , ['https://git.ir/teamtreehouse-django-class-based-views/', 'TreeHouse - Django Class based Views', 'django2']
    # , ['https://git.ir/linkedin-test-driven-development-in-django/', 'Linkedin Learning - Test Driven Development in Django', 'django3']
    # , ['https://git.ir/packtpub-python-and-data-science-a-practical-guide/', 'Packt - Python and Data Science A Practical Guide', 'ds2']
    # , ['https://git.ir/packtpub-hands-on-python-3-x-gui-programming/', 'Packt - Hands-On Python 3.x GUI Programming', 'python1']
    # , ['https://git.ir/packtpub-automating-web-testing-with-selenium-and-python/', 'Packt - Automating Web Testing with Selenium and Python', 'selenium3']
    # , ['https://git.ir/skillshare-web-scraping-with-python/', 'Skillshare - Web Scraping with Python', 'python2']
    # , ['https://git.ir/codewithmosh-the-complete-python-programming-course/', 'Codewithmosh - The Complete Python Programming Course', 'python3']
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
    sections = bs.find_all(name='div', class_='course-lecture-list')
    section_positions = [x.sourcepos for x in sections]
    linksToAllParts = [x.div.a.attrs['href'] for x in all]
    positions = [x.div.a.sourcepos for x in all]
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

    current_section_number = 0
    for i in range(0, len(linksToAllParts)):
        if (i != 0) and (i % WAIT_EVERY_X_DOWNLOADS == 0):
            result = sleep(WAIT_INTERVAL_AFTER_DOWNLOADS, result)
        title = str(current_section_number).rjust(2,'0')
        if (current_section_number < len(section_positions)) and (positions[i] > section_positions[current_section_number]):
            if (current_section_number != 0):
                result = add("cd ..", result)
            result = add("mkdir '" + title + "'", result)
            result = add("cd '" + title + "'", result)
            if (i != 0) and WAIT_AFTER_SECTION:
                result = sleep(WAIT_INTERVAL_AFTER_SECTION, result)
            current_section_number = current_section_number + 1
        command = "curl '" + linksToAllParts[i] + "' -o '" + names[i] + "'"
        result = add(command, result)
    #result = alternative_download(result, names, linksToAllParts)
    # for i in range(0,len(linksToAllParts)):
    #     command = "curl '" + linksToAllParts[i] + "' -o '" + names[i] + "'"
    #     result = add(command, result)
    return result


def alternative_download(result, names, linksToAllParts):
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

