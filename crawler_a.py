#!/usr/bin/env python3
# coding=utf-8
import re
import logging
from json import decoder
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
import time
import json
from SQL import Sql
import datetime
import pickle
import urllib.request
import json
from CONFIG import TIMEOUT_SLEEP_SEC, JDLOGIN_USERNAME, JDLOGIN_PASSWORD

class Crawler(object):

    def __init__(self, proxy=None):
        chrome_options = Options()
        # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--disable-gpu')
        # 以最高权限运行
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument("--dns-prefetch-disable")
        # 禁用图片加载
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        if proxy:
            proxy_address = proxy['https']
            chrome_options.add_argument('--proxy-server=%s' % proxy_address)
            logging.info('Chrome using proxy: %s', proxy['https'])
        self.chrome = webdriver.Chrome(chrome_options=chrome_options)
        # wait 5 seconds for start session (may delete)
        self.chrome.implicitly_wait(5)
        # set timeout like requests.get()
        # jd sometimes load google pic takes much time
        self.chrome.set_page_load_timeout(20)
        # set timeout for script
        self.chrome.set_script_timeout(20)

    def login_jd(self):
        self.chrome.get('https://passport.jd.com/new/login.aspx')  # JD 登录页面
        time.sleep(TIMEOUT_SLEEP_SEC)  # 等待加载
        self.chrome.find_element_by_css_selector('div.login-tab-r a').click()  # 切换登录按钮
        self.chrome.find_element_by_css_selector('input#loginname').send_keys(JDLOGIN_USERNAME)  # 填写账号
        self.chrome.find_element_by_css_selector('input#nloginpwd').send_keys(JDLOGIN_PASSWORD)  # 填写密码
        self.chrome.find_element_by_css_selector('a#loginsubmit').click()  # 点击登录按钮
        time.sleep(10)
        cookies = self.chrome.get_cookies()
        pickle.dump(cookies, open('cookies.pkl', 'wb'))  # 保存cookies
        return cookies

    def load_cookies(self, cookies=None):
        # 如果没有传入cookies就从硬盘读取
        if cookies is None:
            self.chrome.get("https://www.jd.com")
            cookies = pickle.load(open("cookies.pkl", "rb"))
            if cookies is not None:
                self.chrome.delete_all_cookies()
                for c in cookies:
                    if 'expiry' in c:
                        del c['expiry']
                    self.chrome.add_cookie(c)

    def check_login(self):
        while (True):
            login_check_url = "https://passport.jd.com/loginservice.aspx?callback=jQuery859969&method=Login&_=1575601890704"
            try:
                self.chrome.get(login_check_url)
                login_check_res = self.chrome.find_element_by_tag_name('body').text
                if login_check_res.find(JDLOGIN_USERNAME) < 0:
                    return False
                else:
                    return True
            except TimeoutException as e:
                logging.info('{0} failure: {1}'.format(e, login_check_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue


    def get_jd_rawitem(self, item_id, cookies=None):
        item_raw_dict = {"id": None,
                         "title": None,
                         "subtitle": None,
                         "status": None,
                         "url": None,
                         "show_price": None,
                         "plus_price": None,
                         "fans_price": None,
                         "promotion_info": None,
                         "prom_price": None,
                         "prom_discQuota": None,
                         "prom_discPar": None,
                         "coupon_price": None,
                         "coupon_style": None,
                         "coupon_discQuota": None,
                         "coupon_discPar": None,
                         "coupon_discMax": None,
                         "update_time": None}




        ###############################  Phase1 提取页面基本信息  ###############################
        item_url = 'https://item.jd.com/' + item_id + '.html'
        crawling_phase1 = True
        while(crawling_phase1):
            try:
                self.chrome.get(item_url)
            except TimeoutException as e:
                logging.info('{0} failure: {1}'.format(e, item_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue

            # 复制id
            item_raw_dict['id'] = item_id

            # 提取名称
            try:
                name = self.chrome.find_element_by_xpath("//*[@class='sku-name']").text
                item_raw_dict['title'] = name
            except NoSuchElementException as e:
                return None

            # 提取副标题
            try:
                subtitle = self.chrome.find_element_by_xpath("//*[@id='p-ad']").text
                item_raw_dict['subtitle'] = subtitle
            except NoSuchElementException as e:
                return None

            # 生成url
            item_raw_dict['url'] = 'https://item.jd.com/{0}.html'.format(item_raw_dict['id'])

            # 提取状态(是否下架)
            try:
                status = self.chrome.find_element_by_xpath("//*[@class='itemover-tip']").text
                item_raw_dict['status'] = "stock_over"
            except NoSuchElementException as e:
                item_raw_dict['status'] = None

            # 提取show_price,无该元素，则直接保留为None
            try:
                show_price = self.chrome.find_element_by_xpath("//*[@class='p-price']").text
                if show_price:
                    price_xpath = re.findall(r'-?\d+\.?\d*e?-?\d*?', show_price)
                    if len(price_xpath) > 0:
                        item_raw_dict['show_price'] = float(price_xpath[0])  # 提取浮点数
            except NoSuchElementException as e:
                item_raw_dict['show_price'] = None

            # 提取plus_price,无该元素，则直接保留为None
            try:
                plus_price = self.chrome.find_element_by_xpath("//*[@class='p-price-plus']").text
                if plus_price:
                    plus_price_xpath = re.findall(r'-?\d+\.?\d*e?-?\d*?', plus_price)
                    if len(plus_price_xpath) > 0:
                        item_raw_dict['plus_price'] = float(plus_price_xpath[0])  # 提取浮点数
            except NoSuchElementException as e:
                item_raw_dict['plus_price'] = None

            # 提取fans_price,无该元素，则直接保留为None
            try:
                fans_price = self.chrome.find_element_by_xpath("//*[@class='p-price-fans']").text
                if fans_price:
                    fans_price_xpath = re.findall(r'-?\d+\.?\d*e?-?\d*?', fans_price)
                    if len(fans_price_xpath) > 0:
                        item_raw_dict['fans_price'] = float(fans_price_xpath[0])  # 提取浮点数
            except NoSuchElementException as e:
                item_raw_dict['fans_price'] = None

            crawling_phase1 = False

        # 读js有用的参数
        item_skuid = self.chrome.execute_script("return pageConfig.product.skuid")
        item_cat = self.chrome.execute_script("return pageConfig.product.cat")
        item_venderId = self.chrome.execute_script("return pageConfig.product.venderId")
        item_cat_format = '{0},{1},{2}'.format(item_cat[0], item_cat[1], item_cat[2])

        # 计算basic_price
        basic_price = item_raw_dict['show_price']
        if item_raw_dict['plus_price'] is not None:
            if item_raw_dict['fans_price'] is not None:
                basic_price = min(basic_price, item_raw_dict['plus_price'], item_raw_dict['fans_price'])
            else:
                basic_price = min(basic_price, item_raw_dict['plus_price'])
        else:
            if item_raw_dict['fans_price'] is not None:
                basic_price = min(basic_price, item_raw_dict['fans_price'])

        ###############################  Phase2 提取促销信息  ###############################
        crawling_phase2 = True
        while (crawling_phase2):
            # 提取promotion信息
            prom_url = "https://cd.jd.com/promotion/v2?skuId={0}&area=1_2805_2855_0&cat={1}".format(item_skuid, item_cat_format)
            try:
                self.chrome.get(prom_url)
                prom_res = self.chrome.find_element_by_tag_name('body').text
                json_prom = json.loads(prom_res)
            except TimeoutException as e:
                logging.info('{0} failure: {1}'.format(e, prom_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            except decoder.JSONDecodeError as e:
                logging.info('{0} failure: {1}'.format(e, prom_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            if json_prom['prom'] and json_prom['prom']['pickOneTag']:
                desc2 = []
                for item in json_prom['prom']['pickOneTag']:
                    desc2.append(item['content'])
                item_raw_dict['promotion_info'] = ';'.join(desc2)
            else:
                item_raw_dict['promotion_info'] = ''
            crawling_phase2 = False

        # 从促销信息计算prom_price和相关信息
        mans = re.findall(u'(?<=\u6ee1)\\s*[0-9.]+', item_raw_dict['promotion_info'])
        jians = re.findall(u'(?<=\u51cf)\\s*[0-9.]+', item_raw_dict['promotion_info'])
        if len(mans) > 0 and len(mans) == len(jians):
            pps = []  # 每个满减的估计价格列表
            pmq = []  # prom_discQuota 的候选者列表
            pmp = []  # prom_discPar 的候选者列表
            for i in range(len(mans)):
                par = float(jians[i])
                quo = float(mans[i])
                pp = basic_price - par if basic_price > quo else basic_price * (quo - par) / quo
                pps.append(pp)
                pmq.append(quo)
                pmp.append(par)
            # 比较得到最优惠的
            item_raw_dict['prom_price'] = min(pps)
            midx = pps.index(item_raw_dict['prom_price'])
            item_raw_dict['prom_discQuota'] = pmq[midx]
            item_raw_dict['prom_discPar'] = pmp[midx]
        else:
            item_raw_dict['prom_price'] = basic_price
            item_raw_dict['prom_discQuota'] = None
            item_raw_dict['prom_discPar'] = None
        # 修改basic_price为prom_price(注意 促销信息默认可以叠加)
        basic_price = item_raw_dict['prom_price']

        ###############################  Phase3 提取优惠券信息  ###############################
        json_coupon = None
        crawling_phase3 = True
        while (crawling_phase3):
            waiting_coupon_arrive = False
            cupon_url ="https://cd.jd.com/coupon/service?skuId={0}&cat={1}&venderId={2}".format(item_skuid, item_cat_format, item_venderId)
            try:
                self.chrome.get(cupon_url)
                coupon_res = self.chrome.find_element_by_tag_name('body').text
                json_coupon = json.loads(coupon_res)
            except TimeoutException as e:
                logging.info('{0} failure: {1}'.format(e, cupon_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            except decoder.JSONDecodeError as e:
                logging.info('{0} failure: {1}'.format(e, cupon_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            # 有没领取的，就领取
            if json_coupon is not None and 'skuConpons' in json_coupon:
                for ac in json_coupon['skuConpons']:
                    get_cupon_url = "https://cd.jd.com/coupon/active?skuId={0}&cat={1}&venderId={2}&roleId={3}&key={4}&couponBatchId=&answer=&content=".format(item_skuid,item_cat_format,item_venderId,ac['roleId'],ac['key'])
                    try:
                        self.chrome.get(get_cupon_url)
                        get_coupon_res = self.chrome.find_element_by_tag_name('body').text
                        json_get_coupon = json.loads(get_coupon_res)
                        if json_get_coupon['resultCode'] == 999:
                            waiting_coupon_arrive = True
                    except TimeoutException as e:
                        logging.info('{0} failure: {1}'.format(e, get_cupon_url))
                        time.sleep(TIMEOUT_SLEEP_SEC)
                        continue
                # 这里需要等待2分钟左右
                if waiting_coupon_arrive:
                    logging.info('Waiting 120s for coupons ...')
                    time.sleep(120)
                    # 因为领取了优惠券,重新读取json_coupon
                    crawling_phase3 = True
                else:
                    crawling_phase3 = False
            else:
                crawling_phase3 = False

        # 写入时间
        time_now = datetime.datetime.now()
        item_raw_dict['update_time'] = time_now

        eps = []  # 每张券的估计价格列表
        ems = []  # coupon_style 的候选者列表
        emq = []  # coupon_discQuota 的候选者列表
        emp = []  # coupon_discPar 的候选者列表
        dum = []  # coupon_discMax 的候选者列表
        # 计算每一张可用券的coupon_price,并记录相关信息
        if json_coupon and 'currentSkuConpons' in json_coupon:
            for cc in json_coupon['currentSkuConpons']:
                # 满quota减parValue
                if cc['couponStyle'] == 0 or cc['couponStyle'] == 1:
                    esti = basic_price-cc['parValue'] if basic_price > cc['quota'] else basic_price * (cc['quota'] - cc['parValue']) / cc['quota']
                    eps.append(esti)
                    ems.append(cc['couponStyle'])
                    emq.append(cc['quota'])
                    emp.append(cc['parValue'])
                    dum.append(None)
                # 满quota打discount折,最多减highCount(注意这里实际计算方法)
                if cc['couponStyle'] == 3:
                    esti = basic_price - cc['parValue'] if basic_price > cc['quota'] else basic_price * (cc['quota'] - cc['parValue']) / cc['quota']
                    esti = basic_price - cc['highCount'] if basic_price - esti > cc['highCount'] else esti
                    eps.append(esti)
                    ems.append(cc['couponStyle'])
                    emq.append(cc['quota'])
                    emp.append(cc['parValue'])
                    dum.append(cc['highCount'])
        if len(eps) > 0:
            # 比较得到最优惠的
            item_raw_dict['coupon_price'] = min(eps)
            midx = eps.index(item_raw_dict['coupon_price'])
            item_raw_dict['coupon_style'] = ems[midx]
            item_raw_dict['coupon_discQuota'] = emq[midx]
            item_raw_dict['coupon_discPar'] = emp[midx]
            item_raw_dict['coupon_discMax'] = dum[midx]
        else:
            item_raw_dict['coupon_price'] = basic_price
            item_raw_dict['coupon_style'] = None
            item_raw_dict['coupon_discQuota'] = None
            item_raw_dict['coupon_discPar'] = None
            item_raw_dict['coupon_discMax'] = None

        ###############################  Phase4 提取库存信息  ###############################
        crawling_phase4 = True
        while (crawling_phase4):
            stock_url = "https://c0.3.cn/stock?skuId={0}&area=22_1930_50945_52158&venderId={1}&buyNum=1&cat={2}".format(item_skuid,item_venderId,item_cat_format)
            try:
                self.chrome.get(stock_url)
                stock_res = self.chrome.find_element_by_tag_name('body').text
                json_stock = json.loads(stock_res)
            except TimeoutException as e:
                logging.info('{0} failure: {1}'.format(e, stock_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            except decoder.JSONDecodeError as e:
                logging.info('{0} failure: {1}'.format(e, stock_url))
                time.sleep(TIMEOUT_SLEEP_SEC)
                continue
            if json_stock['stock']['StockState'] == 33:
                item_raw_dict['status'] = "stock_in"
            elif json_stock['stock']['StockState'] == 34:
                item_raw_dict['status'] = "stock_out"
            crawling_phase4 = False

        logging.info('Crawl SUCCESS: {}'.format(item_raw_dict))
        return item_raw_dict


if __name__ == '__main__':
    ############# 下面代码作废 ##################
    logging.basicConfig(level=logging.INFO)
    crawler = Crawler()
    #cookies = crawler.login_jd()
    sql = Sql()
    item_ids = ['8683310', '4624351', '1250262', '1120715', '100003671718']
    item_lowest_prices = [9999999 for i in range(len(item_ids))]
    for i in range(100):
        crawler.load_cookies()
        for j in range(len(item_ids)):
            item_raw = crawler.get_jd_rawitem(item_ids[j])
            sql.add_one_monitor(item_raw)
            if item_raw['coupon_price'] < item_lowest_prices[j]:
                item_lowest_prices[j] = item_raw['coupon_price']
        logging.info('Waiting 300s for starting {0} iteration ...'.format(i+2))
        time.sleep(1800)

