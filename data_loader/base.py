# -*- coding: utf-8 -*-
import json
import asyncio
import itertools as it
from os import makedirs
from os.path import join, exists
from uuid import uuid4
from time import sleep
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup


class ArticleLoader:

    NAME = 'article'

    PREPARE = 'prepare'
    LOAD = 'load'
    KILL = 'kill'

    def __init__(self, *, year, host, url_template, save, path, timeout, queue_maxsize, n_processes,
                 log_file_path=None):
        """
        Base class for loading articles from resources, that have one day articles structure.
        Needs to define methods "get_article_text" and "prepare_one_day_articles" with signature, that they have.

        :param int or str year: year for loading
        :param str host: resource host
        :param str url_template: template for url, where articles are being. example: '/news/{year}/{month}/{day}/'
        :param bool save: True/False - save json or not
        :param str path: abs path of directory for saving data
        :param int timeout: timeout in seconds for waiting before requesting to server
        :param int queue_maxsize: maxsize of queue for tasks
        :param int n_processes: processes count
        :param optional log_file_path: abs path of file for saving logs;
            default path: /tmp/data-loader/<name><year>-<H>:<M>:<S>-<d>.<m>.<Y>.log
        """
        self.year = int(year)
        self.save = save
        self.path = path
        self.host = host
        self.timeout = timeout
        self.n_processes = n_processes
        self.url_template = url_template

        self.url_cache = set()
        self.articles = []
        self.queue = asyncio.Queue(maxsize=queue_maxsize)

        self.preparing_progress = 0
        self.preparing_end = 0

        self.loading_progress = 0
        self.loading_end = 0

        self.base_path = '/tmp/data-loader'
        if not exists(self.base_path):
            makedirs(self.base_path)

        name = f'{self.NAME}{year}-{datetime.now().strftime("%H:%M:%S-%d.%m.%Y")}'

        if path:
            self.data_path = path
        else:
            self.data_path = join(self.base_path, name)
            if not exists(self.data_path) and save:
                makedirs(self.data_path)

        self.log_path = log_file_path if log_file_path else join(
            self.base_path, f'{name}.log')

    async def prepare_one_day_articles(self, soup,  year, month, day):
        """
        :return: list of dicts {'url': <url>, 'header': <header>}
        """
        raise NotImplementedError

    async def get_article_text(self, soup):
        """
        :return: str text
        """
        raise NotImplementedError

    async def prepare(self):
        print(f'\nPreparing to load {self.NAME} {self.year}...')

        all_dates = []
        for day, month, year in it.product(range(1, 32), range(1, 13), range(self.year, self.year + 1)):
            try:
                if datetime(year=year, month=month, day=day) > datetime.now():
                    raise ValueError
            except ValueError:
                continue
            day = str(day) if len(str(day)) == 2 else f'0{day}'
            month = str(month) if len(str(month)) == 2 else f'0{month}'
            year = str(year)
            all_dates.append([day, month, year])

        self.preparing_end = len(all_dates)

        for day, month, year in all_dates:
            url = self.url_template.format(year=year, month=month, day=day)

            if url in self.url_cache:
                continue

            await self.queue.put((self.PREPARE, (url, year, month, day)))

        for _ in range(self.n_processes):
            await self.queue.put((self.KILL, None))

    async def load(self):
        print('\nLoading...')
        self.loading_end = len(self.articles)

        for i, article in enumerate(self.articles):
            # print(f'\r{progress} from {end} articles', end='')

            url = article['url']
            if url in self.url_cache:
                continue

            await self.queue.put((self.LOAD, (url, i)))

        for _ in range(self.n_processes):
            await self.queue.put((self.KILL, None))

    async def get(self):
        while True:
            command, data = await self.queue.get()
            if command == self.PREPARE:
                await self.get_prepare(*data)
            elif command == self.LOAD:
                await self.get_load(*data)
            else:
                break

    async def get_prepare(self, url, year, month, day):

        self.preparing_progress += 1

        soup = await self.get_soup(url)
        if not soup:
            await self._log('PREPARING_ERROR', f'No soup for url "{url}"')
            return

        self.url_cache.add(url)
        one_day_articles = await self.prepare_one_day_articles(soup, year, month, day)
        if not one_day_articles:
            await self._log('PREPARING_WARNING', f'Articles was not found from url "{url}"')
            return

        for one_day_article in one_day_articles:
            self.articles.append({
                'url': one_day_article['url'],
                'header': one_day_article['header'],
                'date': f'{day}.{month}.{year}',
                'text': ''
            })

        print(f'\r{self.preparing_progress} from {self.preparing_end} days', end='')
        if self.preparing_progress == self.preparing_end:
            print(f'\nPreparing {self.NAME} {self.year} finished!\n')

    async def get_load(self, url, i):

        self.loading_progress += 1

        soup = await self.get_soup(url)
        if not soup:
            await self._log('WARNING', f'No soup for url "{url}"')
            return

        text = await self.get_article_text(soup)
        if not text:
            await self._log('WARNING', f'No text for url "{url}"')
            return

        self.articles[i]['text'] = text

        if self.save:
            name = f'{uuid4()}.json'
            self.save_json(self.articles[i], name)
            await self._log('INFO', f'Article with url "{url}" was saved as "{name}".')

        print(f'\r{self.loading_progress} from {self.loading_end} articles', end='')
        if self.loading_progress == self.loading_end:
            print(f'\nLoading {self.NAME} {self.year} finished!\n')

    async def get_soup(self, url):
        sleep(self.timeout)
        try:
            async with aiohttp.ClientSession() as session:
                raw_response = await session.get(url=f'{self.host}{url}')
                if raw_response.status != 200:
                    print('Bad status! Use correct timeout.')
                    await self._log('ERROR', f'Bad status from server! "{url}"')
                    return
                content = await raw_response.content.read()

            self.url_cache.add(url)
            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            await self._log('ERROR', f'{e, type(e)}')

    async def _log(self, status, msg):
        with open(self.log_path, 'a+') as logger:
            logger.write(f'{status}:{msg}\n')

    def save_json(self, article, name):
        file = open(join(self.data_path, name), 'w')
        json.dump(article, file, ensure_ascii=False)
        file.close()

    def run(self):
        """ Main method, after finished you can find data in self.articles or in folder with path <path> """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            self.prepare(), *[self.get() for _ in range(self.n_processes)]))
        loop.run_until_complete(asyncio.gather(
            self.load(), *[self.get() for _ in range(self.n_processes)]))
