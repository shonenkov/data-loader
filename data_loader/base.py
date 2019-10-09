# -*- coding: utf-8 -*-
import json
import asyncio
import itertools as it
from os import makedirs
from os.path import join, exists, basename, dirname
from glob import glob
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

    def __init__(self, *, year, host, url_template, save, data_folder_path, timeout, queue_maxsize, n_processes,
                 log_file_path=None):
        """
        Base class for loading articles from resources, that have one day articles structure.
        Needs to define methods "get_article_text" and "prepare_one_day_articles" with signature, that they have.

        :param int or str year: year for loading
        :param str host: resource host
        :param str url_template: template for url, where articles are being. example: '/news/{year}/{month}/{day}/'
        :param bool save: True/False - save json or not
        :param str data_folder_path: abs path of directory for saving data
        :param int timeout: timeout in seconds for waiting before requesting to server
        :param int queue_maxsize: maxsize of queue for tasks
        :param int n_processes: processes count
        :param optional log_file_path: abs path of file for saving logs;
            default path: /tmp/data-loader/<name><year>-<H>:<M>:<S>-<d>.<m>.<Y>.log
        """
        self.year = int(year)
        self.save = save
        self.data_folder_path = data_folder_path
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

        if data_folder_path:
            self.data_path = data_folder_path
        else:
            self.data_path = join(self.base_path, name)
            if not exists(self.data_path) and save:
                makedirs(self.data_path)

        self.log_path = log_file_path if log_file_path else join(
            self.base_path, f'{name}.log')

    async def prepare(self):
        print(f'\nPreparing to load {self.NAME} {self.year}...')

        all_dates = self._get_all_dates()
        self.preparing_end = len(all_dates)

        for day, month, year in all_dates:
            url = self.url_template.format(year=year, month=month, day=day)
            if url in self.url_cache:
                self.preparing_progress += 1
                continue

            await self.queue.put((self.PREPARE, (url, year, month, day)))

        for _ in range(self.n_processes):
            await self.queue.put((self.KILL, None))

    async def load(self):
        print('\nLoading...')
        self.loading_end = len(self.articles)

        for i, article in enumerate(self.articles):
            url = article['url']
            if url in self.url_cache:
                self.loading_progress += 1
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

    async def prepare_one_day_articles(self, soup,  year, month, day):
        """
        :return: list of dicts {'url': <url>, 'header': <header>}
        """
        raise NotImplementedError

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

        if self.preparing_progress < self.preparing_end:
            print(f'\r{self.preparing_progress} from {self.preparing_end} days', end='')
        elif self.preparing_progress == self.preparing_end:
            self.preparing_progress += 1
            print(f'\nPreparing {self.NAME} {self.year} finished!\n')

    async def get_article_text(self, soup):
        """
        :return: str text
        """
        raise NotImplementedError

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
            self._save_json(self.articles[i], name)
            await self._log('INFO', f'Article with url "{url}" was saved as "{name}".')

        if self.loading_progress < self.loading_end:
            print(f'\r{self.loading_progress} from {self.loading_end} articles', end='')
        elif self.loading_progress == self.loading_end:
            self.loading_progress += 1
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

    def _get_all_dates(self):
        all_dates = []
        for day, month, year in it.product(range(1, 32), range(1, 13), range(self.year, self.year + 1)):
            try:
                if datetime(year=year, month=month, day=day) > datetime.now():
                    raise ValueError
            except ValueError:
                continue
            day = str(day).zfill(2)
            month = str(month).zfill(2)
            year = str(year)
            all_dates.append([day, month, year])
        return all_dates

    def _save_json(self, article, name):
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


class DataExternalIDLoader:

    NAME = 'data_external_id'

    LOAD = 'load'
    KILL = 'kill'

    def __init__(self, *, ids, sub_url, save, bs4_features, data_folder_path, data_folder_deep, queue_maxsize,
                 n_processes, log_file_path=None):
        """
        Base class for loading data from external_id, that have one page structure.
        :param ids: iterable object with ids
        :param sub_url: template url with external_id, example: 'https://otvet.mail.ru/question/{external_id}'
        :param save: bool, True - save data, False - don't
        :param bs4_features: 'lxml'/'html'
        :param data_folder_path: folder for load data
        :param data_folder_deep: 1000**n, n - count of separation data
        :param queue_maxsize: maxsize of queue for tasks
        :param n_processes: processes count
        :param log_file_path: default as {NAME}.log
        """

        self.data_folder_path = data_folder_path
        self.data_folder_deep = data_folder_deep
        self.bs4_features = bs4_features
        self.n_processes = n_processes
        self.ids = ids
        self.loaded_external_ids = {basename(path)[:-5] for path in glob(
            join(data_folder_path, *['*' for _ in range(data_folder_deep)], '*.json')
        )}
        self.save = save
        self.loading_progress = 0
        self.queue = asyncio.Queue(maxsize=queue_maxsize)
        self.sub_url = sub_url
        self.log_path = log_file_path if log_file_path else f'{self.NAME}.log'

    async def load(self):
        print('\nLoading...')

        for external_id in self.ids:
            print(self.loading_progress, end='\r')
            if external_id in self.loaded_external_ids:
                self.loading_progress += 1
                continue
            await self.queue.put((self.LOAD, (external_id,)))

        for _ in range(self.n_processes):
            await self.queue.put((self.KILL, None))

    async def get(self):
        while True:
            command, data = await self.queue.get()
            if command == self.LOAD:
                await self.get_load(*data)
            else:
                break

    async def get_data(self, external_id, soup):
        """ Method for parse data from soup. Return JSON  """
        raise NotImplementedError

    async def get_load(self, external_id):

        self.loading_progress += 1

        soup = await self.get_soup(external_id)
        if not soup:
            await self._log('WARNING', f'No soup for external_id "{external_id}"')
            return

        data = await self.get_data(external_id, soup)
        if not data:
            await self._log('WARNING', f'No text for external_id "{external_id}"')
            return

        if self.save:
            name = [f'{external_id}.json']
            for _ in range(self.data_folder_deep):
                name.append(str(external_id // 1000 % 1000))
                external_id = external_id // 1000

            path = join(*name[::-1])
            sub_folder_path = dirname(join(self.data_folder_path, path))
            if not exists(sub_folder_path):
                makedirs(sub_folder_path)

            self._save_json(data, path)
            await self._log('INFO', f'Data saved as "{path}".')

    async def get_soup(self, external_id):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=self.sub_url.format(external_id=external_id), verify_ssl=False) \
                        as raw_response:
                    if raw_response.status == 404:
                        await session.close()
                        return
                    elif raw_response.status != 200:
                        print('Bad status! Use correct timeout.')
                        await self._log('ERROR', f'Bad status from server! "{external_id}"')
                        await session.close()
                        return
                    content = await raw_response.content.read()

            self.loaded_external_ids.add(external_id)
            return BeautifulSoup(content, self.bs4_features)
        except Exception as e:
            await self._log('ERROR', f'{e, type(e)}')

    async def _log(self, status, msg):
        with open(self.log_path, 'a+') as logger:
            logger.write(f'{status}:{msg}\n')

    def _save_json(self, article, name):
        file = open(join(self.data_folder_path, name), 'w')
        json.dump(article, file, ensure_ascii=False)
        file.close()

    def run(self):
        """ Main method """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(
            self.load(), *[self.get() for _ in range(self.n_processes)]))
