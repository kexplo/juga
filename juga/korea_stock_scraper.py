from typing import Union

import aiohttp
from pydantic import BaseModel

from juga.naver_stock_models import (model_config, NaverStockChartURLs,
                                     NaverStockCompareToPrevious,
                                     NaverStockTradeStopType)
from juga.stock_scraper_base import NaverStockData, NaverStockScraperBase


class NaverKoreaStockExchangeType(BaseModel):
    model_config = model_config

    code: str  # "KS",
    zone_id: str  # "Asia/Seoul",
    nation_type: str  # "KOR",
    delay_time: int  # 0,
    start_time: str  # "0900",
    end_time: str  # "1530",
    close_price_send_time: str  # "1630",
    name_kor: str  # "코스피",
    name_eng: str  # "KOSPI",
    nation_code: str  # "KOR",
    nation_name: str  # "대한민국",
    name: str  # "KOSPI"


class NaverKoreaStockResponse(BaseModel):
    model_config = model_config

    stock_end_type: str  # "stock",
    item_code: str  # "035420",
    reuters_code: str  # "035420",
    stock_name: str  # "NAVER",
    sosok: str  # "0",
    close_price: str  # "211,000",
    compare_to_previous_close_price: str  # "-18,000",
    compare_to_previous_price: NaverStockCompareToPrevious
    fluctuations_ratio: str  # "-7.86",
    market_status: str  # "CLOSE",
    local_traded_at: str  # "2023-08-25T16:10:58+09:00",
    trade_stop_type: NaverStockTradeStopType
    stock_exchange_type: NaverKoreaStockExchangeType
    stock_exchange_name: str  # "KOSPI",

    image_charts: NaverStockChartURLs

    # candleDay",
    # candleWeek",
    # candleMonth",
    # day",
    # areaMonthThree",
    # areaYear",
    # areaYearThree",
    # areaYearTen"
    script_chart_types: list[str]

    delay_time: int  # 0,
    delay_time_name: str  # "실시간",
    end_url: str  # "https://m.stock.naver.com/domestic/stock/035420",
    chart_iq_end_url: str  # "https://m.stock.naver.com/fchart/domestic/stock/035420",
    newly_listed: bool  # false


class NaverStockKoreaStockScraper(NaverStockScraperBase):
    async def _fetch_stock_data_impl(self, session: aiohttp.ClientSession) -> NaverStockData:
        code = self.metadata.symbol_code
        async with session.get(f"https://m.stock.naver.com/api/stock/{code}/basic") as resp:
            resp_json = await resp.json()

        stock_resp = NaverKoreaStockResponse(**resp_json)

        async with session.get(
            f"https://m.stock.naver.com/api/stock/{code}/integration"
        ) as resp:
            info_resp_json = await resp.json()

        total_infos = {}
        market_value = ""
        for info in info_resp_json["totalInfos"]:
            total_infos[info["key"].strip()] = info["value"].strip()
            if info["code"] == "marketValue":
                market_value = info["value"].strip()

        return NaverStockData(
            name=stock_resp.stock_name,
            name_eng=stock_resp.stock_name,
            symbol_code=stock_resp.item_code,
            close_price=stock_resp.close_price,
            market_value=market_value,
            stock_exchange_name=stock_resp.stock_exchange_name,
            compare_price=stock_resp.compare_to_previous_close_price,
            compare_ratio=stock_resp.fluctuations_ratio,
            total_infos=total_infos,  # TODO: ETF랑 Stock이랑 별도로 정의하면 좋겠다
            chart_urls=stock_resp.image_charts,
            url=self.metadata.url,
        )
