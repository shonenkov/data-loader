# -*- coding: utf-8 -*-
from .base import ArticleLoader


class BankiRuLoader(ArticleLoader):

    NAME = 'banki'

    HOST = 'http://www.banki.ru'
    DEFAULT_URL_TEMPLATE = '/news/lenta/?d={day}&m={month}&y={year}'

    def __init__(self, year, save=True, data_folder_path=None, log_file_path=None, timeout=1, host=HOST,
                 url_template=DEFAULT_URL_TEMPLATE, queue_maxsize=1, n_processes=1):
        super().__init__(year=year, host=host, url_template=url_template, save=save, data_folder_path=data_folder_path,
                         timeout=timeout, queue_maxsize=queue_maxsize, n_processes=n_processes,
                         log_file_path=log_file_path)

    async def prepare_one_day_articles(self, soup,  year, month, day):
        """
        :return: list of dict {'url': <url>, 'header': <header>}
        """
        all_a = soup.find_all('a')
        if not all_a:
            return

        one_day_articles = []
        for a in all_a:
            if 'text-list-link' in a.attrs.get('class', []) and a['href'].startswith('/news/lenta/'):
                one_day_articles.append({
                    'url': a['href'],
                    'header': a.text,
                })

        return one_day_articles

    async def get_article_text(self, soup):
        """
        :return: str text
        """
        for a in soup.find_all('article'):
            if 'article-text' in a.attrs.get('class', []):
                return a.text
