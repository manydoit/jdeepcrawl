#!/usr/bin/env python3
# coding=utf-8
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DB import Base, JDItem, JDItemMonitor
import datetime
from CONFIG import DB_STRING

class Sql(object):
    engine = create_engine(DB_STRING, echo=True)
    # engine = create_engine('mysql+pymysql://root:root@localhost/pricemonitor?charset=utf8&autocommit=true')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    def add_one_monitor(self, item_raw):
        time_now = datetime.datetime.now()
        new_item = JDItemMonitor(item_id=item_raw['id'],
                          item_title=item_raw['title'],
                          item_subtitle=item_raw['subtitle'],
                          item_url=item_raw['url'],
                          item_status=item_raw['status'],
                          show_price=item_raw['show_price'],
                          plus_price=item_raw['plus_price'],
                          fans_price=item_raw['fans_price'],
                          prom_price=item_raw['prom_price'],
                          prom_discQuota=item_raw['prom_discQuota'],
                          prom_discPar=item_raw['prom_discPar'],
                          coupon_price=item_raw['coupon_price'],
                          coupon_style=item_raw['coupon_style'],
                          coupon_discQuota=item_raw['coupon_discQuota'],
                          coupon_discPar=item_raw['coupon_discPar'],
                          coupon_discMax=item_raw['coupon_discMax'],
                          item_promotion=item_raw['promotion_info'],
                          update_time=item_raw['update_time'])
        self.session.add(new_item)
        self.session.commit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sql = Sql()
