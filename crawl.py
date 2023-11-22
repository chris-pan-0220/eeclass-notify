import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import DB
import LineNotify
import time

config = configparser.ConfigParser()
config.read('config.ini')

credential = config['credential']
account = credential['ACCOUNT']
password = credential['PASSWORD']
db_url = credential['DB_URL']

# 设置Selenium WebDriver，这里以Chrome为例 
driver = webdriver.Chrome('./chromedriver.exe')
root_url = 'https://ncueeclass.ncu.edu.tw'

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

"""從eeclass首頁登入"""
def login():
    try:
        driver.get(root_url)
        # 填写登录表单
        username_input = driver.find_element(By.NAME, "account")
        password_input = driver.find_element(By.NAME, "password")

        username_input.send_keys(account)
        password_input.send_keys(password)

        # 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, "button[data-role='form-submit']")
        login_button.click()

        # 點擊保持登入
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "a.keepLoginBtn"))
        )
        keep_login_button = driver.find_element(By.CSS_SELECTOR, "a.keepLoginBtn")
        keep_login_button.click()
    except Exception as e:
        print(e)
        driver.quit()
    
"""從eeclass首頁登出"""
def logout():
    # 切回首頁
    driver.get(root_url)

    # 尋找登出按鈕
    WebDriverWait(driver, 10).until(
        EC.visibility_of_any_elements_located((By.XPATH, '//*[@id="mod_115"]/div[3]/div/div[5]/span/a'))
    )
    logout_btn = driver.find_elements(By.XPATH, '//*[@id="mod_115"]/div[3]/div/div[5]/span/a')[-1]

    # 點擊登出按鈕
    logout_btn.click()

"""從dashboard頁面的課程列表獲取所有課程號碼，用來遍歷所有課程頁面"""
def get_course():
    try:
        # 獲取課程列表
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.fs-thumblist"))
        )
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # 從課程列表中，提取所有课程號碼
        course = []
        for link in soup.find('div', {'class': 'fs-thumblist'}).find_all('a', href=True):
            if '/course/' in link['href'] and link.text.strip():
                course.append({'course_id': link['href'].replace('/course/', ''), 'title': link.text.strip()})

    except Exception as e:
        print(e)
        logout()
        driver.quit()
    return course

def get_homework(course_number: list[str]):
    collect = { c:{'result': 0, 'target': 0} for c in course_number}
    try:
        for course in course_number: # 對於每一種課程
            
            # 切換到作業頁面
            url = f'{root_url}/course/homeworkList/{course}'
            
            driver.get(url)
            # time.sleep(1)

            # 解析html
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 計算作業數量
            n_rows = 0
            if soup.find('tr', {'id': 'noData'}):
                collect[course]['target'] = 0
                continue
            if soup.find('tbody'):
                n_rows = len(soup.find('tbody').find_all('tr'))
            print(url)
            print('作業數目: ', n_rows)
            collect[course]['target'] = n_rows

            homework = []
            # 對於每一個作業
            for i in range(1, n_rows+1):
                row = soup.select_one(f'tbody > tr:nth-child({i})')

                # 2:title
                title = row.select_one(f'td:nth-child({2}) a').get('title')

                # 5:deadline
                deadline = row.select_one(f'td:nth-child({5}) div').text
                # 09-19 12:00
                # 示例字符串
                date_str = "09-19 12:00"

                # 获取当前年份
                current_year = datetime.now().year

                # 将字符串转换为 datetime 对象
                # 格式 "%Y-%m-%d %H:%M" 中的 %Y 代表四位年份
                date_obj = datetime.strptime(f"{current_year}-{deadline}", "%Y-%m-%d %H:%M")

                # 6:finished
                # print('row: ', row)
                # print('是否完成: ', row.select_one('td:nth-child(6) div span'))
                if row.select_one('td:nth-child(6) div span'):
                    is_finish = True
                else:
                    is_finish = False

                print('title: ', title)
                print('deadline: ', deadline)
                print('deadline (formatted): ', date_obj)
                print('finished: ', is_finish)

                homework.append({'title': title, 'deadline': date_obj, 'is_finish': is_finish, 'course_id': course})

                collect[course]['result'] += 1

            print(f'完成抓取: {collect[course]["result"]}/{collect[course]["target"]}')

        return homework
    except Exception as e:
        print(e)
        logout()
        driver.quit()

def update_homework():
    session = Session()
    course = session.query(DB.Course).all()
    course_id = [ str(c.course_id) for c in course]
    homework = get_homework(course_id)
    
    homework_old = session.query(DB.Homework).all()
    homework_old_title = [h.title for h in homework_old]
    homework_new = []
    for h in homework:
        if h['title'] not in homework_old_title:
            homework_new.append(
                DB.Homework(course_id=h['course_id'],
                            title=h['title'],
                            deadline=h['deadline'],
                            is_finish=h['is_finish']))
    
    if len(homework_new) != 0:
        session = Session()
        session.add_all(homework_new)
        session.commit()
        
        print('新增作業: ')
        for h in homework_new:
            print(h)
        session.close()
    else:
        print('沒有新的作業')
        session.close()
    
    

