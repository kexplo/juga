from typing import Optional, Union

import aiohttp
from pydantic import BaseModel

from juga.naver_stock_models import model_config, NaverStockCompareToPrevious, NaverStockCurrencyType, NaverStockTradeStopType, NaverStockExchangeType
from juga.stock_scraper_base import NaverStockChartURLs, NaverStockData, NaverStockScraperBase


class NaverStockOverMarketPriceInfo(BaseModel):
    model_config = model_config

    trading_session_type: str  # "AFTER_MARKET",
    over_market_status: str  # "CLOSE",
    over_price: str  # "322.95",
    compare_to_previous_price: NaverStockCompareToPrevious
    compare_to_previous_close_price: str  # "-0.03",
    fluctuations_ratio: str  # "-0.01",
    local_traded_at: str  # "2023-08-25T20:00:00-04:00"


class NaverStockMarketOperatingTimeInfo(BaseModel):
    model_config = model_config

    zone_id: str  # "EST5EDT",
    zone_name: str  # "미국(동부)",
    is_dst: bool  # true,
    pre_market_opening_time: str  # "2023-08-25T04:00:00-04:00",
    pre_market_closing_time: str  # "2023-08-25T09:30:00-04:00",
    regular_market_opening_time: str  # "2023-08-25T09:30:00-04:00",
    regular_market_closing_time: str  # "2023-08-25T16:00:00-04:00",
    after_market_opening_time: str  # "2023-08-25T16:00:00-04:00",
    after_market_closing_time: str  # "2023-08-25T20:00:00-04:00"


class NaverStockIndustryCodeType(BaseModel):
    model_config = model_config

    code: str  # "57201020",
    industry_group_Kor: str  # "소프트웨어",
    name: str  # "INDUSTRY57201020"


class GlobalStockResponse(BaseModel):
    model_config = model_config

    stock_end_type: str  # "stock",
    reuters_code: str  # "MSFT.O",
    fund_name: Optional[str] = None  # Invesco QQQ Trust Seires 1
    stock_name: str  # "마이크로소프트",
    stock_name_eng: str  # "Microsoft Corp",
    symbol_code: str  # "MSFT",
    trade_stop_type: NaverStockTradeStopType
    stock_exchange_type: NaverStockExchangeType
    stock_exchange_name: str  # "NASDAQ",
    industry_code_type: Optional[NaverStockIndustryCodeType] = None
    delay_time: int  # 0,
    delay_time_name: str  # "실시간",
    compare_to_previous_price: NaverStockCompareToPrevious
    close_price: str  # "322.98",
    compare_to_previous_close_price: str  # "3.01",
    fluctuations_ratio: str  # "0.94",
    local_traded_at: str  # "2023-08-25T16:00:00-04:00",
    market_status: str  # "CLOSE",
    over_market_price_info: NaverStockOverMarketPriceInfo

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
    currency_type: NaverStockCurrencyType
    count_of_listed_stock: Optional[int] = None  # 7429763722,
    index_or_etf_tool_tip: Optional[str]  # null,
    stock_end_url: str  # "https://m.stock.naver.com/worldstock/stock/MSFT.O",
    chart_iq_end_url: Optional[str] = None  # "https://m.stock.naver.com/fchart/foreign/stock/MSFT.O",
    stock_item_total_infos: list[dict[str, Union[str, dict]]]
    etf_thema_infos: Optional[str] = None  # null,
    is_etf: bool  # false,
    is_etf_america: bool  # false,
    large_code_name: Optional[str] = None  # "국가",
    middle_code_name: Optional[str] = None  # "선진",
    is_finance_summary: Optional[bool] = None  # true,
    has_news: Optional[bool] = None  # true,
    researchs: Optional[list] = None  # [],
    nation_type: str  # "USA",
    nation_name: str  # "미국",
    newly_listed: Optional[bool] = None  # false,
    market_operating_time_info: NaverStockMarketOperatingTimeInfo
    exchange_operating_time: bool  # false
    exchange_current_time: Optional[str] = None  # "2023-08-26T13:08:44.607992-04:00",


class NaverStockGlobalStockScraper(NaverStockScraperBase):
    # https://api.stock.naver.com/stock/MSFT.O/basic
    # https://api.stock.naver.com/etf/QQQ.O/basic
    STOCK_URL_TEMPLATE = "https://api.stock.naver.com/stock/{code}/basic"
    ETF_URL_TEMPLATE = "https://api.stock.naver.com/etf/{code}/basic"

    def _get_api_url(self):
        if "etf" in self.metadata.url.lower():
            return self.ETF_URL_TEMPLATE.format(code=self.metadata.reuters_code)
        return self.STOCK_URL_TEMPLATE.format(code=self.metadata.reuters_code)

    async def _fetch_stock_data_impl(self, session: aiohttp.ClientSession) -> NaverStockData:
        json_dict = None
        async with session.get(self._get_api_url()) as resp:
            json_dict = await resp.json()

        response = GlobalStockResponse(**json_dict)

        market_value = ""
        total_infos: dict[str, Optional[str]] = {}

        for info in response.stock_item_total_infos:
            total_infos[str(info["key"]).strip()] = str(info["value"]).strip()
            if info["code"] == "marketValue":
                market_value = str(info["value"]).strip()

        return NaverStockData(
            name=response.stock_name,
            name_eng=response.stock_name_eng,
            symbol_code=response.symbol_code,
            close_price=response.close_price,
            market_value=market_value,
            stock_exchange_name=response.stock_exchange_name,
            compare_price=response.compare_to_previous_close_price,
            compare_ratio=response.fluctuations_ratio,
            total_infos=total_infos,
            chart_urls=response.image_charts,
            url=self.metadata.url,
        )
