import pandas as pd
import time
import json
from datetime import datetime
from akshare.request import get

def test_stock_hk_hist():
    """
    测试港股历史数据获取
    """
    df = stock_hk_hist(
        symbol="00593",
        period="daily",
        start_date="20230101",
        end_date="20240101",
        adjust="",
    )
    assert not df.empty
    assert "日期" in df.columns
    assert "开盘" in df.columns
    assert "收盘" in df.columns

def stock_hk_hist(
    symbol: str = "00593",
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "22220101",
    adjust: str = "",
) -> pd.DataFrame:
    """
    东方财富网-行情-港股-每日行情
    https://quote.eastmoney.com/hk/08367.html
    :param symbol: 港股-每日行情
    :type symbol: str
    :param period: choice of {'daily', 'weekly', 'monthly'}
    :type period: str
    :param start_date: 开始日期
    :type start_date: str
    :param end_date: 结束日期
    :type end_date: str
    :param adjust: choice of {"qfq": "1", "hfq": "2", "": "不复权"}
    :type adjust: str
    :return: 每日行情
    :rtype: pandas.DataFrame
    """
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    url = "https://33.push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": f"116.{symbol}",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "end": "20500000",
        "lmt": "1000000",
    }

    r = get(url, params=params)
    data_json = r.json()
    temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
    if temp_df.empty:
        return pd.DataFrame()
    temp_df.columns = [
        "日期",
        "开盘",
        "收盘",
        "最高",
        "最低",
        "成交量",
        "成交额",
        "振幅",
        "涨跌幅",
        "涨跌额",
        "换手率",
    ]
    temp_df.index = pd.to_datetime(temp_df["日期"], errors="coerce")
    temp_df = temp_df[start_date:end_date]
    if temp_df.empty:
        return pd.DataFrame()
    temp_df.reset_index(inplace=True, drop=True)
    temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
    temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
    temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
    temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
    temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
    temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
    temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
    temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
    temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
    temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")
    temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.date
    return temp_df

if __name__ == "__main__":
    df = stock_hk_hist(symbol="00696", period="daily", start_date="20250101", end_date="20250608", adjust="")
    print(df)