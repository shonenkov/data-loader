# -*- coding: utf-8 -*-
import os
from os.path import dirname, exists
from os import makedirs


import pytest

from data_loader.lenta_ru import LentaRuLoader


TEST_ROOT = dirname(__file__)


@pytest.yield_fixture(scope='module')
def lenta_ru_loader():
    yield LentaRuLoader(year=2009, save=False)


@pytest.fixture(scope='session', autouse=True)
def unpack_resources():
    resources = '/tmp/test-data-loader-resources'
    if not exists(resources):
        makedirs(resources)
    os.system(f'cd {resources} && tar -xvzf {TEST_ROOT}/resources/lenta_ru/2018-07-02/articles.tar.gz')
