from SQL import Sql
from crawler_a import Crawler
import time, datetime
import json
from CONFIG import CR_ITERATIONS, CR_SLEEP_SEC
from wx_adb import WXadb
import logging
from xpinyin import Pinyin

def main():
    MAX_PRICE = 9999999.00
    crawler = Crawler()

    # 需要时才运行一次
    #cookies = crawler.login_jd()

    sql = Sql()

    with open("item_id_list.json", 'r') as load_f:
        item_ids = json.load(load_f)

    # 读商品信息数据库记录，更新item_lowest_prices和item_latest_prices
    item_lowest_prices = []
    item_latest_prices = []
    for i in range(len(item_ids)):
        info_item = sql.read_one_info(item_ids[i])
        if info_item:
            item_lowest_prices.append(info_item.coupon_price)
            item_latest_prices.append(info_item.coupon_price)
        else:
            item_lowest_prices.append(MAX_PRICE)
            item_latest_prices.append(MAX_PRICE)

    wxadb = WXadb()
    wxadb.add_device("f51e6c3a")
    pinyin = Pinyin()

    wxadb.send_WX_msg('xso message>> target numbers:{0}; iteration times:{1}; interval seconds:{2} {3}'.format(len(item_ids), CR_ITERATIONS, CR_SLEEP_SEC,
                                                                            datetime.datetime.now()))
    n_error_time = 0
    for i in range(CR_ITERATIONS):
        crawler.load_cookies()
        if not crawler.check_login():
            wxadb.send_WX_msg('xso warning>> JD login failed! {0}'.format(datetime.datetime.now()))
            return False
        for j in range(len(item_ids)):
            time.sleep(1)
            item_raw = crawler.get_jd_rawitem(item_ids[j])
            # 如果爬取的该条数据不完整
            if not item_raw or not item_raw['coupon_price']:
                n_error_time += 1
                continue
            if n_error_time > 10:
                wxadb.send_WX_msg('xso warning>> several times failed and quit! {0}'.format(datetime.datetime.now()))
                return False
            # 加入一条监控数据库记录
            sql.add_one_monitor(item_raw)

            # 破低价（有货）
            if item_raw['coupon_price'] < item_lowest_prices[j]:
                if item_lowest_prices[j] != MAX_PRICE and item_raw['status'] == 'stock_in':
                    wxadb.send_WX_msg('xso message>> {0} history lowest price:{1:.2f}yuan, current price:{2:.2f}yuan. {3} {4}'.format(
                        pinyin.get_pinyin(item_raw['title'], ''),
                        item_lowest_prices[j],
                        item_raw['coupon_price'],
                        item_raw['url'],
                        item_raw['update_time']))
                # 更新item_lowest_prices
                item_lowest_prices[j] = item_raw['coupon_price']
                # 更新商品信息数据库记录
                sql.add_update_one_info(item_raw)
            # 降价
            elif item_raw['coupon_price'] < item_latest_prices[j]:
                if item_latest_prices[j] != MAX_PRICE and item_raw['status'] == 'stock_in':
                    wxadb.send_WX_msg('xso message>> {0} last price:{1:.2f}yuan, current price:{2:.2f}yuan. {3} {4}'.format(
                        pinyin.get_pinyin(item_raw['title'], ''),
                        item_latest_prices[j],
                        item_raw['coupon_price'],
                        item_raw['url'],
                        item_raw['update_time']))
            item_latest_prices[j] = item_raw['coupon_price']
        logging.info('Waiting {0}s to start {1} iteration ...'.format(CR_SLEEP_SEC, i + 2))
        wxadb.send_WX_msg('xso message>> {0} iteration finished. {1}'.format(i+1, datetime.datetime.now()))
        time.sleep(CR_SLEEP_SEC)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
