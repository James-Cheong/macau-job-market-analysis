import re
import pandas as pd
import time
import datetime
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def main():
    start_time = time.time()

    all_jobs_list = []
    search_jobs(all_jobs_list)
    # store in cv
    df = pd.DataFrame(all_jobs_list, columns=['種類', '公司類型', '招聘職位', '薪金', '公司名稱', '學歷', '經驗/技能', '職責'])
    df = pre_process_data(df)
    df.to_csv(f'D:\python_project\output\gov_jobs_{datetime.datetime.now().strftime("%Y%m%d")}.csv', index=False, encoding='utf_8_sig')
    end_time = time.time()
    print(f'Finished in {end_time-start_time:.2f}s')


def pre_process_data(df):

    return df

def driver_init(url: str):
    # Set the path to the Firefox webdriver
    firefox_driver_path = "driver\geckodriver.exe"
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.headless = True
    # Add the anti-scrape headers to the request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    for key, value in headers.items():
        firefox_options.add_argument(f"--header={key}={value}")
    # Open the Firefox web browser
    service = Service(executable_path=firefox_driver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    # Navigate to the website
    driver.get(url)
    # Wait for the page to load
    driver.implicitly_wait(10)
    return driver


def expand_all_jobs_in_job_detail(driver):
    # get the total nums of the jobs in this page
    job_list = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/div[1]/div/p'))).text
    job_nums = re.findall(r'\d+', job_list)[0]
    # scroll to the bottom of the page
    while len(driver.find_elements(By.CSS_SELECTOR, "div.job__box")) < int(job_nums):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
       # time.sleep(0.5)
    # expand all job_box
    action_divs = driver.find_elements(By.CSS_SELECTOR, ".action__text")
    for div in action_divs:
        # Scroll the div into view and click on it
        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", div)


def get_all_jobs_in_page(driver, category: str):
    all_jobs = []
    job_boxes = driver.find_elements(By.CSS_SELECTOR, "div.job__box")
    # Iterate over the job__box
    for job_box in job_boxes:
        job_in_job_box = [category]
        # Iterate over the m-cell divs
        for m_cell in job_box.find_elements(By.CSS_SELECTOR, ".m-cell"):
            # Find the m-cell__title div
            m_cell_title = m_cell.find_element(By.CSS_SELECTOR, ".m-cell__title").text
            # Check if the m-cell__title text is equal to the desired value
            if m_cell_title not in ("", "空缺編號", "工作地點", "工作時間"):
                # Find the m-cell__value div
                m_cell_value = m_cell.find_element(By.CSS_SELECTOR, ".m-cell__value").text
                # append all description to a list
                job_in_job_box.append(m_cell_value)
        all_jobs.append(job_in_job_box)
    return all_jobs


def search_jobs_for_market_box(marketing_box_index, all_jobs_list):
    driver = driver_init('https://www.dsal.gov.mo/jobseeking/app/#/service')

    market_box_jobs_list = []
    wait = WebDriverWait(driver, 10)
    marketing_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".marketing__box")))
    market_name = marketing_boxes[marketing_box_index].text
    try:
        btn = driver.find_element(By.XPATH, "//button[contains(., '不再提示')]")
        btn.click()
    except:
        print('No need to click 不再提示')
    # click the market box and show the minor boxes for the first time
    driver.execute_script("arguments[0].scrollIntoView();", marketing_boxes[marketing_box_index])
    marketing_boxes[marketing_box_index].click()

    minor_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".minor__box")))

    # Keep track of the current minor__box index
    minor_box_index = 0

    # Iterate through each minor__box
    while minor_box_index < len(minor_boxes):
        try:
            first_line_div = minor_boxes[minor_box_index].find_element(By.CSS_SELECTOR, ".first__line")
            # Click into the current minor__box
            category = first_line_div.text
            driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", first_line_div)
        except:
            print('Somehow can\'t click the minor box...')
        try:
            # Wait for the desired element to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job__box")))
            # extracting data if job_box is located
            expand_all_jobs_in_job_detail(driver)
            jobs_list = get_all_jobs_in_page(driver, category)
            market_box_jobs_list += jobs_list
        except:
            print('This minor box doesn\'t have any jobs. Skipping ...')

        # Go back to the original page
        driver.back()
        driver.refresh()
        # Wait for the marketing__box to reload
        marketing_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".marketing__box")))
        driver.execute_script("arguments[0].scrollIntoView();", marketing_boxes[marketing_box_index])
        marketing_boxes[marketing_box_index].click()
        # reload minor_boxes
        minor_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".minor__box")))
        # Increment the current minor__box index
        minor_box_index += 1
    all_jobs_list += market_box_jobs_list
    driver.quit()
    return f'{market_name} is completed.'


def search_jobs(data):
    driver = driver_init('https://www.dsal.gov.mo/jobseeking/app/#/service')
    marketing_boxes_num = len(WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".marketing__box"))))
    driver.quit()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(search_jobs_for_market_box, marketing_box_index, data) for marketing_box_index in range(marketing_boxes_num)]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())


if __name__ == '__main__':
    main()
