import multiprocessing
import re
import pandas as pd
from fuzzywuzzy import fuzz
from extractor.mapping import CATEGORY_MAPPING, INDUSTRY_MAPPING


# def compare_rows(row1, df2):
#     duplicates = []
#     for _, row2 in df2.iterrows():
#         title_score = fuzz.token_sort_ratio(row1['招聘職位'], row2['招聘職位'])
#         company_score = fuzz.token_sort_ratio(row1['公司名稱'], row2['公司名稱'])
#         if title_score >= 80 and company_score >= 80:
#             duplicates.append(_)
#     return duplicates


# def get_duplicats(df1, df2):
#     df1 = df1[['招聘職位', '公司名稱']]
#     df2 = df2[['招聘職位', '公司名稱']]
#     with multiprocessing.Pool() as pool:
#         results = []
#         for _, row1 in df1.iterrows():
#             result = pool.apply_async(compare_rows, args=(row1, df2))
#             results.append(result)
#         duplicates = []
#         for result in results:
#             duplicates += result.get()

#     return duplicates


def search_experience(s: str):
    num_dict = {
        '一': '1', '二': '2', '兩': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7',
        '八': '8', '九': '9', '十': '10', '十一': '11', '十二': '12', '十三': '13',
        '十四': '14', '十五': '15', '十六': '16', '十七': '17', '十八': '18', '十九': '19',
        '二十': '20', '二十五': '25', '三十': '30', '三十五': '35', '四十': '40'
    }
    pattern = "([0-9一二兩三四五六七八九十]+)(?:\+|\s?年|\syears|\syear|-year)(?:.*experience|.*經驗)"
    match = re.search(pattern, s)
    if match:
        exp_str = match.group(1)
        if re.search('[\u4e00-\u9fff]', exp_str):
            exp_str = num_dict[exp_str]
        return int(exp_str)
    else:
        return 0


def extract_salary_range(salary_range: str, x: int):
    if '按日' in salary_range:
        match = re.findall(r'\d+', salary_range.replace(',', ''))
        return int(match[0]) * x
    else:
        match = re.findall(r'\$(\d+,\d+)', salary_range)
        if len(match) == 1:
            val = int(match[0].replace(",", ""))
            return val
        elif len(match) == 2:
            low, high = [int(x.replace(",", "")) for x in match]
            return (low + high) / 2
        else:
            return None


def data_cleansing(df, x):
    # df2 = pd.read_csv('.\output\hello_jobs.csv')
    # duplicates_index = get_duplicats(df1, df2)
    # df2.drop(duplicates_index, inplace=True)
    # df = pd.concat([df1, df2])
    df.dropna(subset=['種類', '公司類型'],inplace=True)
    df['學歷'] = df['學歷'].apply(lambda x: re.search(r'.*?教育', x).group() if re.search(r'.*教育', x) else '不論學歷')
    df['學歷'] = df['學歷'].str.replace('初中教育', '中學教育').str.replace('高中教育', '中學教育')
    df['種類'] = df['種類'].replace(CATEGORY_MAPPING)
    df['公司類型'] = df['公司類型'].replace(INDUSTRY_MAPPING)
    df['experience'] = df['經驗/技能'].fillna('') + df['職責'].fillna('')
    df['experience'] = df['experience'].apply(search_experience)
    df['mid_salary'] = df['薪金'].apply(lambda salary_range: extract_salary_range(salary_range, x))
    df.to_csv('job_list.csv', index=False, encoding='utf_8_sig')
    return df
