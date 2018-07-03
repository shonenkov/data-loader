# -*- coding: utf-8 -*-
from os.path import dirname

import pytest

from data_loader.lenta_ru import LentaRuLoader


TEST_ROOT = dirname(__file__)


@pytest.yield_fixture(scope='module')
def lenta_ru_loader():
    yield LentaRuLoader(year=2009, save=False)
