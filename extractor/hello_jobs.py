import time
import asyncio
import backoff
import pandas as pd
from aiohttp import ClientSession, ClientError
from bs4 import BeautifulSoup


@backoff.on_exception(backoff.expo, ClientError, max_tries=5, factor=2)
async def fetch_html(url, session):
    async with session.get(url) as response:
        return await response.text()


async def scrape_page(page_num: int, session: ClientSession):
    data = []
    url = f'https://jobsearch.hello-jobs.com/Job-Search/%E4%BB%BB%E4%BD%95%E8%81%B7%E4%BD%8D%E7%A8%AE%E9%A1%9E-Functional-Area-Jobs-in-Macau/F-1.aspx?pageNumber={page_num}'
    html = await fetch_html(url, session)
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.select("a[id$='_lnkJobTitle']")
    for link in links:
        url = link.get('href')
        url = 'https://jobsearch.hello-jobs.com/Job-Search' + url[2:]
        job_html = await fetch_html(url, session)
        job_soup = BeautifulSoup(job_html, 'html.parser')
        try:
            catagory = job_soup.find('span', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_rptFieldOfWork_ctl00_LblReqFieldOfWork'}).text
            catagory = catagory.split(' ')[0]
        except AttributeError:
            catagory = None

        try:
            job_title = job_soup.find('span', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_LblJobTitle'}).text
            print(job_title)
        except AttributeError:
            job_title = None

        try:
            job_description = job_soup.find('div', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_DivJobDescription'}).text
        except AttributeError:
            job_description = None

        try:
            company_name = job_soup.find('span', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_lblCompanyDisplayName'}).text
        except AttributeError:
            company_name = None

        try:
            education = job_soup.find('span', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_lblEducationLevel'}).text
            if education in ('學士學位', '碩士學位或以上'):
                education = '高等教育'
            elif education in ('小學', '中學'):
                education += '教育'
            else:
                education = '職業技術教育'
        except AttributeError:
            education = None

        try:
            industry = job_soup.find('span', {'id': 'ctl00_MasterContentPlaceHolder_GeneralJobDescription_LblReqIndustry'}).text
        except AttributeError:
            industry = None

        row = {'種類': catagory, '公司類型': industry, '招聘職位': job_title, '薪金': None, '公司名稱': company_name, '學歷': education, '經驗/技能': None, '職責': job_description}
        data.append(row)
    return data


async def main():
    job_detail = []
    async with ClientSession() as session:
        tasks = [asyncio.create_task(scrape_page(i, session)) for i in range(1, 56)]
        results = await asyncio.gather(*tasks)
        for result in results:
            job_detail.extend(result)
    df = pd.DataFrame(job_detail)
    df.to_csv('D:\python_project\output\hello_jobs.csv', index=False, encoding='utf_8_sig')


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f'Finished in {end_time-start_time} s')
