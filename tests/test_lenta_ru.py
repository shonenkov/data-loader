# -*- coding: utf-8 -*-
import pytest
import asyncio
from os.path import join

from bs4 import BeautifulSoup

from data_loader import LentaRuLoader
from .conftest import TEST_ROOT


@pytest.mark.asyncio
@pytest.mark.parametrize('soup_path, expected_text_path', [
    ('soup0.html', 'soup0.txt'),
    ('soup1.html', 'soup1.txt'),
    ('soup2.html', 'soup2.txt'),
    ('soup3.html', 'soup3.txt'),
    ('soup4.html', 'soup4.txt'),
])
async def test_get_article_text(soup_path, expected_text_path, lenta_ru_loader):
    soup_path = join(TEST_ROOT, f'resources/lenta_ru/soups/{soup_path}')
    expected_text_path = join(
        TEST_ROOT, f'resources/lenta_ru/article_texts/{expected_text_path}')
    soup = BeautifulSoup(open(soup_path, 'r'), 'html.parser')
    expected_text = open(expected_text_path, 'r').read()
    text = await lenta_ru_loader.get_article_text(soup)
    assert text.strip() == expected_text.strip()


@pytest.mark.asyncio
async def test_lentaru_loader():
    async def my_get_soup(url):
        return BeautifulSoup(
            open(f'/tmp/test-data-loader-resources/articles/{url.replace("/", "-")}.html', 'r'), 'html.parser'
        )

    def _my_get_all_dates():
        return [('02', '07', '2018')]

    lenta_ru = LentaRuLoader(year=2018, save=False)
    lenta_ru.get_soup = my_get_soup
    lenta_ru._get_all_dates = _my_get_all_dates

    await asyncio.gather(
        lenta_ru.prepare(), *[lenta_ru.get() for _ in range(lenta_ru.n_processes)]
    )
    await asyncio.gather(
        lenta_ru.load(), *[lenta_ru.get() for _ in range(lenta_ru.n_processes)]
    )

    assert len(lenta_ru.articles) == 200
    for article in lenta_ru.articles:
        assert article['text']
        assert article['date'] == '02.07.2018'
        assert article['url']
        assert article['header']
