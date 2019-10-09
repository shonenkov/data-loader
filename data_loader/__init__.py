# -*- coding: utf-8 -*-
from . import base
from .banki_ru import BankiRuLoader
from .lenta_ru import LentaRuLoader
from .mail_ru import AnswerMailRuLoader

__all__ = ['base', 'BankiRuLoader', 'LentaRuLoader', 'AnswerMailRuLoader']
__version__ = '0.3.0'
