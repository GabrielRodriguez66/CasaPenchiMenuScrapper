import datetime
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from twilio.rest import Client


class CasaPenchiMenuScrapper:
    CASA_PENCHI_FACEBOOK_URL = "https://www.facebook.com/CasaPenchi/posts"
    LATEST_POST_XPATH = "//div[contains(concat(' ',normalize-space(@class),' '),' userContentWrapper')]"
    SEE_MORE_XPATH = LATEST_POST_XPATH + "//a[@class='see_more_link']"
    LATEST_POST_DATE_XPATH = LATEST_POST_XPATH + "//span[@class='timestampContent']"

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--lang=en")
        self.driver = webdriver.Chrome('./drivers/chromedriver.exe', chrome_options=chrome_options)

    def was_menu_posted_today(self, post_date_element):
        date_split = post_date_element.text.split()
        day, hour = date_split[1], date_split[4]

        if len(day) == 1:
            date_split[1] = '0' + day

        if len(hour.split(':')[0]) == 1:
            date_split[4] = '0' + hour

        post_date = datetime.datetime.strptime(' '.join(date_split), '%B %d at %I:%M %p')
        today = datetime.datetime.now()
        return post_date.day == today.day and post_date.month == post_date.month

    def get_menu_from_facebook(self):
        try:
            self.driver.get(self.CASA_PENCHI_FACEBOOK_URL)
            self.driver.execute_script("window.scrollTo(0, 450)")
            latest_post_date = self.driver.find_element_by_xpath(self.LATEST_POST_DATE_XPATH)

            if self.was_menu_posted_today(latest_post_date):
                # Must click 'see more' to expand
                latest_post_see_more = self.driver.find_element_by_xpath(self.SEE_MORE_XPATH)
                latest_post_see_more.click()
                menu = self.driver.find_element_by_xpath(self.LATEST_POST_XPATH).text
            else:
                menu = 'No se encontró menú de Casa Penchi para el día de hoy.'

        except Exception:
            # An error ocurred during Casa Penchi menu scrapping
            menu = None
        return menu

    def send_sms(self, sms_body, phone_numbers):
        today = datetime.datetime.now()
        # Don't send menu on weekends
        if today.isoweekday() not in [6, 7]:
            client = Client(os.getenv('TWILIO_SID'), os.getenv('AUTH_TOKEN'))
            for number in phone_numbers:
                client.messages.create(to=number, from_=os.getenv('TWILIO_PHONE_NUMBER'), body=sms_body)

    def get_and_send_today_menu(self, phone_numbers):
        sms_body = self.get_menu_from_facebook()
        if sms_body is not None:
            self.send_sms(sms_body, phone_numbers)


if __name__ == '__main__':
    CasaPenchiMenuScrapper().get_and_send_today_menu(phone_numbers=["+17879006598"])
