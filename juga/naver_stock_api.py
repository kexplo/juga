from typing import Dict, List, Optional, Tuple, Type, TypedDict, TypeVar

import aiohttp
from asyncache import cached
from cachetools import LRUCache

from juga.korea_stock_scraper import NaverStockKoreaStockScraper
from juga.metadata_scraper import NaverStockMetadata, NaverStockMetadataScraper
from juga.stock_scraper_base import (NaverStockChartURLs, NaverStockData,
                                     NaverStockScraperBase)


class InvalidStockQuery(Exception):
    pass


class NaverStockAPIResponse(TypedDict):
    stockName: str  # noqa: N815
    stockNameEng: str  # noqa: N815
    symbolCode: str  # noqa: N815
    closePrice: str  # noqa: N815
    stockExchangeType: Dict[str, str]  # noqa: N815
    compareToPreviousClosePrice: str  # noqa: N815
    stockItemTotalInfos: List[Dict[str, str]]  # noqa: N815
    fluctuationsRatio: str  # noqa: N815
    imageChartTypes: List[str]  # noqa: N815
    imageCharts: Dict[str, str]  # noqa: N815


class NaverStockGlobalStockScraper(NaverStockScraperBase):
    def _get_url_prefix(self):
        if self.metadata.is_etf:
            return "https://api.stock.naver.com/etf/"
        else:
            return "https://api.stock.naver.com/stock/"

    async def _fetch_stock_data_impl(
        self, session: aiohttp.ClientSession
    ) -> NaverStockData:
        json_dict = None
        async with session.get(
            self._get_url_prefix() + f"{self.metadata.reuters_code}/basic"
        ) as resp:
            json_dict = await resp.json()
        return self.api_response_to_stock_data(json_dict)

    @classmethod
    def api_response_to_stock_data(
        cls, response: NaverStockAPIResponse
    ) -> NaverStockData:
        total_infos: Dict[str, Optional[str]] = {}
        market_value: Optional[str] = None
        for total_info in response["stockItemTotalInfos"]:
            total_infos[total_info["key"]] = total_info.get("value")
            if total_info.get("code") == "marketValue":
                market_value = total_info.get("value")
            # code, key, value[,
            #   compareToPreviousPrice[code(2,5), text(상승,하락), name]]
        image_charts = response["imageCharts"]

        chart_urls = NaverStockChartURLs(
            image_charts.get("candleWeek", ""),
            image_charts.get("candleMonth", ""),
            image_charts.get("day", ""),
            image_charts.get("day_up", ""),
            image_charts.get("day_up_tablet", ""),
            image_charts.get("areaMonthThree", ""),
            image_charts.get("areaYear", ""),
            image_charts.get("areaYearThree", ""),
            image_charts.get("areaYearTen", ""),
            image_charts.get("transparent", ""),
        )

        return NaverStockData(
            response["stockName"],
            response["stockNameEng"],
            response["symbolCode"],
            response["closePrice"],
            market_value,
            response["stockExchangeType"]["name"],
            response["compareToPreviousClosePrice"],
            response["fluctuationsRatio"],
            total_infos,
            chart_urls,
            "",
        )


class NaverStockScraperFactory:
    @classmethod
    def from_metadata(cls, stock_metadata: NaverStockMetadata):
        if stock_metadata.is_global:
            return NaverStockGlobalStockScraper(stock_metadata)
        # kospi, kosdaq
        return NaverStockKoreaStockScraper(stock_metadata)


T = TypeVar("T", bound="NaverStockAPI")


class NaverStockAPI:
    @classmethod
    async def from_query(cls: Type[T], query: str) -> T:
        metadata = (await cls.fetch_metadata(query))[0]
        return cls(metadata)

    @classmethod
    @cached(LRUCache(maxsize=20))
    async def fetch_metadata(
        cls, query: str
    ) -> Tuple[NaverStockMetadata, ...]:
        async with aiohttp.ClientSession() as session:
            return await NaverStockMetadataScraper.fetch_metadata(session=session, query=query)

    def __init__(self, metadata: NaverStockMetadata):
        self.metadata = metadata
        self.parser = NaverStockScraperFactory.from_metadata(metadata)

    async def fetch_stock_data(self) -> NaverStockData:
        async with aiohttp.ClientSession() as session:
            return await self.parser.fetch_stock_data(session)
