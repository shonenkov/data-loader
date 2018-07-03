# -*- coding: utf-8 -*-
from .base import ArticleLoader


class LentaRuLoader(ArticleLoader):

    NAME = 'lenta'

    HOST = 'https://lenta.ru'
    DEFAULT_URL_TEMPLATE = '/news/{year}/{month}/{day}/'

    def __init__(self, year, save=True, path=None, log_file_path=None, timeout=0,
                 host=HOST, url_template=DEFAULT_URL_TEMPLATE, queue_maxsize=200, n_processes=10):
        super().__init__(year=year, host=host, url_template=url_template, save=save, path=path, timeout=timeout,
                         queue_maxsize=queue_maxsize, n_processes=n_processes, log_file_path=log_file_path)

    async def prepare_one_day_articles(self, soup,  year, month, day):
        """
        :return: list of dict {'url': <url>, 'header': <header>}
        """
        one_day_articles = []
        for div in soup.find_all('div', attrs='b-tabloid__topic_news'):
            a = div.a
            url = a['href']
            if f'/{year}/{month}/' in url:
                one_day_articles.append({
                    'url': url,
                    'header': a.text,
                })

        return one_day_articles

    async def get_article_text(self, soup):
        """
        :return: str text
        """
        text = ''
        for div in soup.find_all('div', attrs=['b-text']):
            if div['itemprop'] == 'articleBody':
                text = f'{text} {div.text}'

        return text
