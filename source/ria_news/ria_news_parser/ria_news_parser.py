import requests
import datetime
from bs4 import BeautifulSoup
# https://github.com/nithinmurali/pygsheets
import pygsheets
import configparser
import requests_html
import asyncio
from requests_html import HTMLSession

def get_article_statistics(url):
   
    session = HTMLSession()

    attempt = 0

    while attempt < 3:
        response = session.get(url, timeout=10000)
        response.html.render()
        soup = BeautifulSoup(response.html.html, 'lxml')
        result = soup.find_all('div', attrs = {'class':'article__info-statistic'})
        if len(result[0].text) > 0:
            try:
                article_views = int(result[0].text)
                session.close()
                return article_views
            except:
                continue
        attempt += 1

    session.close()
    return 0

# config
config = configparser.ConfigParser()
config.read('config.ini')

# Google sheets
client = pygsheets.authorize(service_file='service.json')

# Google sheet with articles
sheets = client.open_by_url(config['google']['article_file'])
wks = sheets.worksheet_by_title(config['google']['article_file_sheet'])

# Google sheet with errors
error_sheets = client.open_by_url(config['google']['error_file'])
error_wks = error_sheets.worksheet_by_title(config['google']['error_file_sheet'])

# Last downloaded article
last_datetime = datetime.datetime.strptime(wks.get_value('D1'), '%H:%M %d.%m.%Y')
last_url = wks.get_value('B1')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/41.0.2228.0 Safari/537.3'}


# Update statistic
n = 0
while True:
    n += 1
    url = wks.get_value('B' + str(n))
    if len(url) == 0:
        break
    createdAt = datetime.datetime.strptime(wks.get_value('D' + str(n)), '%H:%M %d.%m.%Y')
    if (datetime.datetime.now() - createdAt).seconds > 1200:
        break
    
    article_statistics = get_article_statistics(url)
    if article_statistics > 0:
        statistics_cell = wks.update_value(('E' + str(n)),article_statistics)
    
    print(str(n) + ' ' + url + ' ' + str(article_statistics))


ria = 'https://ria.ru/services/economy/more.html?date='
ria = 'https://ria.ru/services/search/getmore/?query=&offset='
offset = 0
not_end = True
current_datetime = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

articles = []

while not_end:

    url_for_request = ria + current_datetime
    url_for_request = ria + str(offset)

    req = requests.get(url_for_request, headers=headers)
    soup = BeautifulSoup(req.text, 'lxml')

    for item in soup.find_all('div', attrs={'class': 'list-item'}):
        try:
            url = item.find_all('a', attrs={'class': 'list-item__title color-font-hover-only'})[0].attrs['href']
            article_statistics = get_article_statistics(url)
            req2 = requests.get(url, headers=headers)
            soup2 = BeautifulSoup(req2.text, 'lxml')

            createdAt = soup2.find_all('div', attrs={'class': 'article__info-date'})[0].find_all('a')[0].next
            createdAt_datetime = datetime.datetime.strptime(createdAt, '%H:%M %d.%m.%Y')

            title = str(soup2.find_all(['div', 'h1'], attrs={'class': 'article__title'})[0]).replace(
            '<div class="article__title">', '').replace('<h1 class="article__title">', '').replace('</div>', '')
            author = str(soup2.find_all('meta', attrs={'name': 'analytics:author'})).replace('[<meta content="',
                                                                                         '').replace(
            '" name="analytics:author"/>]', '')
            if createdAt_datetime >= last_datetime and url != last_url and createdAt_datetime <= datetime.datetime.now():
                article = {'title': title, 'url': url, 'author': author, 'createdAt': createdAt, 'createdAt_datetime': createdAt_datetime, 'article_statistics': article_statistics}
                print(article)
                articles.append(article)
            elif createdAt_datetime < last_datetime:
                not_end = False
        except:
            error_wks.insert_rows(0, 1, [url])



    current_datetime = createdAt_datetime.strftime('%Y%m%dT%H%M59')
    offset += 20


articles_distinct = {v['url']: v for v in articles}.values()
articles_sorted = sorted(articles_distinct, key=lambda d: d['createdAt_datetime'])

for article in articles_sorted:
    wks.insert_rows(0, 1, [article['title'], article['url'], article['author'], article['createdAt'], article['article_statistics']])