from dataclasses import asdict

import aiohttp
import pytest

from juga.metadata_scraper import NaverStockMetadata, NaverStockMetadataScraper

NAVER_METADATA = (
    NaverStockMetadata(
        symbol_code="035420",
        display_name="NAVER",
        stock_exchange_code="KOSPI",
        stock_exchange_name="코스피",
        url="https://m.stock.naver.com/domestic/stock/035420/total",
        reuters_code="035420",
        nation_code="KOR",
        nation_name="대한민국",
    ),
)

MICROSOFT_METADATA = (
    NaverStockMetadata(
        symbol_code="MSFT",
        display_name="Microsoft Corp",
        stock_exchange_code="NASDAQ",
        stock_exchange_name="나스닥 증권거래소",
        url="https://m.stock.naver.com/worldstock/stock/MSFT.O/total",
        reuters_code="MSFT.O",
        nation_code="USA",
        nation_name="미국",
    ),
    NaverStockMetadata(
        symbol_code="04338",
        display_name="Microsoft Corp",
        stock_exchange_code="HONG_KONG",
        stock_exchange_name="홍콩 거래소",
        url="https://m.stock.naver.com/worldstock/stock/4338.HK/total",
        reuters_code="4338.HK",
        nation_code="HKG",
        nation_name="홍콩",
    ),
)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("naver", NAVER_METADATA),
        ("microsoft", MICROSOFT_METADATA),
    ],
)
async def test_fetch_metadata(
    query: str,
    expected: tuple[NaverStockMetadata],
):
    async with aiohttp.ClientSession() as session:
        ret = await NaverStockMetadataScraper.fetch_metadata(session, query)
        assert len(ret) == len(expected)

        for metadata, expected_md in zip(ret, expected):
            assert asdict(metadata) == asdict(expected_md)


@pytest.mark.parametrize(
    ("mockdata_filename", "query", "expected"),
    [
        ("230826_autocomplete_naver_result.json", "naver", NAVER_METADATA),
        ("230826_autocomplete_microsoft_result.json", "microsoft", MICROSOFT_METADATA),
    ],
)
async def test_fetch_metadata_with_mock(
    mockdata_filename: str,
    query: str,
    expected: tuple[NaverStockMetadata],
    mock_aioresponse,
    read_testdata,
):
    mock_aioresponse.get(
        NaverStockMetadataScraper.URL_TEMPLATE.format(query=query),
        payload=read_testdata(mockdata_filename),
    )

    async with aiohttp.ClientSession() as session:
        ret = await NaverStockMetadataScraper.fetch_metadata(session, query)
        assert len(ret) == len(expected)

        for metadata, expected_md in zip(ret, expected):
            assert asdict(metadata) == asdict(expected_md)
