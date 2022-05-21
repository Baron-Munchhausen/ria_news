import requests
import datetime
from bs4 import BeautifulSoup
# https://github.com/nithinmurali/pygsheets
import pygsheets
import configparser

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

ria = 'https://ria.ru/services/economy/more.html?date='
ria = 'https://ria.ru/services/search/getmore/?query=&offset='
offset = 0
not_end = True
current_datetime = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
#current_datetime = datetime.datetime(2022,5,12,9,0).strftime('%Y%m%dT%H%M%S')

articles = []

while not_end:

    url_for_request = ria + current_datetime
    url_for_request = ria + str(offset)

    req = requests.get(url_for_request, headers=headers)
    soup = BeautifulSoup(req.text, 'lxml')

    for item in soup.find_all('div', attrs={'class': 'list-item'}):
        url = item.find_all('a', attrs={'class': 'list-item__title color-font-hover-only'})[0].attrs['href']
        try:
            req2 = requests.get(url, headers=headers)
            soup2 = BeautifulSoup(req2.text, 'lxml')

            createdAt = soup2.find_all('div', attrs={'class': 'article__info-date'})[0].find_all('a')[0].next
            createdAt_datetime = datetime.datetime.strptime(createdAt, '%H:%M %d.%m.%Y')

            title = str(soup2.find_all(['div', 'h1'], attrs={'class': 'article__title'})[0]).replace(
            '<div class="article__title">', '').replace('<h1 class="article__title">', '').replace('</div>', '')
            author = str(soup2.find_all('meta', attrs={'name': 'analytics:author'})).replace('[<meta content="',
                                                                                         '').replace(
            '" name="analytics:author"/>]', '')
        except:
            error_wks.insert_rows(0, 1, [url])

        if createdAt_datetime >= last_datetime and url != last_url and createdAt_datetime <= datetime.datetime.now():
            article = {'title': title, 'url': url, 'author': author, 'createdAt': createdAt, 'createdAt_datetime': createdAt_datetime}
            print(article)
            articles.append(article)
        elif createdAt_datetime < last_datetime:
            not_end = False

    current_datetime = createdAt_datetime.strftime('%Y%m%dT%H%M59')
    offset += 20
    # not_end = False


articles_distinct = {v['url']: v for v in articles}.values()
articles_sorted = sorted(articles_distinct, key=lambda d: d['createdAt_datetime'])

for article in articles_sorted:
    wks.insert_rows(0, 1, [article['title'], article['url'], article['author'], article['createdAt']])


#x = name
#        for attr in dir(x):
#            if not attr.startswith('_'):  # Если не внутренний и не служебный
#                print(attr)
#                print(getattr(x, attr))
#        print('------')