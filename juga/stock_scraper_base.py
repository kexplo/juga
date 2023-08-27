from abc import ABCMeta, abstractmethod
from typing import Optional

import aiohttp
from pydantic import BaseModel, ConfigDict, Field

from juga.metadata_scraper import NaverStockMetadata
from juga.naver_stock_models import NaverStockChartURLs


class NaverStockData(BaseModel):
    name: str
    name_eng: Optional[str]
    symbol_code: str
    close_price: str
    market_value: Optional[str]
    stock_exchange_name: str
    compare_price: str
    compare_ratio: str
    total_infos: dict[str, Optional[str]]  # TODO: ETF랑 Stock이랑 별도로 정의하면 좋겠다
    chart_urls: NaverStockChartURLs
    url: str

    def __post_init__(self):
        if self.compare_price[0] != "-":
            self.compare_price = "🔺" + self.compare_price
        if self.compare_ratio[0] != "-":
            self.compare_ratio = "🔺" + self.compare_ratio
        self.compare_ratio += "%"


class NaverStockScraperBase(metaclass=ABCMeta):
    def __init__(self, stock_metadata: NaverStockMetadata):
        self.metadata = stock_metadata

    @abstractmethod
    async def _fetch_stock_data_impl(self, session: aiohttp.ClientSession) -> NaverStockData:
        pass

    async def fetch_stock_data(self, session: aiohttp.ClientSession) -> NaverStockData:
        stock_data = await self._fetch_stock_data_impl(session)
        stock_data.url = self.metadata.url
        # workaround for broken korea stock market link
        stock_data.url = stock_data.url.replace("main.nhn", "index.nhn")
        return stock_data
