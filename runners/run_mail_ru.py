# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.getcwd())

from data_loader import AnswerMailRuLoader  # noqa


if __name__ == '__main__':

    data_folder_path = 'data'
    if not os.path.exists(data_folder_path):
        os.makedirs(data_folder_path)

    mail_ru = AnswerMailRuLoader(
        ids=range(0, 1000),
        save=True,
        data_folder_path=data_folder_path,
        queue_maxsize=200,
        n_processes=10,
    )
    mail_ru.run()
