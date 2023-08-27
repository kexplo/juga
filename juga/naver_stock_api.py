from typing import Tuple, Type, TypeVar

import aiohttp
from asyncache import cached
from cachetools import LRUCache

from juga.global_stock_scraper import NaverStockGlobalStockScraper
from juga.korea_stock_scraper import NaverStockKoreaStockScraper
from juga.metadata_scraper import NaverStockMetadata, NaverStockMetadataScraper
from juga.stock_scraper_base import NaverStockData


class InvalidStockQuery(Exception):
    pass


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
        metadata = (await cls.fetch_metadata(query))
        if not metadata:
            raise InvalidStockQuery(f"failed to find stock. query: {query}")
        # pick first one
        return cls(metadata[0])

    @classmethod
    @cached(LRUCache(maxsize=20))
    async def fetch_metadata(cls, query: str) -> Tuple[NaverStockMetadata, ...]:
        async with aiohttp.ClientSession() as session:
            return await NaverStockMetadataScraper.fetch_metadata(session=session, query=query)

    def __init__(self, metadata: NaverStockMetadata):
        self.metadata = metadata
        self.parser = NaverStockScraperFactory.from_metadata(metadata)

    async def fetch_stock_data(self) -> NaverStockData:
        async with aiohttp.ClientSession() as session:
            return await self.parser.fetch_stock_data(session)
