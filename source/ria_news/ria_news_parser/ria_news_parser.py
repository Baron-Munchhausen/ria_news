import requests
import datetime
from bs4 import BeautifulSoup
import pygsheets  # https://github.com/nithinmurali/pygsheets
import configparser
from requests_html import HTMLSession


def get_article_statistics(_url):

    session = HTMLSession()

    attempt = 0

    while attempt < 3:
        response = session.get(_url, timeout=10000)
        response.html.render()
        article_soup = BeautifulSoup(response.html.html, 'lxml')
        result = article_soup.find_all('div', attrs={'class': 'article__info-statistic'})
        if len(result[0].text) > 0:
            session.close()
            try:
                article_views = int(result[0].text)
                return article_views
            except ValueError:
                continue
        attempt += 1
    session.close()
    return 0


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

        article_statistics = get_article_statistics(url)
        if article_statistics > 0:
            _wks.update_value(('E' + str(n)), article_statistics)

        print(str(n) + ' ' + url + ' ' + str(article_statistics))


def download_new_articles(_wks, _error_wks):

    # Last downloaded articles
    last_datetime = datetime.datetime.strptime(wks.get_value('D1'), '%H:%M %d.%m.%Y')
    last_urls = []
    n = 0
    while True:
        n += 1
        if datetime.datetime.strptime(wks.get_value('D' + str(n)), '%H:%M %d.%m.%Y') == last_datetime:
            last_urls += wks.get_value('B' + str(n))
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
                article_statistics = get_article_statistics(url)
                req2 = requests.get(url, headers=headers)
                soup2 = BeautifulSoup(req2.text, 'lxml')

                created_at = soup2.find_all('div', attrs={'class': 'article__info-date'})[0].find_all('a')[0].next
                created_at_datetime = datetime.datetime.strptime(created_at, '%H:%M %d.%m.%Y')

                title = str(soup2.find_all(['div', 'h1'], attrs={'class': 'article__title'})[0]).replace(
                    '<div class="article__title">', '').replace('<h1 class="article__title">', '').replace('</div>', '')
                author = str(soup2.find_all('meta', attrs={'name': 'analytics:author'})).replace('[<meta content="',
                                                                                                 '').replace(
                    '" name="analytics:author"/>]', '')
                if last_datetime <= created_at_datetime <= datetime.datetime.now() and url not in last_urls:
                    article = {'title': title, 'url': url, 'author': author, 'created_at': created_at,
                               'createdAt_datetime': created_at_datetime, 'article_statistics': article_statistics}
                    print(article)
                    articles.append(article)
                elif created_at_datetime < last_datetime:
                    not_end = False
            except:
                error_wks.insert_rows(0, 1, [url])

        offset += 20

    articles_distinct = {v['url']: v for v in articles}.values()
    articles_sorted = sorted(articles_distinct, key=lambda d: d['createdAt_datetime'])

    for article in articles_sorted:
        wks.insert_rows(0, 1, [article['title'], article['url'], article['author'], article['created_at'],
                               article['article_statistics']])


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

# Update view statistic
update_view_statistics(wks, 2400)

# Download new articles
download_new_articles(wks, error_wks)
