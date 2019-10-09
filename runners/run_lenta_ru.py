# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.getcwd())

from data_loader import LentaRuLoader  # noqa


if __name__ == '__main__':

    years = [2019]
    data_folder_path = 'lenta_ru'
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)

    for year in years:
        year_path = os.path.join(data_folder_path, str(year))
        if not os.path.exists(year_path):
            os.makedirs(year_path)
        bank = LentaRuLoader(year=year, data_folder_path=year_path)
        bank.run()
