# -*- coding: utf-8 -*-
from os.path import join

import pytest
from bs4 import BeautifulSoup

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
