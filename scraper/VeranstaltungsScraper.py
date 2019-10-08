import hashlib
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class VeranstaltungsScraper:
    def __init__(self):
        self.list_url = 'http://www.lsf.tu-berlin.de/qisserver/servlet/de.his.servlet.RequestDispatcherServlet?state=wplan&missing=allTerms&week=-1&act=stg&pool=stg&show=liste&P.vx=lang&P.subc=plan&k_abstgv.abstgvnr='
        self.search_url = 'https://moseskonto.tu-berlin.de/moses/modultransfersystem/studiengaenge/anzeigenKombiniert.html?id='
        self.courses = ['626', '1103']
        self.moses = ['179', '33']

        options = Options()
        options.headless = False
        self.driver = webdriver.Chrome(
            executable_path='/Users/franzbender/Documents/Software/Semesterplan/chromedriver',
            chrome_options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_module(self, id, version):
        url = f'https://moseskonto.tu-berlin.de/moses/modultransfersystem/bolognamodule/beschreibung/anzeigen.html?number={id}&version={version}&sprache=1'

        self.driver.get(url)

        text = self.driver.find_element_by_xpath('//span[contains(@id, "BoxBestandteile")]').text
        numbers = re.findall('(\d+ L \d+)', text)
        return numbers

    def all_modules(self):
        all = {}
        for id in self.moses:
            all.update(self.get_modules(id))

        for key in all:
            name, version = all[key]
            connections = self.get_module(key, version)
            all[key] = name, version, connections

        return all

    def get_modules(self, id):
        self.driver.delete_all_cookies()
        self.driver.get(f'{self.search_url}{id}')

        element = self.driver.find_element_by_xpath("//li[@data-label='Modulliste WS 2019/20']")
        self.driver.execute_script("arguments[0].click();", element)

        self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[@class='ui-column-title' and contains(text(), 'Studiengangsbereich')]")))

        folders = self.driver.find_elements_by_xpath(
            '//tr/td/span[contains(@class, "ui-treetable-toggler") and contains(@class, "ui-icon-triangle-1-e") and not(@style="visibility:hidden")]')

        lists = []
        for i, folder in enumerate(folders):
            folder.click()
            time.sleep(0.1)
            lists += self.driver.find_elements_by_xpath(f'//tr[@data-prk="0_{i}"]')

        data = {}
        for folder in lists:
            new = self.get_modules_for_folder(folder)
            data.update(new)

        return data

    def get_modules_for_folder(self, node: WebElement):
        node.click()

        title = node.find_element_by_xpath('.//span[@style="font-size: small;"]').text.strip()
        self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//h4[contains(text(), '" + title + "')]")
        ))

        self.wait.until(EC.invisibility_of_element_located(
            (By.XPATH, 'span[@class="fa fa-refresh fa-spin loading-symbol"]')
        ))

        heading = self.driver.find_element_by_xpath('//div[@class="panel-heading"]/strong[contains(text(), "Module")]')
        table = heading.find_element_by_xpath('../..//table/tbody')

        data = {}

        for row in table.find_elements_by_xpath('tr'):
            fields = row.find_elements_by_xpath('td')
            if len(fields) > 0:
                name = fields[0].text.strip()
                nr = fields[1].text.strip()
                version = fields[2].text.strip()
                data[nr] = (name, version)

        return data

    def all_lsf(self):
        veranstaltungen = {}
        for course in self.courses:
            tmp_veranstaltungen = self.get_list(course)
            for (nr, title, sws, times) in tmp_veranstaltungen:
                if not nr in veranstaltungen:
                    veranstaltungen[nr] = title, sws, times
        return veranstaltungen

    def get_list(self, plan):
        self.driver.get(f'{self.list_url}{plan}')

        veranstaltung_headlines = self.driver.find_elements_by_xpath(
            '//a[contains(@href, "publishSubDir=veranstaltung")]')

        out_list = []
        for veranstaltung in veranstaltung_headlines:
            nr, title, sws, active, times = self.process_veranstaltung(veranstaltung)
            if active:
                out_list.append((nr, title, sws, times))

        return out_list

    def process_veranstaltung(self, veranstaltung: WebElement):
        parent, active, meta, table = self.extract_parent_data(veranstaltung)

        title = veranstaltung.text
        sws = self.extract_sws(meta)
        nr = self.extract_nr(meta)
        times = self.extract_dates(table)

        return (nr, title, sws, active, times)

    def extract_sws(self, meta: WebElement):
        swses = re.findall('(\d+.\d)+ SWS', meta.text)
        sws = 'no information'
        if len(swses) > 0:
            sws = swses[0]
        return sws

    def extract_nr(self, meta: WebElement):
        numbers = re.findall('Nr\.:  (\d+ L \d+)', meta.text)

        number = 'No Information (self-generated unique number: ' + hashlib.md5(meta.text.encode()).hexdigest() + ')'
        if len(numbers) > 0:
            number = numbers[0]
        return number

    def extract_dates(self, table: WebElement):
        date_table = []
        rows = table.find_elements_by_tag_name('tr')
        for row in rows[1:]:
            try:
                fields = row.find_elements_by_tag_name('td')
                raw_time = fields[1].text
                times = re.findall('(\d\d:\d\d)', raw_time)

                raw_dates = fields[3].text
                dates = re.findall('(\d\d.\d\d.\d\d\d\d)', raw_dates)

                day = fields[0].text

                rythm = fields[2].text

                from_time = times[0]
                to_time = times[1]

                from_date = dates[0]
                to_date = dates[1]

                room = fields[6].text

                date_table.append((day, rythm, from_time, to_time, from_date, to_date, room))
            except Exception:
                pass
        return date_table

    def extract_parent_data(self, veranstaltung: WebElement):
        parent = veranstaltung.find_element_by_xpath('./../..')
        meta = parent.find_element_by_xpath('following-sibling::div')
        dates = parent.find_element_by_xpath('following-sibling::table')
        active = True
        if 'Inaktiv' in parent.text:
            active = False
        return (veranstaltung, active, meta, dates)

        #
        #
        # input_element = self.driver.find_element_by_xpath("//input[@placeholder='Modultitel / Modulnummer...']")
        # input_element.send_keys(title)
        #
        # search_button = self.driver.find_element_by_partial_link_text('Module suchen')
        # search_button.click()
        #
        #
        # result = self.driver.find_element_by_xpath("//div[contains(@id, 'ergebnisliste')]")
        #
        # date_table = []
        # rows = result.find_elements_by_tag_name('tr')
        # for row in rows[1:]:
        #     try:
        #         fields = row.find_elements_by_tag_name('td')
        #
        # return result.text
