import requests
import datetime
from bs4 import BeautifulSoup
import pygsheets  # https://github.com/nithinmurali/pygsheets
import configparser
from requests_html import HTMLSession


class RiaArticle:
    
    def __init__(self, url):

        self.url = url

    def get_statistics(self):
        
        session = HTMLSession()

        attempt = 0

        while attempt < 3:
            response = session.get(self.url, timeout=10000)
            # сделать зависимость таймаута от попытки
            try:
                timeout = 10 + 5 * attempt
                response.html.render(timeout=timeout)
                article_soup = BeautifulSoup(response.html.html, 'lxml')
                result = article_soup.find_all('div', attrs={'class': 'article__info-statistic'})
                if len(result[0].text) > 0:
                    try:
                        self.statistics = int(result[0].text)
                        session.close()
                        break
                    except ValueError:
                        continue
            except:
                attempt += 1
        session.close()

        if self.statistics == None:
            self.statistics = -1

    def get_info(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/41.0.2228.0 Safari/537.3'}

        self.get_statistics()
        req = requests.get(self.url, headers=headers)
        soup = BeautifulSoup(req.text, 'lxml')

        self.created_at = soup.find_all('div', attrs={'class': 'article__info-date'})[0].find_all('a')[0].next
        self.created_at_datetime = datetime.datetime.strptime(self.created_at, '%H:%M %d.%m.%Y')

        self.title = soup.find('h1', class_='article__title').text
        self.author = soup.find('div', class_='article__author-name').text


def update_view_statistics(_wks, _period):

    n = 0

    while True:
        n += 1
        url = wks.get_value('B' + str(n))
        if len(url) == 0:
            break
        created_at = datetime.datetime.strptime(_wks.get_value('D' + str(n)), '%H:%M %d.%m.%Y')
        if (datetime.datetime.now() - created_at).seconds > _period:
            break

        article = RiaArticle(url)
        article.get_statistics()
        
        if article.statistics > 0:
            _wks.update_value(('E' + str(n)), article.statistics)

        print(str(n) + ' ' + url + ' ' + str(article.statistics))


def download_new_articles(_wks, _error_wks):

    # Last downloaded articles
    last_datetime = datetime.datetime.strptime(wks.get_value('D1'), '%H:%M %d.%m.%Y')
    last_urls = []
    n = 0
    while True:
        n += 1
        if datetime.datetime.strptime(wks.get_value('D' + str(n)), '%H:%M %d.%m.%Y') == last_datetime:
            last_urls.append(wks.get_value('B' + str(n)))
        else:
            break

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/41.0.2228.0 Safari/537.3'}

    ria = 'https://ria.ru/services/search/getmore/?query=&offset='
    offset = 0
    not_end = True

    articles = []

    while not_end:

        url_for_request = ria + str(offset)

        req = requests.get(url_for_request, headers=headers)
        soup = BeautifulSoup(req.text, 'lxml')

        for item in soup.find_all('div', attrs={'class': 'list-item'}):
            url = item.find_all('a', attrs={'class': 'list-item__title color-font-hover-only'})[0].attrs['href']
            try:
                article = RiaArticle(url)
                article.get_info()
                if last_datetime <= article.created_at_datetime <= datetime.datetime.now() and url not in last_urls:
                    print(article.created_at + ' ' + article.title)
                    articles.append(article)
                elif article.created_at_datetime < last_datetime:
                    not_end = False
            except:
                error_wks.insert_rows(0, 1, [url])

        offset += 20

    articles_distinct = {v.url: v for v in articles}.values()
    articles_sorted = sorted(articles_distinct, key=lambda d: d.created_at_datetime)

    for article in articles_sorted:
        wks.insert_rows(0, 1, [article.title, article.url, article.author, article.created_at,
                               article.statistics])


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

while True:
    # Update view statistics
    update_view_statistics(wks, 2400)

    # Download new articles
    download_new_articles(wks, error_wks)
