from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Type, TypedDict, TypeVar

import aiohttp
from asyncache import cached
from bs4 import BeautifulSoup
from cachetools import LRUCache


class InvalidStockQuery(Exception):
    pass


@dataclass
class NaverStockMetadata:
    symbol_code: str
    display_name: str
    stock_exchange_name: str
    url: str
    reuters_code: str
    is_etf: bool = field(init=False)
    is_global: bool = field(init=False)

    def __post_init__(self):
        self.is_etf = "etf" in self.url
        self.is_global = self.stock_exchange_name not in ["코스피", "코스닥"]


@dataclass
class NaverStockData:
    name: str
    name_eng: Optional[str]
    symbol_code: str
    close_price: str
    market_value: Optional[str]
    stock_exchange_name: str
    compare_price: str
    compare_ratio: str
    total_infos: Dict[str, Optional[str]]  # TODO: ETF랑 Stock이랑 별도로 정의하면 좋겠다
    day_graph_url: str
    candle_graph_url: str
    url: str = field(init=False)

    def __post_init__(self):
        if self.compare_price[0] != "-":
            self.compare_price = "🔺" + self.compare_price
        if self.compare_ratio[0] != "-":
            self.compare_ratio = "🔺" + self.compare_ratio
        self.compare_ratio += "%"


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


class NaverStockAPIParser(metaclass=ABCMeta):
    def __init__(self, stock_metadata: NaverStockMetadata):
        self.metadata = stock_metadata

    @abstractmethod
    async def _fetch_stock_data_impl(
        self, session: aiohttp.ClientSession
    ) -> NaverStockData:
        pass

    async def fetch_stock_data(
        self, session: aiohttp.ClientSession
    ) -> NaverStockData:
        stock_data = await self._fetch_stock_data_impl(session)
        stock_data.url = self.metadata.url
        # workaround for broken korea stock market link
        stock_data.url = stock_data.url.replace('main.nhn', 'index.nhn')
        return stock_data


class NaverStockAPIGlobalStockParser(NaverStockAPIParser):
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
            image_charts["day"],
            image_charts["candleMonth"],
        )


class NaverStockAPIKoreaStockParser(NaverStockAPIParser):
    async def _fetch_stock_data_impl(
        self, session: aiohttp.ClientSession
    ) -> NaverStockData:
        code = self.metadata.symbol_code
        async with session.get(
            "https://m.stock.naver.com/api/item/getOverallHeaderItem.nhn"
            f"?code={code}"
        ) as resp:
            header_json = (await resp.json())["result"]

        async with session.get(
            "https://m.stock.naver.com/api/html/item/getOverallInfo.nhn"
            f"?code={code}"
        ) as resp:
            html = await resp.text()

        name = header_json["nm"]
        time = header_json["time"]
        symbol_code = header_json["cd"]
        close_price = f'{header_json["nv"]:,}'
        compare_price = f'{header_json["cv"]:,}'
        compare_ratio = f'{header_json["cr"]:,}'
        stock_exchange_name = self.metadata.stock_exchange_name

        soup = BeautifulSoup(html, "html.parser")
        total_info_lis = soup.select("ul.total_list > li")
        total_infos = {
            li.find("div").text.strip(): li.find("span").text.strip()
            for li in total_info_lis
        }

        image_chart_types = [
            li.find("span").text.strip()
            for li in soup.select("ul.lnb_lst > li")
        ]
        # 클라이언트에서 이미지 캐시되는 것을 막기 위해
        # 유효하지 않지만 URL 뒤에 '?time' 인자를 덧붙인다
        charts = [
            img.attrs["data-src"] + f"?{time}"
            for img in soup.select("div.flick-ct * > img")
        ]
        image_charts = {
            img_type: chart
            for img_type, chart in zip(image_chart_types, charts)
        }
        return NaverStockData(
            name,
            None,
            symbol_code,
            close_price,
            total_infos.get("시총"),
            stock_exchange_name,
            compare_price,
            compare_ratio,
            total_infos,
            image_charts["1일"],
            image_charts["일봉"],
        )


class NaverStockAPIParserFactory:
    @classmethod
    def from_metadata(cls, stock_metadata: NaverStockMetadata):
        if stock_metadata.is_global:
            return NaverStockAPIGlobalStockParser(stock_metadata)
        # kospi, kosdaq
        return NaverStockAPIKoreaStockParser(stock_metadata)


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
        url_tmpl = "https://ac.finance.naver.com/ac?q={query}&q_enc=euc-kr&t_koreng=1&st=111&r_lt=111"  # noqa: E501
        json_dict = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url_tmpl.format(query=query)) as resp:
                json_dict = await resp.json(content_type=None)

        items: List[Tuple[str, ...]] = []
        for group in json_dict["items"]:
            for group_item in group:  # type: List[List[str]]
                items.append(tuple(i[0] for i in group_item))

        results: List[NaverStockMetadata] = []
        for item in items:
            symbol_code, display_name, market, url, reuters_code = item
            results.append(
                NaverStockMetadata(
                    symbol_code,
                    display_name,
                    market,
                    f"https://m.stock.naver.com{url}",
                    reuters_code,
                )
            )
        return tuple(results)

    def __init__(self, metadata: NaverStockMetadata):
        self.metadata = metadata
        self.parser = NaverStockAPIParserFactory.from_metadata(metadata)

    async def fetch_stock_data(self) -> NaverStockData:
        async with aiohttp.ClientSession() as session:
            return await self.parser.fetch_stock_data(session)
