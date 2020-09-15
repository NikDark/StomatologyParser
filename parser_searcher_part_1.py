import csv
import re
import sys

import requests
from bs4 import BeautifulSoup as BS
from selenium import webdriver

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
}

GOOGLE_URL = f"https://www.google.com/search?q=Стоматология&start="
MAIL_URL = f"https://go.mail.ru/search?fm=1&q=Стоматология&sf="
BING_URL = f"https://www.bing.com/search?q=Стоматология&sp=-1&pq=cтоматология&sc=8&qs=n&sk=&first="
YANDEX_URL = f"https://yandex.com/search/?clid=2186621&text=Стоматология&p="

ERROR_404 = 404
ERROR_429 = 429


def html_get(url):
    """This function copy html code and return him in str format

    Arguments:
        url {str} -- search query link

    Returns:
        Error code or html page if no error occurred

    """
    try:
        r = requests.get(url, headers=HEADERS)
        # If the status of the error code is 200 or 404, then everything is fine
        # Yes, and 404, because this is necessary in order to track the end of pages in the search engine results
        assert (r.status_code == 200 or r.status_code == 404), """
        !!! Too many response from your computer !!!
        !!!    Use VPN or try another network    !!!"""
        return r.text
    except AssertionError as Assert:
        print(Assert)
        return r.status_code
    except Exception as e:
        print('Check your internet connection or try using VPN connection')


# def mail_html_get(url=MAIL_URL):
#     """This function returns the html on the site mail.ru,
#     since mail.ru is a dynamic site and
#     it returns full HTML only after
#     launching it in the browser

#     For this feature to work, you must download the webdriver for Mozilla Firefox
#     and add it to the /Scripts folder which is located
#     in root folder with your Python (or in virtualenv)

#     Keyword Arguments:
#         url {str} -- [search query link to mail.ru] (default: {MAIL_URL})

#     Returns:
#          generated_html -- page layout as a string containing html code
#     """
#     try:
#         options = webdriver.FirefoxOptions()  # Options for our browser
#         options.add_argument('--headless')  # Hides browser display
#         browser = webdriver.Firefox(firefox_options=options)
#         browser.get(url)  # open our url in browser
#         generated_html = browser.page_source  # copy generated with js html
#         browser.quit()  # close browser
#         return generated_html
#     except Exception:  # if no internet connection, generate Exception
#         print('Check your internet connection and try again')
#         sys.exit()  # exit from program, because no internet connection


