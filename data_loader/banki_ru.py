import json
import asyncio
import itertools as it
import logging
from os import makedirs
from os.path import join
from uuid import uuid4
from time import sleep
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup


class BankiRuLoader:

    TIMEOUT = 0.1
    HOST = 'http://www.banki.ru'

    def __init__(self, year, save=True, path='/tmp/data-loader', timeout=TIMEOUT):
        """
        :param int year: year for downloading news:
        :param save:
        :param path:
        :param timeout:
        """
        self.timeout = timeout
        self.year = year
        self.save = save

        self.all_dates = []
        for day, month, year in it.product([i for i in range(1, 32)], [i for i in range(1, 13)],
                                           [i for i in range(self.year, self.year+1)]):
            try:
                if datetime(year=year, month=month, day=day) > datetime.now():
                    raise ValueError
            except ValueError:
                continue
            day = str(day)
            month = str(month)
            year = str(year)
            self.all_dates.append([day if len(day) == 2 else "0" + str(day),
                                   month if len(month) == 2 else "0" + str(month),
                                   year])

        self.all_news = []
        self.all_got_urls = set()
        self.progress = 0

        self.data_path = join(path, f'bankiru{year}-{datetime.now().strftime("%H:%M:%S-%d.%m.%Y")}')

        makedirs(self.data_path)
        logging.basicConfig(filename=f'{self.data_path}.log', level=logging.INFO)
        logging.info(f'Was created directory "{self.data_path}"')

    async def get_soup(self, url):
        sleep(self.TIMEOUT)
        try:
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url=f'{self.HOST}{url}')
                content = await raw_response.content.read()

            self.all_got_urls.add(url)
            return BeautifulSoup(content, "html.parser")
        except Exception as e:
            logging.error(f'{e, type(e)}')

    @staticmethod
    async def get_text_from_news(soup):
            for a in soup.find_all('article'):
                if "article-text" in a.attrs.get('class', []):
                    return a.text

    async def parse_one_day_news(self, url, day, month, year):
        self.progress += 1
        if self.progress % round(len(self.all_dates) / 100) == 0:
            print(f'{(self.progress / len(self.all_dates)):.2f}')
        soup = await self.get_soup(url)
        if not soup:
            logging.warning(f'No soup: {url}')
            return

        all_a = soup.find_all('a')
        if not all_a:
            logging.warning(f'News was not found from: {url}')
            return

        for a in all_a:
            if "text-list-link" in a.attrs.get('class', []):
                news_url = a['href']
                if news_url in self.all_got_urls:
                    continue

                soup = await self.get_soup(news_url)
                if not soup:
                    logging.warning(f'No soup: {news_url}')
                    continue

                text = await self.get_text_from_news(soup)
                if not text:
                    logging.warning(f'News {news_url} was downloaded early.')
                    continue

                self.all_got_urls.add(news_url)

                news = {
                    'url': news_url,
                    'header': a.text,
                    'date': f'{day}.{month}.{year}',
                    'text': text
                }

                self.all_news.append(news)
                if self.save:
                    name = f'{uuid4()}.json'
                    self.save_json(news, name)
                    logging.info(f'News {news_url} was saved as {name}.')

    async def parse_news(self):
        for i, (day, month, year) in enumerate(self.all_dates):
            url = f'/news/lenta/?d={day}&m={month}&y={year}'
            if url not in self.all_got_urls:
                await self.parse_one_day_news(url, day, month, year)

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.parse_news())

    def save_json(self, news, name):
        file = open(join(self.data_path, name), 'w')
        json.dump(news, file, ensure_ascii=False)
        file.close()
