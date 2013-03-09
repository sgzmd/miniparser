# Loads approved used MINI cars from MINI website and sends email with all
# MINI Countrymans. Code could be cleaner, but hey - it works!

import smtpconfig

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

import logging
import pprint
import re
import smtplib
import time

from time import sleep
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuring very basic logging settings
logging.basicConfig()
logger = logging.getLogger('mini')
logger.setLevel(logging.DEBUG)

def fail(msg):
  logger.warning("Cannot continue: %s", msg)


class MiniDriver:
  """ Controls Selenium and grabs all required data form web pages. """
  def __init__(self):
    self.driver = webdriver.Firefox()
    self.driver.implicitly_wait(30)
    self.base_url = "http://www.minicherished.co.uk"
    self.verificationErrors = []
    self.accept_next_alert = True
    self.extracted_cars = []

  def wait_for_text(self, text):
    """ Waits for specific text to appear on a web page. """
    for i in range(60):
      body = self.driver.find_element_by_css_selector("BODY").text
      if body.find(text) != -1:
        return
      else:
        sleep(1)

    fail("Timed out waiting for text " + text)

  def load_results_page(self):
    """ Main data-loading method. """
    driver = self.driver
    driver.get(self.base_url + "/miniuk/minicherished/homepage/")

    self.wait_for_text("Search for a MINI")

    # filling in MINI search form
    driver.find_element_by_link_text("Model").click()
    driver.find_element_by_link_text("Countryman").click()
    driver.find_element_by_id("scrollHide_0").click()
    driver.find_element_by_link_text("All Countryman").click()
    driver.find_element_by_xpath(
      "//a[@onclick=\"clickOnControlInputText('postcode'); return false;\"]").click()
    sleep(0.2)
    driver.find_element_by_id("input-postcode").clear()
    sleep(0.2)
    driver.find_element_by_id("input-postcode").send_keys("W4 2SQ")
    driver.find_element_by_id("input-postcode").send_keys(Keys.RETURN)
    sleep(0.2)
    driver.find_element_by_css_selector(
      "div.search-info-button-2 > a.bg-black > img").click()
    driver.find_element_by_id("scrollHide_0").click()
    driver.find_element_by_link_text("Transmission").click()
    driver.find_element_by_link_text("Automatic").click()
    driver.find_element_by_link_text("Distance from postcode").click()
    driver.find_element_by_link_text("100 miles").click()
    driver.find_element_by_id("scrollHide_0").click()
    driver.find_element_by_id("check-packagePepper").click()
    driver.find_element_by_id("check-packageChili").click()
    driver.find_element_by_css_selector("#doSearch > a.bg-black > img").click()

    # waiting for results page to load
    self.wait_for_text("Sort cars")

    # why should I sort the list if those guys can do that for me?
    Select(driver.find_element_by_css_selector(
      "td.sort > select")).select_by_visible_text("Price Low to High")

  def is_element_present(self, how, what):
    try:
        self.driver.find_element(by=how, value=what)
    except NoSuchElementException, e:
      return False

    return True

  def get_page_count(self):
    """ Extracts total number of pages in results. """
    pager = self.driver.find_element_by_css_selector("td.pager").text.strip()

    max_page = pager.split("of")[1].strip().split(" ")[0]
    logger.info("Max page: %s", max_page)

    # adding +1 because first (active) page is not a link, just span
    return int(max_page) + 1


  def close_alert_and_get_its_text(self):
    try:
      alert = self.driver.switch_to_alert()
      if self.accept_next_alert:
        alert.accept()
      else:
        alert.dismiss()
      return alert.text
    finally: self.accept_next_alert = True

  def navigate_to_page(self, page):
    """ Navigates to specified page number. """
    self.driver.find_element_by_link_text(str(page)).click()
    sleep(0.5)

  def extract_cars(self):
    """ Extracts cars details from a loaded page. """
    car_results = self.driver.find_elements_by_css_selector("table.car-result")

    for car in car_results:
      model_name = car.find_element_by_css_selector("td.details-1-1-2").text
      specs = car.find_elements_by_css_selector("td.details-1-2")
      specs.extend(car.find_elements_by_css_selector("td.details-2-2"))

      titles = car.find_elements_by_css_selector("td.details-1-1")
      titles.extend(car.find_elements_by_css_selector("td.details-2-1"))

      assert len(specs) == len(titles)

      mini = { 'model': model_name, 'specs': {} }

      for i in range(0, len(specs)):
        name = titles[i].text
        spec = specs[i].text

        mini['specs'][name] = spec


      img = car.find_element_by_css_selector("img").get_attribute("src")
      mini['src'] = img

      logger.info(str(mini))

      self.extracted_cars.append(mini)

  def tearDown(self):
    self.driver.quit()

def main():
  mini = MiniDriver()
  mini.load_results_page()
  logger.info("Page count=%d", mini.get_page_count())

  # loading data from the first page
  mini.extract_cars()

  max_page = mini.get_page_count()

  # loading data from subsequent pages
  for i in range(2,max_page):
    mini.navigate_to_page(i)
    mini.extract_cars()

  mini.tearDown()

  cars = mini.extracted_cars

  # formatting results
  html = u''
  format = u'''
    <table>
    <tr><td><img src="{1}"/></td><td>
    <table>
      <tr style='margin-top: 0.5em'>
        <td>Model Name</td>
        <td><b>{0}</b></td>
      </tr>
      {2}
    </table>
    </td></tr></table>

  '''

  spec_format = u"<tr><td>{0}</td><td>{1}</td></tr>"

  for car in cars:
    specs = car['specs']

    all_specs_html = u''
    for spec_name in specs.keys():
      all_specs_html = all_specs_html + spec_format.format(spec_name, specs[spec_name])


    logger.info(all_specs_html)

    html = html + format.format(car['model'],
                                car['src'],
                                all_specs_html)

  f = open('result.html', 'w')
  f.write(html.encode('utf8'))
  f.close()

  logger.info("Sending email...")
  smtp = smtplib.SMTP('smtp.gmail.com', 587)
  smtp.starttls()
  smtp.login(smtpconfig.USER, smtpconfig.PASS)

  # Create message container - the correct MIME type is multipart/alternative.
  msg = MIMEMultipart('alternative')
  msg['Subject'] = "MINIs"
  msg['From'] = smtpconfig.SENDER
  msg['To'] = smtpconfig.SENDER

  part1 = MIMEText("See HTML part", 'plain')
  part2 = MIMEText(html.encode("utf8"), 'html')

  msg.attach(part1)
  msg.attach(part2)

  logger.info("%s", msg.as_string())

  smtp.sendmail(smtpconfig.SENDER, smtpconfig.RECVS, msg.as_string())
  smtp.quit()

if __name__ == '__main__':
  main()