def mail_ru_parse() -> list:
    """
    This function "pulls out" only the data we need, such as
    Anchor, URL, Snippet from mail.ru page
    The function goes through the pages of the search engine mail.ru and
    if the page returned error code 404 means the previous page was the last    
    and you can complete the search for items
    Only this function uses selenium

    Returns:
        list -- Processed Results
    """
    options = webdriver.FirefoxOptions()  # Options for our browser
    options.add_argument('--headless')  # Hides browser display
    browser = webdriver.Firefox(firefox_options=options)

    datas = []  # Page parsing results
    page = 0
    while True:
        # While we can find some data we need
        # then the cycle will work, but how the valid data ends,
        # the cycle will complete its work
        worked_url = MAIL_URL
        worked_url += str(page * 10)  # Working URL with page number
        try:
            browser.get(worked_url)  # open our url in browser
            html = browser.page_source  # copy generated with js html
        except Exception:  # if no internet connection, generate Exception
            print('Check your internet connection or try using VPN connection ')
            browser.quit()  # close selenium browser
            return  # exit from program, because no internet connection
        print('\rYou have finished %3d%%' % (page * 100 // 65), end='',
              flush=True)  # This strings print progress of parsing pages
        soup = BS(html, 'html.parser')  # Tree of our page in BS4 format
        # list of our cards that the search engine found
        results = soup.find_all('li', class_='result__li')
        if not results:
            break
        # Disassemble html in parts
        for item in results:
            try:
                datas.append(
                    {
                        'Searcher': 'mail.ru',
                        'Url': item.find('a', class_='light-link').get('href'),
                        'Anchor': item.find('a', class_='light-link').get_text(),
                        'Snippet': item.find('div', class_='SnippetResult-result').find('span').get_text(),
                    }
                )
            # If some elements were not found, then the data is not valid
            # and we perform the next step
            except Exception:
                pass
        page += 1
    # This strings print that we finished of parsing pages
    print('\rYou have finished %3d%%' % 100, end='', flush=True)
    print('\n', page, 'pages was parsed')
    browser.quit()  # close selenium browser
    return datas  # return all valid data that we could find


def google_com_parse() -> list:
    """
    This function "pulls out" only the data we need, such as
    Anchor, URL, Snippet from google.com page
    The function goes through the pages of the search engine google.com and
    if the page returned error code 404 means the previous page was the last    
    and you can complete the search for items.
    
    This function uses module requests

    Returns:
        list -- Processed Results
    """
    datas = []  # Page parsing results
    page = 0
    while True:
        # While we can find some data that we need,
        # the cycle will work, but how the valid data ends,
        # the cycle will complete its work
        worked_url = GOOGLE_URL
        worked_url += str(page * 10)  # Working URL with page number
        html = html_get(worked_url)  # HTML markup


        # If html_get returned one of the errors with code 404 or 429,
        # then we end the function
        if html in [ERROR_404, ERROR_429]:
            return
        soup = BS(html, 'html.parser')  # Tree of our page in BS4 format
        print('\rYou have finished %3d%%' % (page * 100 // 28), end='', flush=True)  # This strings print progress of parsing pages
        # list of our cards that the search engine found
        results = soup.find_all('div', class_='g')
        # If you didn’t find anything on this page, then it’s the last one and we exit loop
        if not results:
            break
        for item in results:
            try:
                snippet = item.find('div', class_='s').find(
                    'span', class_='st').get_text()
                # clean snippet from garbage with reqular expression
                clean_snippet = re.sub('\xa0', '', snippet)
                datas.append(
                    {
                        'Searcher': 'google.com',
                        'Url': item.find('div', class_='r').find('a').get('href'),
                        'Anchor': item.find('h3', class_='LC20lb DKV0Md').get_text(),
                        'Snippet': clean_snippet,
                    }
                )
                # If some elements were not found, then the data is not valid
                # and we perform the next step
            except Exception:
                pass
        page += 1
    print('\rYou have finished %3d%%' % 100, end='', flush=True)
    print('\n',page,'pages was parsed')
    return datas


def yandex_com_parse() -> list:
    """
    This function collects search results from the Yandex.com search engine.
    ! Do not run this function very often, because Yandex actively catches such requests
    
    Returns:
        data[list] -- data collected
    """    
    datas = []
    page = 0
    while True:
        # While we can find some data that we need,
        # the cycle will work, but how the valid data ends,
        # the cycle will complete its work
        worked_url = YANDEX_URL
        worked_url += str(page)
        html = html_get(worked_url)
        if html in [ERROR_404, ERROR_429]:
            return
        soup = BS(html, 'html.parser')
        print('\rYou have finished %3d%%' % (page * 100 // 25), end='', flush=True)
        results = soup.find_all('li', class_='serp-item')
        if not results:
            break
        for item in results:
            try:
                url = item.find('h2', class_='organic__title-wrapper').find('a', class_='link').get('href')
                
                if re.search('yabs.yandex', url): # If we found a link starting on yabs.yandex then this is advertising, so we skip it
                    continue
                
                anchor = item.find('div', class_='organic__url-text').get_text()
                clean_anchor = re.sub('\xa0', '', anchor) # clean anchors from garbage
                
                snippet = item.find('span', class_='extended-text__full').get_text()
                clean_snippet = re.sub('\xa0', '', snippet) # clean snippet from garbage
                
                datas.append(
                    {
                        'Searcher': 'yandex.com',
                        'Url': url,
                        'Anchor': clean_anchor.replace('Скрыть', '').strip(), #delete the inscription "Скрыть" at the end of each line
                        'Snippet': clean_snippet.replace('Скрыть', '').strip(), #delete the inscription "Скрыть" at the end of each line
                    }
                )
            # If some elements were not found, then the data is not valid
            # and we perform the next step
            except Exception:
                continue
        page += 1
    print('\rYou have finished %3d%%' % 100, end='', flush=True)
    print('\n',page,'pages was parsed')
    return datas


def bing_com_parse() -> list:
    """
    This function collects search results from the bing.com search engine.
    
    Returns:
        list -- [description]
    """    
    datas = []
    num_page = 0 # Page number
    while True:
        #The bing.com search engine normally displays a maximum of 100 pages
        # and each page has 10 articles. Therefore, we took a maximum of 1000 articles
        # While we can find some data that we need,
        # the cycle will work, but how the valid data ends,
        # the cycle will complete its work
        if num_page == 0:
            page = 1
        else:
            page = ((num_page - 1) * 10 + 11)
        if page >= 1000:
            break
        worked_url = BING_URL
        worked_url += str(page)
        html = html_get(worked_url)
        if html in [ERROR_404, ERROR_429]:
            return
        soup = BS(html, 'html.parser')
        print('\rYou have finished %3d%%' % (num_page * 100 // 100), end='', flush=True)
        results = soup.find_all('li', class_='b_algo')
        # If there are no elements on this page, then we proceed to the next
        if not results:
            num_page += 1
            continue

        for item in results:
            url = item.find('h2').find('a').get('href')
            anchor = item.find('h2').find('a').get_text()
            clean_anchor = re.sub('\xa0', '', anchor) # clean anchor from garbage
            snippet = item.find('div', class_='b_caption').find('p').get_text()
            clean_snippet = re.sub('\xa0', '', snippet) # clean snippet from garbage
            try:
                datas.append(
                    {
                        'Searcher': 'bing.com',
                        'Url': url,
                        'Anchor': clean_anchor.strip(),
                        'Snippet': clean_snippet.strip(),
                    }
                )
            # If some elements were not found, then the data is not valid
            # and we perform the next step
            except Exception:
                continue
        num_page += 1
    print('\rYou have finished %3d%%' % 100, end='', flush=True)
    print('\n',num_page,'pages was parsed')
    return datas


def search_stomatology():
    """
    This function creates a file, collects data and writes it to a file.
    Search_Stomatology.csv encoded in UTF-16.
    Columns in the file are separated by a comma
    
    Columns: ['Searcher', 'Url', 'Anchor', 'Snippet']

    """    
    with open('Search_Stomatology.csv', mode='w', encoding='utf-16', newline='') as csv_file:
        fieldnames = ['Searcher', 'Url', 'Anchor', 'Snippet'] # Column Names
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',') # this is our so-called "writer" who will write our data to a file
        writer.writeheader() # this function records the title
        
        try:
            print('Start parsing Mail.ru')
            for item in mail_ru_parse():
                writer.writerow(item)
            print('Mail.ru -- OK\n')
        except Exception:
            print('Mail.ru -- Error\n')

        try:
            print('Start parsing Google.com')
            for item in google_com_parse():
                writer.writerow(item)
            print('Google.com -- OK\n')
        except Exception as e:
            print(e)
            print('Google.com -- Error\n')

        try:
            print('Start parsing Yandex.com')
            for item in yandex_com_parse():
                writer.writerow(item)
            print('Yandex.com -- OK\n')
        except Exception as e:
            print(e)
            print('Yandex.com -- Error\n')

        try:
            print('Start parsing Bing.com')
            for item in bing_com_parse():
                writer.writerow(item)
            print('Bing.com -- OK\n')
        except Exception as e:
            print(e)
            print('Bing.com -- Error\n')


if __name__ == "__main__":
    search_stomatology()
