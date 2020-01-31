import os
from csv import DictWriter

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
import sys

import time
##################################################################################################################
# ***DISCLAIMER:
# Scraping data may be considered illegal. This script is developed for
# educational purposes only. Before scraping a website please get the owners
# permission first.
##################################################################################################################


def wait_for_element(delay, element, driver):
    """Wait for the element to appear on the webpage before continuing"""
    try:
        myElem = WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.ID, element)))
        # print(f"[+]Page is ready , \'{element}\' found")
    except TimeoutException:
        # print("[-]Waiting took too much time!")
        pass


##################################################################################################################
def login(user, passw, driver):
    """Do the required login"""
    print(f'[*] Trying log in with username: \'{user}\'')
    username = driver.find_element_by_id("inputEmail")  # username form field
    password = driver.find_element_by_id(
        "inputPassword")  # password form field

    username.send_keys(user)
    password.send_keys(passw)

    driver.find_element_by_css_selector(
        '.btn.btn-lg.btn-primary.btn-block').click()

##################################################################################################################


def get_lessons_from_progress(driver):
    """Finds specific elements from the HTML source code in order to get their values - dirty workaround because progress doesn't like scraping it"""

    frame1 = WebDriverWait(driver, 5).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, 'contentAreaFrame')))

    driver.implicitly_wait(12)

    # wait_for_element(10, 'isolatedWorkAreaForm')
    lessons_table = driver.find_element_by_id('isolatedWorkAreaForm')
    val = lessons_table.get_attribute("action")

    driver.get(val)

    # wait_for_element(10, 'WD3F-contentTBody')
    driver.refresh()
    wait_for_element(7, 'WD3F-contentTBody', driver)
    lessons_table = driver.find_element_by_id('WD3F-contentTBody')

    # wait_for_element(10, 'WD10AA')

    # print(driver.find_element_by_id('WD10AA').text)#mesos oros

    # get all of the rows in the table
    return lessons_table.find_elements_by_xpath(".//tr")


##################################################################################################################
def save_results_csv(xrostoumena, perasmena, user):
    """Export data to a csv file"""

    with open("grades"+"_"+user+".csv", mode='w', newline='') as file:
        headers = ['Όνομα Μαθήματος', 'Περίοδος', 'Εξάμηνο', 'Βαθμός']
        csv_writer = DictWriter(file, delimiter=',',
                                quotechar='"', fieldnames=headers)
        csv_writer.writeheader()

        for row in xrostoumena:
            csv_writer.writerow({
                'Όνομα Μαθήματος': row[0],
                'Περίοδος': row[1],
                'Εξάμηνο': row[2],
                'Βαθμός': 0.0
            })

        for row in perasmena:
            csv_writer.writerow({
                'Όνομα Μαθήματος': row[0],
                'Περίοδος': row[1],
                'Εξάμηνο': row[2],
                'Βαθμός': row[3]
            })

    print(f'[+]Grades saved : grades_{user}.csv')


##################################################################################################################
def calculate_ECTS(ects, xeim, ear, period):
    ects = int(ects.replace(',00', ''))
    if period == 'Χειμερινό Εξάμηνο':
        xeim += ects
    else:
        ear += ects

    return xeim, ear


##################################################################################################################

def find_lessons(rows):

    rows.pop(0)

    xrostoumena = []
    perasmena = []

    lessons = [[row.find_elements_by_xpath(".//td")[3].text,
                row.find_elements_by_xpath(".//td")[6].text,
                row.find_elements_by_xpath(".//td")[19].text,
                row.find_elements_by_xpath(".//td")[4].text]
               for row in rows if row.find_elements_by_xpath(".//td")[0].text != ' ' and len(row.find_elements_by_xpath(".//td")) > 3]

    for i in reversed(range(len(lessons))):

        if not lessons[i][0]:
            del lessons[i]
            continue

        try:
            grade = float(lessons[i][3].replace(',', '.'))
        except:
            grade = 0.0

        if(grade >= 5.0):
            perasmena.append(lessons[i])
            del lessons[i]
        else:
            continue

    for i in reversed(range(len(lessons))):
        try:
            grade = float(lessons[i][3].replace(',', '.'))
        except:
            grade = 0.0

        if(grade < 5.0 and not any(lessons[i][0] in les for les in perasmena) and not any(lessons[i][0] in les for les in xrostoumena)):
            xrostoumena.append(lessons[i])

        del lessons[i]

    return xrostoumena, perasmena


##################################################################################################################
def main():
    # prevent firefox from opening windows
    options = Options()

    options.headless = True

    # choose a browser that you have already installed on your machine
    driver = webdriver.Firefox(
        options=options, executable_path=os.path.dirname(os.path.abspath(__file__))+"\\geckodriver.exe")
    # driver = webdriver.Chrome(
    #     options=options, executable_path=os.path.dirname(os.path.abspath(__file__))+"\\geckodriver.exe")

    driver.get("https://progress.upatras.gr")

    # login to progress.upatras.gr
    login(sys.argv[1], sys.argv[2], driver)

    wait_for_element(5, 'welcomeText', driver)

    # navigate to page behind login

    wait_for_element(5, 'OL2N11', driver)

    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located((By.ID, 'divLoadingBackground')))

    driver.find_element_by_id("0L2N11").click()

    # get lessons information from table
    try:
        lessons = get_lessons_from_progress(driver)
    except Exception as e:
        print(e)
    finally:
        pass

    try:
        # save results to csv file
        xrostoumena, perasmena = find_lessons(lessons)

        save_results_csv(xrostoumena, perasmena, sys.argv[1])
    finally:
        # close driver
        driver.close()


if __name__ == "__main__":
    # start_time = time.time()
    main()
    # print("--- %s seconds ---" % (time.time() - start_time))
