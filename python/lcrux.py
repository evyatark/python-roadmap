from lp import save_to_file, add, BASE_DIR, fix_chars
from selenium1 import selenium_bs

WAIT_EVERY_X_DOWNLOADS = 5
WAIT_INTERVAL_AFTER_DOWNLOADS = 10
WAIT_AFTER_SECTION = True
WAIT_INTERVAL_AFTER_SECTION = 30


courses = [
     #['https://www.learningcrux.com/course/apache-kafka-series-kafka-streams-for-data-processing', 'dummy', 'crux_kafka_stream']
     ['https://www.learningcrux.com/course/splunk-2019-beginner-to-architect', 'dummy', 'crux_splunk']
     #,['https://www.learningcrux.com/course/python-3-deep-dive-part-1', 'dummy', 'crux_pythonDeepDive1']
    #,['https://www.learningcrux.com/course/python-3-deep-dive-part-2', 'dummy', 'crux_pythonDeepDive2']
    #, ['https://www.learningcrux.com/course/python-3-deep-dive-part-3', 'dummy', 'crux_pythonDeepDive3']
      #,['https://www.learningcrux.com/course/python-3-deep-dive-part-4-oop', 'dummy', 'crux_pythonDeepDive4']
    #, ['https://www.learningcrux.com/course/beginner-react-2019-create-a-movie-web-app', 'dummy', 'crux_react0']
    #, ['https://www.learningcrux.com/course/apache-kafka-series-learn-apache-kafka-for-beginners-v2', 'dummy', 'crux_kafka0']
    # , ['https://www.learningcrux.com/course/apache-kafka-series-kafka-connect-handson-learning', 'dummy', 'crux_kafka_connect']
    # , ['https://www.learningcrux.com/course/apache-kafka-series-ksql-on-ksqldb-for-stream-processing', 'dummy', 'crux_kafka_ksql']
    # , ['https://www.learningcrux.com/course/modern-react-with-redux-2019-update', 'dummy', 'crux_react_redux0']
    # , ['https://www.learningcrux.com/course/build-a-slack-chat-app-with-react-redux-and-firebase', 'dummy', 'crux_react_firebase0']
    # , ['https://www.learningcrux.com/course/complete-react-developer-in-2019-w-redux-hooks-graphql', 'dummy', 'crux_react_complete']
    # , ['https://www.learningcrux.com/course/universal-react-with-nextjs-the-ultimate-guide', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/full-stack-project-spring-boot-20-reactjs-redux', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/vue-js-2-the-complete-guide-incl-vue-router-vuexs', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/advanced-react-and-redux-2018-edition', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/react-nodejs-express-mongodb-the-mern-fullstack-guide', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/understanding-npm-nodejs-package-manager', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/nodejs-the-complete-guide-incl-mvc-rest-apis-graphqls', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/python-for-data-science-and-machine-learning-bootcamp', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/spark-and-python-for-big-data-with-pyspark', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/django-2-build-deploy-fully-featured-web-application', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/python-for-statistical-analysis', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/python-and-django-full-stack-web-developer-bootcamp-2', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/django-python-complete-bundle-django-real-project-2020', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/the-complete-python-programmer-bootcamp-2020', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/importing-financial-data-with-python-from-free-web-sources', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/manage-finance-data-with-python-pandas-unique-masterclass', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/ultimate-aws-certified-sysops-administrator-associate-2019', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/ultimate-aws-certified-solutions-architect-associate-2019', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/aws-lambda-and-the-serverless-framework-hands-on-learning', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/aws-cloudformation-master-class', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/amazon-eks-starter-docker-on-aws-eks-with-kubernetes', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/aws-dynamodb-the-complete-guide-build-18-hands-on-demos', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/the-complete-developers-guide-to-mongodb', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/apache-spark-for-java-developers', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/apache-maven-beginner-to-guru', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/introduction-to-apache-nifi-hortonworks-dataflow-hdf-20', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/docker-and-kubernetes-the-complete-guide', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/automated-software-testing-with-cypress-2020-update', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/r-programming-for-absolute-beginners', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/introduction-to-data-science', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/the-modern-javascript-bootcamp-2019', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/canary-deployments-to-kubernetes-using-istio-and-friends', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/vue-js-2-the-complete-guide-incl-vue-router-vuexs', 'dummy', 'crux_']
    # , ['https://www.learningcrux.com/course/the-complete-deep-web-course-2018-become-an-expert', 'dummy', 'crux_']
    # , ['', 'dummy', 'crux_']
    # , ['', 'dummy', 'crux_']
    # , ['', 'dummy', 'crux_']
]



def name_from_link(link):
    sindex = 1 + str(link).rindex('/')
    bindex = str(link).rindex('git') - 1
    result = link[sindex:bindex] + '.mp4'
    # https://www.learningcrux.com/video/splunk-2019-beginner-to-architect/0/0
    return result


def readAndProcess(url, dir_name):
    result = ''
    print("loading", url, '...')
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

    result = ''
    for command in ['#!/bin/sh',
                    'cd ' + "'" + BASE_DIR + "'" ,
                    'mkdir ' + "'" + dir_name + "'" ,
                    'cd ' + "'" + dir_name+ "'" ]:
        result = add(command, result)

    current_section = ''
    for i in range(0,len(all_chapter_links)):
        if i%WAIT_EVERY_X_DOWNLOADS==0:
            result = sleep(WAIT_INTERVAL_AFTER_DOWNLOADS, result)
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
            if WAIT_AFTER_SECTION:
                result = sleep(WAIT_INTERVAL_AFTER_SECTION, result)
            current_section = title
        #name = title + '-' + str(i).rjust(3, '0') + ' ' + all_chapter_names[i]
        name = str(i).rjust(3, '0') + ' ' + all_chapter_names[i] + '.mp4'
        link = all_chapter_links[i].replace('/video', 'https://www.learningcrux.com/play')
        command = "curl '" + link + "?type=hard' -L -o '" + name + "'"
        result = add(command, result)
    return result

def sleep(seconds, result):
    result = add("echo waiting " + str(seconds) + " seconds...", result)
    result = add("sleep " + str(seconds), result)
    return result


def process(num):
    file_name = str(num).rjust(3, '0') + '_' + courses[num][2]
    if not (file_name.endswith('.sh')):
        file_name = file_name + '.sh'
    save_to_file(readAndProcess(courses[num][0], courses[num][1]), file_name)


if __name__ == "__main__":
    for i in range(0, len(courses)):
        process(i)

