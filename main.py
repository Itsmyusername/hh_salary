import requests
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable
from contextlib import suppress


def predict_salary(salary_from, salary_to):
    if salary_from > 0 and salary_to > 0:
        mid_salary = int((salary_from + salary_to) / 2)
    elif salary_from > 0:
        mid_salary = int(salary_from * 1.2)
    elif salary_to > 0:
        mid_salary = int(salary_to * 0.8)
    return mid_salary


def predict_rub_salary_hh(vacancy):
    hh_rub_salary = 0
    if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
        salary_from = vacancy['salary']['from'] or 0
        salary_to = vacancy['salary']['to'] or 0
        hh_rub_salary = predict_salary(salary_from, salary_to)
    return hh_rub_salary


def predict_rub_salary_sj(vacancy):
    sj_predict_salary = 0
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    if vacancy['currency'] == 'rub':
        sj_predict_salary = predict_salary(salary_from, salary_to)
    return sj_predict_salary


def get_vacancies_from_hh(language):
    hh_url = 'https://api.hh.ru/vacancies'
    page = 0  # первая страница поиска (нумерация с 0)
    number_of_pages = 1
    vacancies = []
    while page < number_of_pages:
        headers = {'User-Agent': 'HH-User-Agent'}
        params = {
            'area': 1,  # Код города, 1 - Москва
            'text': f'программист {language}',
            'page': page  # Текущая страница поиска
        }
        response = requests.get(hh_url, headers=headers, params=params)
        page += 1
        with suppress(requests.exceptions.HTTPError):
            response.raise_for_status()
        developers_of_lang_data = response.json()
        vacancies.extend(developers_of_lang_data['items'])
        number_of_pages = developers_of_lang_data['pages'] - 1
    return vacancies


def get_hh_statistic(vacancies):
    if vacancies:
        number_of_vacancies = len(vacancies)
        salaries = [predict_rub_salary_hh(vacancy) for vacancy in vacancies if predict_rub_salary_hh(vacancy) != 0]
        vacancies_processed = len(salaries)
        average_salary = int(sum(salaries)/vacancies_processed)
        hh_statistics = {
            'vacancies_found': number_of_vacancies,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }
        return hh_statistics


def make_all_language_stat_from_hh(languages):
    stat = {}
    for language in languages:
        vacancies = get_vacancies_from_hh(language)
        stat[language] = get_hh_statistic(vacancies)
    return stat


def get_vacancies_from_sj(language, secret_key):
    sj_url = 'https://api.superjob.ru/2.0/vacancies'
    page = 0
    next_page = True
    vacancies = []
    while next_page:
        headers = {'X-Api-App-Id': secret_key}
        params = {
            'page': page,  # Номер страницы результата поиска
            'count': 5,  # Количество результатов на страницу поиска
            'keyword': language,  # Язык программирования
            'town': 4,  # Название города или его ID. 4 - Москва
            'catalogues': 48,  # Список разделов каталога отраслей. 48 - "Разработка, программирование"
            'no_agreement': 1  # Без вакансий, где оклад по договоренности
        }
        response = requests.get(sj_url, headers=headers, params=params)
        page += 1
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            next_page = False
            continue
        developers_of_lang_data_sj = response.json()
        vacancies.extend(developers_of_lang_data_sj['objects'])
        next_page = developers_of_lang_data_sj['more']
    return vacancies


def get_sj_statistic(vacancies):
    number_of_vacancies = len(vacancies)
    if number_of_vacancies:
        salaries = [predict_rub_salary_sj(vacancy) for vacancy in vacancies]
        average_salary = int(sum(salaries)/number_of_vacancies)
        sj_statistics = {
            'vacancies_found': number_of_vacancies,
            'vacancies_processed': number_of_vacancies,
            'average_salary': average_salary
        }
        return sj_statistics


def make_all_language_stat_from_sj(languages):
    stat = {}
    for language in languages:
        vacancies = get_vacancies_from_sj(language, secret_key)
        stat[language] = get_sj_statistic(vacancies)
    return stat


def make_table(site_name, statistic):
    title = '-----------------{} statistics'.format(site_name)
    if statistic:
        table_in_terminal = [[
            'lang', 'vacancies_found', 'vacancies_processed', 'average_salary'
        ]]
        for language, language_stat in statistic.items():
            if not language_stat:
                continue
            row = [language]
            for key, value in language_stat.items():
                row.append(value)
            table_in_terminal.append(row)
        return AsciiTable(table_in_terminal, title).table


if __name__ == '__main__':
    load_dotenv()
    languages = ['Python', 'Java', 'Javascript', 'TypeScript', 'Swift', 'Scala', 'Objective-C', 'Shell', 'Go', 'C', 
                 'PHP', 'Ruby', 'c++', 'c#', '1c']
    site_name = 'HH'
    print(make_table(site_name, make_all_language_stat_from_hh(languages)))

    site_name = 'SJ'
    secret_key = os.getenv('SJ_KEY')
    print(make_table(site_name, make_all_language_stat_from_sj(languages)))