def init():
    DB.migration()
    
    # 獲取課程資料
    course = get_course()
    print('課程資料: ', course)

    # 將課程資料儲存到資料庫
    session = Session()
    session.add_all([ DB.Course(course_id=c['course_id'], title=c['title']) for c in course])
    session.commit()
    session.close()


def main():
    login()
    # check init
    
    db_path = db_url.split('///')[1]
    if not os.path.exists(db_path):
        print('initialize database')
        init()

    # update homework
    update_homework()

    # send message
    session = Session()
    course = session.query(DB.Course).all()
    messages = ''
    today = datetime.today()
    for c in course:
        id = c.course_id # 注意foreign key
        homework = session \
                    .query(DB.Homework) \
                    .filter(DB.Homework.course_id == id) \
                    .filter(DB.Homework.deadline > today) \
                    .filter(DB.Homework.is_finish == False) \
                    .all()
        if len(homework):
            messages += f'{c.title}\n'
            messages += '='*25+'\n'
            for h in homework:
                messages += '\n'
                messages += f'{h.title}\n'
                messages += f'期限：{h.deadline.strftime("%m-%d %H:%M")}\n'
                messages += '\n'
    if messages != '':
        messages = '未完成作業：\n\n' + messages
        print(messages)
        LineNotify.send_line_notify(messages)
    else:
        messages = '呱！目前沒有未完成的作業'
        print(messages)
        LineNotify.send_line_notify(messages)

    session.close()
    logout()
    driver.quit()

if __name__ == '__main__':
    # today = datetime.today()
    # session = Session()
    # homework = session \
    #         .query(DB.Homework) \
    #         .filter(DB.Homework.deadline > today) \
    #         .filter(DB.Homework.is_finish == False) \
    #         .all()
    # for h in homework:
    #     print(h)
    # session.close()
    main()

# course = [{'course_id': '24337', 'title': '資訊電機學院學士班導師班'}, {'course_id': '21795', 'title': '資料科學導論 Introduction to Data Science'}, {'course_id': '22828', 'title': '資電專題實作(I) Independent study of electrical and computer engineering (I)'}, {'course_id': '23230', 'title': '經濟學 Economics'}, {'course_id': '21760', 'title': '機率與統計 Probability and Statistics'}, {'course_id': '23394', 'title': '排球入門 Volleyball I'}, {'course_id': '22599', 'title': '自然語言處理 Natural language processing'}, {'course_id': '22777', 'title': '商事法 Introduction to Commercial Law'}, {'course_id': '22091', 'title': '資料結構 Data Structure'}, {'course_id': '21761', 'title': '組合語言與系統程式 Assembly Language and System Programming'}]
# engine = create_engine(db_url)
# Session = sessionmaker(bind=engine)
# # exit()
# for c in course: 
#     print(c)
#     session = Session()
#     new_course = Course(course_id=c['course_id'], title=c['title'])
#     session.add(new_course)
#     session.commit()
#     session.close()

# session = Session()
# session.query(Homework).all()
# session.close()
# for c in course:
#     print(c)
    


# def collect_course(course_number: list[str]):
#     collect = { c:{'result': 0, 'target': 0} for c in course_number} 
#     for course in course_number: # 對於每一種課程
#         # 切換到公告頁面
#         url = f'{root_url}/course/bulletin/{course}'
#         print(url)
#         driver.get(url)

#         # 準備解析html
#         html = driver.page_source
#         soup = BeautifulSoup(html, 'html.parser')

#         # 計算公告數量
#         n_rows = 0
#         if soup.find('tr', {'id': 'noData'}):
#             collect[course]['target'] = 0
#             continue
#         if soup.find('table', {'id': 'bulletinMgrTable'}):
#             n_rows = len(soup.find('table', {'id': 'bulletinMgrTable'}).find('tbody').find_all('tr'))
#         print('公告數目: ', n_rows)
#         collect[course]['target'] = n_rows

#         # 對於每一個公告
#         for i in range(1, n_rows+1):
#             # 点击公告链接
#             WebDriverWait(driver, 5).until(
#                 EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f"#bulletinMgrTable tr:nth-child({i}) a"))
#             )
#             announcement_link = driver.find_element(By.CSS_SELECTOR, f'#bulletinMgrTable tr:nth-child({i}) a')
#             announcement_link.click()

#             # 等待modal加载完成
#             WebDriverWait(driver, 5).until(
#                 EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f"#mod_bulletin_contentModal_course_{course} > div"))
#             )

