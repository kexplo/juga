from dataclasses import dataclass, field

import aiohttp
from pydantic import BaseModel, ConfigDict


@dataclass
class NaverStockMetadata:
    symbol_code: str
    display_name: str
    stock_exchange_code: str
    stock_exchange_name: str
    url: str
    reuters_code: str
    nation_code: str
    nation_name: str
    # is_etf: bool = field(init=False)
    is_global: bool = field(init=False)

    def __post_init__(self):
        # self.is_etf = "etf" in self.url
        self.is_global = self.nation_code != "KOR"


def to_lower_camel(string: str) -> str:
    camel = "".join(word.capitalize() for word in string.split("_"))
    return camel[:1].lower() + camel[1:]


model_config = ConfigDict(alias_generator=to_lower_camel)


class NaverStockAutoCompleteItem(BaseModel):
    model_config = model_config

    code: str
    name: str
    type_code: str
    type_name: str
    url: str
    reuters_code: str
    nation_code: str
    nation_name: str


class NaverStockAutoCompleteResult(BaseModel):
    model_config = model_config

    query: str
    items: list[NaverStockAutoCompleteItem]


class NaverStockAutoCompleteResponse(BaseModel):
    model_config = model_config

    is_success: bool
    detail_code: str
    message: str
    result: NaverStockAutoCompleteResult


class NaverStockMetadataScraper:
    URL_TEMPLATE = "https://m.stock.naver.com/front-api/v1/search/autoComplete?query={query}&target=stock%2Cindex%2Cmarketindicator%2Ccoin"  # noqa: E501

    @classmethod
    async def fetch_metadata(cls, session: aiohttp.ClientSession, query: str) -> tuple[NaverStockMetadata, ...]:
        json_dict = None
        async with session.get(cls.URL_TEMPLATE.format(query=query)) as resp:
            json_dict = await resp.json(content_type=None)

        response = NaverStockAutoCompleteResponse(**json_dict)
        # TODO: check response.is_success

        results: list[NaverStockMetadata] = []
        for item in response.result.items:
            results.append(
                NaverStockMetadata(
                    symbol_code=item.code,
                    display_name=item.name,
                    stock_exchange_code=item.type_code,
                    stock_exchange_name=item.type_name,
                    url=f"https://m.stock.naver.com{item.url}",
                    reuters_code=item.reuters_code,
                    nation_code=item.nation_code,
                    nation_name=item.nation_name,
                )
            )
        return tuple(results)
