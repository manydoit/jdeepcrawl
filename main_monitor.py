from wxpy import *
from SQL import Sql
from crawler_a import Crawler
import time, datetime
import json
from CONFIG import CR_ITERATIONS, CR_SLEEP_SEC

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
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


    bot = Bot()
    my_friend = bot.friends().search('solo', sex=MALE)[0]
    my_friend.send('小蒐开始工作!\n目标商品:{0}个;\n监控次数:{1}轮;\n间隔时长:{2}秒\n{3}'.format(len(item_ids), CR_ITERATIONS, CR_SLEEP_SEC, datetime.datetime.now()))

    for i in range(CR_ITERATIONS):
        crawler.load_cookies()
        for j in range(len(item_ids)):
            time.sleep(1)
            item_raw = crawler.get_jd_rawitem(item_ids[j])
            # 加入一条监控数据库记录
            sql.add_one_monitor(item_raw)
            if item_raw['coupon_price'] < item_lowest_prices[j]:
                # 发送破低价消息
                my_friend.send('破最低价提示! {0}!\n原低价约{1:.2f}元;\n现低价约{2:.2f}元.\n{3}\n{4}\n{5}'.format(
                    item_raw['status'],
                    item_lowest_prices[j],
                    item_raw['coupon_price'],
                    item_raw['url'],
                    item_raw['title'],
                    item_raw['update_time']))
                # 更新item_lowest_prices
                item_lowest_prices[j] = item_raw['coupon_price']
                # 更新商品信息数据库记录
                sql.add_update_one_info(item_raw)
            else:
                if item_raw['coupon_price'] < item_latest_prices[j]:
                    my_friend.send('降价提示! {0}!\n上轮价约{1:.2f}元;\n现降为约{2:.2f}元,{2}.\n{3}\n{4}\n{5}'.format(
                        item_raw['status'],
                        item_latest_prices[j],
                        item_raw['coupon_price'],
                        item_raw['url'],
                        item_raw['title'],
                        item_raw['update_time']))
            item_latest_prices[j] = item_raw['coupon_price']
        logging.info('Waiting {0}s to start {1} iteration ...'.format(CR_SLEEP_SEC, i+2))
        time.sleep(CR_SLEEP_SEC)
