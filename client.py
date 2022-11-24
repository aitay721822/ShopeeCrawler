import logging
import re

from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains


@dataclass
class ProductItem:
    id: str
    img_url: str
    title: str
    price: str
    url: str

class Client:

    def __init__(self, driver_path, logger = logging.getLogger('client')):
        self.logger = logger
        self.regex = re.compile(r'-i\.[0-9]+\.[0-9]+')
        self.default_params = {
            'page': 0,         # page number
            'sortBy': 'ctime', # 時間排序
        }
        self.driver_path = driver_path
        self.driver = self.init_driver()
    
    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        return webdriver.Chrome(self.driver_path, options=options)

    def close_driver(self):
        self.driver.quit()

    def restart_driver(self):
        self.close_driver()
        self.driver = self.init_driver()

    def unique_link(self, link):
        res = self.regex.findall(link)
        if res and len(res) > 0:
            self.logger.debug(f'Generated {res} by {link}')
            return res[0]
        else:
            self.logger.error(f'Failed to generate unique link by {link}, use original link instead')
            return link
    
    def fetch(self, url, **args) -> List[ProductItem]:
        url = urlparse(url)
        # 先取得預設值
        params = self.default_params.copy()
        # 除了頁數，其他參數更新(url)
        params.update({k: ','.join(v) for k, v in parse_qs(url.query).items() if k != 'page'})
        # 更新參數(副程式)
        for k, v in args.items():
            if isinstance(v, list):
                params[k] = ','.join(v)
            else:
                params[k] = v
                
        # 因為 urlencode 會將空格轉成 +，所以直接自幹
        url = urlunparse((url.scheme, url.netloc, url.path, '', '&'.join(f'{k}={v}' for k, v in params.items()), ''))

        self.driver.get(url)
        self.logger.info(f'Fetch {url} to get lastest result')
        main = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "shopee-search-item-result")))
        items = WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "shopee-search-item-result__item")))
        
        # make unload items loaded
        stale_retry = 0
        self.logger.info(f"Load {len(items)} Items")
        while stale_retry < 100:
            try:
                e = main.find_element(By.CLASS_NAME, "shopee-image-placeholder")
                ActionChains(self.driver).move_to_element(e).perform()
            except StaleElementReferenceException:
                stale_retry += 1
                continue
            except NoSuchElementException:
                break
        if stale_retry >= 100: self.logger.error(f"Failed to load all items")

        # get all items
        self.logger.info(f'Loaded {len(items)} items')
        info = []
        for item in items:
            link_element = item.find_element(By.XPATH, "./a[@data-sqe='link']")
            link = link_element.get_attribute("href")
            img = link_element.find_element(By.XPATH, ".//img").get_attribute('src')
            title = link_element.find_element(By.XPATH, './/div[@data-sqe="name"]').text
            price = link_element.find_element(By.XPATH, './/div[@data-sqe="name"]/following-sibling::div').text
            info.append(ProductItem(self.unique_link(link), img, title, price, link))
        return info