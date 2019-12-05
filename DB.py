#!/usr/bin/env python3
# coding=utf-8
# import logging
from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String, DateTime, Numeric, Boolean, BIGINT, FLOAT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from CONFIG import DB_STRING

Base = declarative_base()

class JDItemInforms(Base):
    __tablename__ = 'jditeminfo'
    column_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(BIGINT, nullable=False)
    item_title = Column(String(128))
    item_subtitle = Column(String(512))
    item_url = Column(String(128))
    item_status = Column(String(128))
    show_price = Column(FLOAT)
    plus_price = Column(FLOAT)
    fans_price = Column(FLOAT)
    prom_price = Column(FLOAT)
    prom_discQuota = Column(FLOAT)
    prom_discPar = Column(FLOAT)
    coupon_price = Column(FLOAT)
    coupon_style = Column(BIGINT)
    coupon_discQuota = Column(FLOAT)
    coupon_discPar = Column(FLOAT)
    coupon_discMax = Column(FLOAT)
    item_promotion = Column(String(512))
    update_time = Column(DateTime)

class JDItemMonitor(Base):
    __tablename__ = 'jditemonitor'
    column_id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(BIGINT, nullable=False)
    item_title = Column(String(128))
    item_subtitle = Column(String(512))
    item_url = Column(String(128))
    item_status = Column(String(128))
    show_price = Column(FLOAT)
    plus_price = Column(FLOAT)
    fans_price = Column(FLOAT)
    prom_price = Column(FLOAT)
    prom_discQuota = Column(FLOAT)
    prom_discPar = Column(FLOAT)
    coupon_price = Column(FLOAT)
    coupon_style = Column(BIGINT)
    coupon_discQuota = Column(FLOAT)
    coupon_discPar = Column(FLOAT)
    coupon_discMax = Column(FLOAT)
    item_promotion = Column(String(512))
    update_time = Column(DateTime)

if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    engine = create_engine(DB_STRING, echo=True)
    # engine = create_engine('mysql+pymysql://root:root@localhost/pricemonitor?charset=utf8', echo=True)
    Base.metadata.create_all(engine)