#             # 切换到iframe (公告放在iframe裡面)
#             iframe = driver.find_element(By.CSS_SELECTOR, ".fs-modal-iframe")
#             driver.switch_to.frame(iframe)
#             # 提取公告的详细信息
#             WebDriverWait(driver, 5).until(
#                 EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f".modal-iframe-ext2"))
#             )
#             announcement_title = driver.find_element(By.CSS_SELECTOR, ".modal-iframe-ext2").text
#             announcement_content = driver.find_element(By.CSS_SELECTOR, ".bulletin-content")

#             # 印出提取的信息
#             print("公告標題：", announcement_title)
#             print("公告内容：")
#             for c in announcement_content.find_elements(By.CSS_SELECTOR, '.bulletin-content > div'):
#                 print(c.text)

#             # 切换回主页面
#             driver.switch_to.default_content()

#             # 關閉modal
#             close_btn = driver.find_element(By.CSS_SELECTOR, f'#mod_bulletin_contentModal_course_{course} > div > div > div.modal-header > button')
#             close_btn.click()

#             collect[course]['result'] += 1

#         print(f'完成抓取: {collect[course]["result"]}/{collect[course]["target"]}')

#     print('最終結果：', collect)

# def crawl():
#     login()
#     course_number = get_course_number()
#     # collect_course(course_number)
#     collect_homework(course_number)
#     logout()

# def init():
#     login()  
#     course_number = get_course_number()  

# crawl()
# exit()

# login()

# WebDriverWait(driver, 10).until(
#     EC.visibility_of_element_located((By.CSS_SELECTOR, "div.fs-thumblist"))
# )
# html = driver.page_source
# soup = BeautifulSoup(html, 'html.parser')

# # 提取所有课程链接
# course_number = []
# for link in soup.find('div', {'class': 'fs-thumblist'}).find_all('a', href=True):
#     if '/course/' in link['href']:
#         # 构建完整的课程链接
#         # course_url = root_url + link['href']
#         course_number.append(link['href'].replace('/course/', ''))

# course_number = list(set(course_number))
# collect = { c:{'result': 0, 'target': 0} for c in course_number} 
# for course in course_number:
#     url = f'{root_url}/course/bulletin/{course}'
#     print(url)
#     driver.get(f'{root_url}/course/bulletin/{course}')
#     html = driver.page_source
#     soup = BeautifulSoup(html, 'html.parser')
#     n_rows = 0
#     if soup.find('tr', {'id': 'noData'}):
#         collect[course]['target'] = 0
#         continue
#     if soup.find('table', {'id': 'bulletinMgrTable'}):
#         n_rows = len(soup.find('table', {'id': 'bulletinMgrTable'}).find('tbody').find_all('tr'))
#     print('公告數目: ', n_rows)
#     collect[course]['target'] = n_rows
#     for i in range(1, n_rows+1):
#         # 点击某个公告链接（根据实际情况选择合适的选择器）
#         WebDriverWait(driver, 5).until(
#             EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f"#bulletinMgrTable tr:nth-child({i}) a"))
#         )
#         announcement_link = driver.find_element(By.CSS_SELECTOR, f'#bulletinMgrTable tr:nth-child({i}) a')
#         announcement_link.click()
#         # 等待模态框加载完成
#         try:
#             WebDriverWait(driver, 5).until(
#                 EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f"#mod_bulletin_contentModal_course_{course} > div"))
#             )
#         except: 
#             print('find modal fail')
#         # 切换到iframe
#         iframe = driver.find_element(By.CSS_SELECTOR, ".fs-modal-iframe")
#         driver.switch_to.frame(iframe)
#         # 提取公告的详细信息
#         WebDriverWait(driver, 5).until(
#             EC.visibility_of_all_elements_located((By.CSS_SELECTOR, f".modal-iframe-ext2"))
#         )
#         popularity = driver.find_element(By.CSS_SELECTOR, ".modal-iframe-ext2").text
#         announcement_content = driver.find_element(By.CSS_SELECTOR, ".bulletin-content")

#         # 打印提取的信息
#         print("公告详情：", popularity)
#         print("公告内容：")
#         for c in announcement_content.find_elements(By.CSS_SELECTOR, '.bulletin-content > div'):
#             print(c.text)

#         # 切换回主页面
#         driver.switch_to.default_content()

#         close_btn = driver.find_element(By.CSS_SELECTOR, f'#mod_bulletin_contentModal_course_{course} > div > div > div.modal-header > button')
#         close_btn.click()

#         collect[course]['result'] += 1

#     print(f'完成抓取: {collect[course]["result"]}/{collect[course]["target"]}')

# print('最終結果：', collect)

# logout()
# print('登出成功')
# driver.quit()






    
# 点击“保持登录”按钮（根据实际的按钮定位进行替换）

# 接下来可以进行其他操作，比如获取课程信息
# ...

# 完成后关闭浏览器
# driver.quit()
