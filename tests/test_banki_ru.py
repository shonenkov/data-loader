# -*- coding: utf-8 -*-
import pytest
import asyncio
import re
from os.path import join

from bs4 import BeautifulSoup

from data_loader import BankiRuLoader
from tests.conftest import TEST_ROOT, WORD_PATTERN


@pytest.mark.asyncio
@pytest.mark.parametrize('soup_path, expected_text_path', [
    ('soup0.html', 'soup0.txt'),
    ('soup1.html', 'soup1.txt'),
    ('soup2.html', 'soup2.txt'),
    ('soup3.html', 'soup3.txt'),
    ('soup4.html', 'soup4.txt'),
])
async def test_get_article_text(soup_path, expected_text_path, banki_ru_loader):
    soup_path = join(TEST_ROOT, f'resources/banki_ru/soups/{soup_path}')
    expected_text_path = join(
        TEST_ROOT, f'resources/banki_ru/article_texts/{expected_text_path}')
    soup = BeautifulSoup(open(soup_path, 'r'), 'html.parser')
    expected_text = open(expected_text_path, 'r').read()
    text = await banki_ru_loader.get_article_text(soup)
    assert re.findall(WORD_PATTERN, text) == re.findall(WORD_PATTERN, expected_text)


@pytest.mark.asyncio
async def test_bankiru_loader():
    async def my_get_soup(url):
        return BeautifulSoup(
            open(f'/tmp/test-data-loader-resources/{url.replace("/", "-")}.html', 'r'), 'html.parser'
        )

    def _my_get_all_dates():
        return [('03', '07', '2018')]

    banki_ru = BankiRuLoader(year=2018, save=False)
    banki_ru.get_soup = my_get_soup
    banki_ru._get_all_dates = _my_get_all_dates

    await asyncio.gather(
        banki_ru.prepare(), *[banki_ru.get() for _ in range(banki_ru.n_processes)]
    )
    await asyncio.gather(
        banki_ru.load(), *[banki_ru.get() for _ in range(banki_ru.n_processes)]
    )

    assert len(banki_ru.articles) == 54
    for article in banki_ru.articles:
        assert article['text']
        assert article['date'] == '03.07.2018'
        assert article['url']
        assert article['header']
