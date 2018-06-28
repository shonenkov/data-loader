import json
import asyncio
import itertools as it
from os import makedirs
from os.path import join, exists, dirname
from uuid import uuid4
from time import sleep
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

LIB_ROOT = dirname(__file__)


class BankiRuLoader:

    TIMEOUT = 1
    HOST = 'http://www.banki.ru'

    def __init__(self, year, save=True, path=None, log_file_path=None, timeout=TIMEOUT):
        """
        :param int year: year for downloading news, recommend >= 2005
        :param bool save: save data or not; in case False you can find data in self.all_news if it is necessary
        :param str path: folder path for save json files with data
        :param int timeout: delay between requests to server
        """
        self.timeout = timeout
        self.year = year
        self.save = save

        self.all_dates = []
        for day, month, year in it.product(range(1, 32), range(1, 13), range(self.year, self.year + 1)):
            try:
                if datetime(year=year, month=month, day=day) > datetime.now():
                    raise ValueError
            except ValueError:
                continue
            day = str(day) if len(str(day)) == 2 else f"0{day}"
            month = str(month) if len(str(month)) == 2 else f"0{month}"
            year = str(year)
            self.all_dates.append([day, month, year])

        self.all_news = []
        self.all_got_urls = set()
        self.progress = 0

        self.base_path = '/tmp/data-loader'
        if not exists(self.base_path):
            makedirs(self.base_path)

        name = f'bankiru{year}-{datetime.now().strftime("%H:%M:%S-%d.%m.%Y")}'

        if path:
            self.data_path = path
        else:
            self.data_path = join(self.base_path, name)
            if not exists(self.data_path) and save:
                makedirs(self.data_path)

        self.log_path = log_file_path if log_file_path else join(self.base_path, f'{name}.log')

    def run(self):
        """ Main method, after finished you can find data in self.all_news or in folder with path <path> """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.parse_news())

    async def get_soup(self, url):
        sleep(self.TIMEOUT)
        try:
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url=f'{self.HOST}{url}')
                if raw_response.status != 200:
                    print('Bad status! Use correct timeout.')
                    await self._log('ERROR', f'Bad status from server! "{url}"')
                    return
                content = await raw_response.content.read()

            self.all_got_urls.add(url)
            return BeautifulSoup(content, "html.parser")
        except Exception as e:
            await self._log('ERROR', f'{e, type(e)}')

    @staticmethod
    async def get_text_from_news(soup):
            for a in soup.find_all('article'):
                if "article-text" in a.attrs.get('class', []):
                    return a.text

    async def parse_one_day_news(self, url, day, month, year):
        self.progress += 1
        if self.progress % round(len(self.all_dates) / 100) == 0:
            print(f'{round(self.progress / len(self.all_dates) * 100)}%')
        soup = await self.get_soup(url)
        if not soup:
            await self._log('WARNING', f'No soup for url "{url}"')
            return

        all_a = soup.find_all('a')
        if not all_a:
            await self._log('WARNING', f'News was not found from url "{url}"')
            return

        for a in all_a:
            if "text-list-link" in a.attrs.get('class', []):
                news_url = a['href']
                if news_url in self.all_got_urls:
                    continue

                soup = await self.get_soup(news_url)
                if not soup:
                    await self._log('WARNING', f'No soup for url "{news_url}"')
                    continue

                text = await self.get_text_from_news(soup)
                if not text:
                    await self._log('WARNING', f'News with url "{news_url}" was downloaded early.')
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
                    await self._log('INFO', f'News with url "{news_url}" was saved as "{name}".')

    async def parse_news(self):
        for i, (day, month, year) in enumerate(self.all_dates):
            url = f'/news/lenta/?d={day}&m={month}&y={year}'
            if url not in self.all_got_urls:
                await self.parse_one_day_news(url, day, month, year)

    async def _log(self, status, msg):
        with open(self.log_path, 'a+') as logger:
            logger.write(f'{status}:{msg}\n')

    def save_json(self, news, name):
        file = open(join(self.data_path, name), 'w')
        json.dump(news, file, ensure_ascii=False)
        file.close()
