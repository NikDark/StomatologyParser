import csv
import re
import threading
from multiprocessing.pool import ThreadPool

import requests
from bs4 import BeautifulSoup as BS
from selenium.common.exceptions import WebDriverException
from parser_searcher_part_1 import search_stomatology

threadLocal = threading.local() # create a local thread
pages = []

url_count = 0

def get_all_links():
    """
    Collects all links from the file Search_Stomatology.csv
    and returns them as list
    """    
    links = []
    global url_count
    file_name = 'Search_Stomatology.csv'

    with open(file_name, 'r', newline='', encoding='utf-16') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            links.append(row['Url'])
            url_count+=1

    return links


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
}


def get_html(url):
    """
    Accesses the page and copies its HTML code.
    Arguments:
        url {str} -- URL of the page you want to copy completely
    Returns:
        returns HTML page code [str]
    """    
    r = requests.get(url, headers=HEADERS)
    # immediately recode the page text in UTF-8
    r.encoding = 'utf-8'
    # check for the correct encoding. If valid characters
    # less than 15, then change the encoding on Windows-1251
    if len(re.findall("[а-яА-Я]+", r.text)) < 15:
        r.encoding = 'cp1251'
    return r.text

count_of_parsed_page = 0

def make_all(url):
    """
    Collects all the data that we need to collect from the page, such
    like URL, Head, Description, Keywords, h1, h2, h3
    
    Arguments:
        url {str} -- URL of the page from which to collect data
    """    
    global count_of_parsed_page
    try:
        # Получаем код страницы
        html = get_html(url)
        # Преобразуем её в тип BeautfoulSoup
        soup = BS(html, "html.parser")
        # Если произошла какая-то с открытием страницы, то переходим к следующей
    except WebDriverException as exc:
        count_of_parsed_page+=1
        return
    except Exception as exc:
        count_of_parsed_page+=1
        return

    try:
        # Собираем все элементы Description и очищаем от лишних пробелов по краям
        description = soup.find_all('meta', {"name": "description"})[
            0]['content'].strip()
    except IndexError:
        description = 'Такого тега нету'
    except KeyError:
        description = 'Пустой тэг'

    try:
        # Собираем все элементы Keywords и очищаем от лишних пробелов по краям
        keywords = soup.find_all('meta', {"name": "keywords"})[
            0]['content'].strip()
    except IndexError:
        keywords = 'Такого тега нету'
    except KeyError:
        keywords = 'Пустой тэг'

    pattern_url = r'(.*)(.pdf$|.doc$|.docx$|.jpg$|.xml$|.xlsx$|.xls$)'
    result_url = re.search(pattern_url, url)
    # If we find some link that refers to some file,
    # then we skip this link and go to the next
    if result_url:
        count_of_parsed_page+=1
        return
    
    try:
        # Search for head tag
        head = str(soup.head)
    except Exception:
        head = 'Такого тега нету'

    try:
        # Search for h1 tag
        h1 = soup.find_all('h1')[0].get_text().strip()
    except IndexError:
        h1 = 'Такого тега нету'

    try:
         # Search for h2 tag
        h2 = soup.find_all('h2')[0].get_text().strip()
    except IndexError:
        h2 = 'Такого тега нету'

    try:
         # Search for h3 tag
        h3 = soup.find_all('h3')[0].get_text().strip()
    except IndexError:
        h3 = 'Такого тега нету'

    def clean(string):
        # Clear tags from transitions to another line.
        # Remove special characters from tags. Turn a string into a list
        # and convert to a new string, but without extra spaces
        replace_result = re.sub(r'[\\.]+', ' ', string)
        result = ' '.join(replace_result.split())
        return result

    def clean_head(head):
        # Удаляет теги <script> и <style> в теге head
        result = re.sub("[/\n/\t/\r]+", '', head) # Remove special characters
        head_soup = BS(result, 'lxml')
        if head_soup.script:
            head_soup.script.decompose()
        if head_soup.style:
            head_soup.style.decompose()
        return re.sub("[/\n/\t/\r]+", '', str(head_soup)) # Remove special characters

    page = {
        'Url': url,
        'Description': f"{clean(description)}" if len(description) > 0 else 'Пустой тэг',
        'H1': f"{clean(h1)}" if len(h1) > 0 else 'Пустой тэг',
        'h2': f"{clean(h2)}" if len(h2) > 0 else 'Пустой тэг',
        'h3': f"{clean(h3)}" if len(h3) > 0 else 'Пустой тэг',
        'head': clean_head(head) if len(head) > 0 else 'Пустой тэг',
        'keywords': f"{clean(keywords)}" if len(keywords) > 0 else 'Пустой тэг',
    }
    pages.append(page)
    count_of_parsed_page+=1
    print('\rYou have finished %3d%%' % (count_of_parsed_page * 100 / url_count), end='', flush=True)


def main():
    # Open the file and write the column names. Only columns name. We will record the data after reading
    with open('Data_Search_Stomatology.csv', mode='w', encoding='utf-16', newline='') as csv_:
        field = ['Url', 'Description',
                 'H1', 'h2', 'h3', 'head', 'keywords']
        file_ = csv.DictWriter(csv_, fieldnames=field, delimiter=',')
        file_.writeheader()
    # Get all the links from the file 'Search_Stomatology.csv'
    links = get_all_links()
    # Use 40 threads
    with ThreadPool(40) as tp:
        tp.map(make_all, links)

    # Write the received data to the file 'Data-Search_Stomatology.csv'
    with open('Data_Search_Stomatology.csv', encoding='UTF-16', mode='a', newline='') as csv_file:
        fieldnames = ['Url', 'Description',
                      'H1', 'h2', 'h3', 'head', 'keywords']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=',')
        for page in pages:
            writer.writerow(page)
    print('\rYou have finished %3d%%' % (count_of_parsed_page * 100 / url_count), end='', flush=True)


if __name__ == "__main__":
    main()
