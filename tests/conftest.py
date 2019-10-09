# -*- coding: utf-8 -*-
import os
import re
from os.path import dirname, exists
from os import makedirs


import pytest

from data_loader import LentaRuLoader, BankiRuLoader


TEST_ROOT = dirname(__file__)

WORD_PATTERN = re.compile(r'\b[\w\-]+\b')


@pytest.yield_fixture(scope='module')
def lenta_ru_loader():
    yield LentaRuLoader(year=2009, save=False)


@pytest.yield_fixture(scope='module')
def banki_ru_loader():
    yield BankiRuLoader(year=2018, save=False)


@pytest.fixture(scope='session', autouse=True)
def unpack_resources():
    resources = '/tmp/test-data-loader-resources'
    if not exists(resources):
        makedirs(resources)

    os.system(f'cd {resources} && tar -xvzf {TEST_ROOT}/resources/lenta_ru/2018-07-02/lenta_ru_articles.tar.gz')
    os.system(f'cd {resources} && tar -xvzf {TEST_ROOT}/resources/banki_ru/2018-07-03/banki_ru_articles.tar.gz')
