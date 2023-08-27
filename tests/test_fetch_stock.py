import aiohttp

from juga.metadata_scraper import NaverStockMetadata
from juga.naver_stock_api import NaverStockGlobalStockScraper, NaverStockKoreaStockScraper
from juga.stock_scraper_base import NaverStockData


async def test_fetch_korea_stock(mock_aioresponse, read_testdata):
    expected_basic = read_testdata("230826_m_api_basic_naver_result.json")

    mock_aioresponse.get("https://m.stock.naver.com/api/stock/035420/basic", payload=expected_basic)

    expected_integration = read_testdata("230826_m_api_integration_naver_result.json")

    mock_aioresponse.get("https://m.stock.naver.com/api/stock/035420/integration", payload=expected_integration)

    metadata = NaverStockMetadata(
        symbol_code="035420",
        display_name="NAVER",
        stock_exchange_code="KOSPI",
        stock_exchange_name="코스피",
        url="https://m.stock.naver.com/domestic/stock/035420/total",
        reuters_code="035420",
        nation_code="KOR",
        nation_name="대한민국",
    )

    scraper = NaverStockKoreaStockScraper(metadata)

    expected_json = '{"name":"NAVER","name_eng":"NAVER","symbol_code":"035420","close_price":"211,000","market_value":"34조 6,144억","stock_exchange_name":"KOSPI","compare_price":"-18,000","compare_ratio":"-7.86","total_infos":{"전일":"229,000","시가":"221,500","고가":"222,000","저가":"210,500","거래량":"2,059,768","대금":"442,787백만","시총":"34조 6,144억","외인소진율":"47.00%","52주 최고":"246,500","52주 최저":"155,000","PER":"47.51배","EPS":"4,441원","추정PER":"35.14배","추정EPS":"6,004원","PBR":"1.41배","BPS":"149,954원","배당수익률":"0.43%","주당배당금":"914원"},"chart_urls":{"candleDay":"https://ssl.pstatic.net/imgfinance/chart/mobile/candle/day/035420_end.png?1692947458000","candleWeek":"https://ssl.pstatic.net/imgfinance/chart/mobile/candle/week/035420_end.png?1692947458000","candleMonth":"https://ssl.pstatic.net/imgfinance/chart/mobile/candle/month/035420_end.png?1692947458000","day":"https://ssl.pstatic.net/imgfinance/chart/mobile/day/035420_end.png?1692947458000","day_up":"https://ssl.pstatic.net/imgfinance/chart/mobile/mini/035420_end_up.png?1692947458000","day_up_tablet":"https://ssl.pstatic.net/imgfinance/chart/mobile/mini/035420_end_up_tablet.png?1692947458000","areaMonthThree":"https://ssl.pstatic.net/imgfinance/chart/mobile/area/month3/035420_end.png?1692947458000","areaYear":"https://ssl.pstatic.net/imgfinance/chart/mobile/area/year/035420_end.png?1692947458000","areaYearThree":"https://ssl.pstatic.net/imgfinance/chart/mobile/area/year3/035420_end.png?1692947458000","areaYearTen":"https://ssl.pstatic.net/imgfinance/chart/mobile/area/year10/035420_end.png?1692947458000","transparent":"https://ssl.pstatic.net/imgfinance/chart/mobile/mini/035420_transparent.png?1692947458000"},"url":"https://m.stock.naver.com/domestic/stock/035420/total"}'  # noqa: E501
    expected_result = NaverStockData.model_validate_json(expected_json)

    async with aiohttp.ClientSession() as session:
        result = await scraper.fetch_stock_data(session)
        assert dict(result) == dict(expected_result)


async def test_fetch_global_stock(mock_aioresponse, read_testdata):
    expected_basic = read_testdata("230826_api_basic_msft_result.json")
    mock_aioresponse.get("https://api.stock.naver.com/stock/MSFT.O/basic", payload=expected_basic)

    metadata = NaverStockMetadata(
        symbol_code="MSFT",
        display_name="Microsoft Corp",
        stock_exchange_code="NASDAQ",
        stock_exchange_name="나스닥 증권거래소",
        url="https://m.stock.naver.com/worldstock/stock/MSFT.O/total",
        reuters_code="MSFT.O",
        nation_code="USA",
        nation_name="미국",
    )

    scraper = NaverStockGlobalStockScraper(metadata)

    expected_json = '{"name":"마이크로소프트","name_eng":"Microsoft Corp","symbol_code":"MSFT","close_price":"322.98","market_value":"2조 3,997억 USD","stock_exchange_name":"NASDAQ","compare_price":"3.01","compare_ratio":"0.94","total_infos":{"전일":"319.97","시가":"321.47","고가":"325.36","저가":"318.80","거래량":"21,684,104","대금":"70억 USD","시총":"2조 3,997억 USD","업종":"소프트웨어","52주 최고":"366.78","52주 최저":"213.43","PER":"32.91배","EPS":"9.81","PBR":"11.64배","BPS":"27.75","주당배당금":"2.72","배당수익률":"0.85%","배당일":"2023.09.14.","배당락일":"2023.08.16.","액면변경":"N/A","액면가":"N/A"},"chart_urls":{"candleDay":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/candle/day/MSFT.O_end.png?1692946800000","candleWeek":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/candle/week/MSFT.O_end.png?1692946800000","candleMonth":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/candle/month/MSFT.O_end.png?1692946800000","day":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/MSFT.O_end.png?1692946800000","day_up":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/MSFT.O_end_up.png?1692946800000","day_up_tablet":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/MSFT.O_end_up_tablet.png?1692946800000","areaMonthThree":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/area/month3/MSFT.O_end.png?1692946800000","areaYear":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/area/year/MSFT.O_end.png?1692946800000","areaYearThree":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/area/year3/MSFT.O_end.png?1692946800000","areaYearTen":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/area/year10/MSFT.O_end.png?1692946800000","transparent":"https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/MSFT.O_transparent.png?1692946800000"},"url":"https://m.stock.naver.com/worldstock/stock/MSFT.O/total"}'  # noqa: E501
    expected_result = NaverStockData.model_validate_json(expected_json)

    async with aiohttp.ClientSession() as session:
        result = await scraper.fetch_stock_data(session)
        assert dict(result) == dict(expected_result)
