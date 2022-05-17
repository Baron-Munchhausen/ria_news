import requests
import datetime
from bs4 import BeautifulSoup
import pygsheets

client = pygsheets.authorize(service_file='service.json')
sheets = client.open_by_url('https://docs.google.com/spreadsheets/d/1Gkb12I1E21XLNKjA52cNSV-W7IWdXgoyghP12jmkwNk')
wks = sheets.worksheet_by_title('Лист1')

last_datetime = datetime.datetime.strptime(wks.get_value('D1'), '%H:%M %d.%m.%Y')

if __name__ == '__main__':
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}

    ria = 'https://ria.ru/services/economy/more.html?date='
    not_end = True
    current_datetime = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

    articles = []
    while not_end:

        url_for_request = ria + current_datetime

        req = requests.get(url_for_request, headers=headers)
        soup = BeautifulSoup(req.text, 'lxml')

        for item in soup.find_all('div', attrs={'class': 'list-item'}):
            url = item.find_all('a', attrs={'class': 'list-item__title color-font-hover-only'})[0].attrs['href']

            req2 = requests.get(url, headers=headers)
            soup2 = BeautifulSoup(req2.text, 'lxml')
            title = str(soup2.find_all(['div', 'h1'], attrs={'class': 'article__title'})[0]).replace(
                '<div class="article__title">', '').replace('<h1 class="article__title">', '').replace('</div>', '')
            author = str(soup2.find_all('meta', attrs={'name': 'analytics:author'})).replace('[<meta content="',
                                                                                             '').replace(
                '" name="analytics:author"/>]', '')
            createdAt = soup2.find_all('div', attrs={'class': 'article__info-date'})[0].find_all('a')[0].next
            createdAt_datetime = datetime.datetime.strptime(createdAt, '%H:%M %d.%m.%Y')
            if createdAt_datetime > last_datetime:
                article = {'title': title, 'url': url, 'author': author, 'createdAt': createdAt}
                print(article)
                articles.append(article)
            else:
                not_end = False
        current_datetime = createdAt_datetime.strftime('%Y%m%dT%H%M59')
        # not_end = False

    articles = {v['url']:v for v in articles}.values()
    articles = sorted(articles, key=lambda d: d['createdAt'])

    for article in articles:
        wks.insert_rows(0, 1, [article['title'], article['url'], article['author'], article['createdAt']])