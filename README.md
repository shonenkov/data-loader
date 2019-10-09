# Data Loader #

[![Build Status](https://api.travis-ci.com/shonenkov/data-loader.svg)](https://travis-ci.com/shonenkov/data-loader)
[![Coverage Status](https://coveralls.io/repos/github/shonenkov/data-loader/badge.svg)](https://coveralls.io/github/shonenkov/data-loader)

# Installing for version 0.0.1: #
```
pip install -e git+https://github.com/shonenkov/data-loader@v0.3.0#egg=data_loader-0.3.0
```



## Starting of loading MAIL RU (see `runners/run_mail_ru.py` ):
```
from data_loader import AnswerMailRuLoader

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
```