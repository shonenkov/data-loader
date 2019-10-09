# -*- coding: utf-8 -*-
from .base import DataExternalIDLoader


class AnswerMailRuLoader(DataExternalIDLoader):

    def __init__(self, *, ids, save, data_folder_path, queue_maxsize, n_processes):
        """
        Async multiprocessing loader of Answer Mail Ru

        :param ids: iterable object with ids
        :param save: bool, True - save data, False - don't
        :param data_folder_path: folder for load data
        :param queue_maxsize: maxsize of queue for tasks
        :param n_processes: processes count
        """
        super().__init__(
            ids=ids,
            sub_url='https://otvet.mail.ru/question/{external_id}',
            save=save,
            bs4_features='lxml',
            data_folder_path=data_folder_path,
            data_folder_deep=2,
            queue_maxsize=queue_maxsize,
            n_processes=n_processes
        )

    async def get_data(self, external_id, soup):

        title = soup.find('h1', 'q--qtext').text.strip()
        raw_comments = soup.find_all('div', 'q--qcomment medium')
        comments = []
        if raw_comments:
            comments = [q.text.strip() for q in raw_comments]

        category = soup.find('a', 'black list__title list__title')
        sub_category = soup.find('a', 'medium item item_link selected')

        if category is not None:
            category = category.text.strip()
        if sub_category is not None:
            sub_category = sub_category.text.strip()

        raw_answers = soup.find_all('div', 'a--atext atext')
        answers = []
        if raw_answers:
            answers = [a.text.strip() for a in raw_answers]

        return {'id': str(external_id), 'title': title, 'category': category, 'sub_category': sub_category,
                'comments': comments, 'answers': answers}
