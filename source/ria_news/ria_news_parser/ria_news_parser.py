# pip install requests bs4 pygsheets
import requests
import datetime
from bs4 import BeautifulSoup
import pygsheets


client = pygsheets.authorize(service_file='service.json')
sheets = client.open_by_url('https://docs.google.com/spreadsheets/d/1Gkb12I1E21XLNKjA52cNSV-W7IWdXgoyghP12jmkwNk')
wks = sheets.worksheet_by_title('Лист1')
