import bs4
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC

def selenium_bs(url, delay):
    #url = 'https://www.learningcrux.com/course/apache-kafka-series-kafka-streams-for-data-processing'
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    print('starting Firefox webdriver...')
    browser = webdriver.Firefox(firefox_options=options)
    print('wait patiently, getting url', url, '...')
    browser.get(url)
    print('url retrieved!')
    WebDriverWait(browser, delay)
    #WebDriverWait(browser, delay).until(EC.presence_of_element_located(browser.find_element_by_id('headingOne')))
    soup = bs4.BeautifulSoup(browser.page_source, "html.parser")
    return soup

# bs = selenium_bs('https://www.learningcrux.com/course/apache-kafka-series-kafka-streams-for-data-processing', 1)
# elements = bs.select('article h1')
# print(elements)