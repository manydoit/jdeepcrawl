from SQL import Sql
import datetime
import matplotlib.pyplot as plt


def main():
    sql = Sql()
    mon_records = sql.read_one_monitor("1268059")
    prices = []
    dates = []
    for mr in mon_records:
        prices.append(mr.coupon_price)
        dates.append(mr.update_time)
    dates_order, prices_order = zip(*sorted(zip(dates, prices)))
    plt.plot(dates_order,'g*', [1,4,9,16], 'ro')
    plt.show()


if __name__ == '__main__':
    main()