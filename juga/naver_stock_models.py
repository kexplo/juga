from pydantic import BaseModel, ConfigDict, Field


def to_lower_camel(string: str) -> str:
    camel = "".join(word.capitalize() for word in string.split("_"))
    return camel[:1].lower() + camel[1:]


model_config = ConfigDict(alias_generator=to_lower_camel)


class NaverStockChartURLs(BaseModel):
    model_config = model_config

    candle_day: str  # 일봉
    candle_week: str  # 주봉
    candle_month: str  # 월봉
    day: str  # 1일
    day_up: str = Field(alias="day_up")
    day_up_tablet: str = Field(alias="day_up_tablet")
    area_month_three: str  # 3개월
    area_year: str  # 1년
    area_year_three: str  # 3년
    area_year_ten: str  # 10년
    transparent: str


class NaverStockCodeType(BaseModel):
    code: str  # "5",
    text: str  # "하락",
    name: str  # "FALLING"


class NaverStockCompareToPrevious(NaverStockCodeType):
    # code: "5",
    # text: "하락",
    # name: "FALLING"
    pass


class NaverStockCurrencyType(NaverStockCodeType):
    # code: "USD",
    # text: "US dollar",
    # name: "USD"
    pass


class NaverStockTradeStopType(NaverStockCodeType):
    # code: "1",
    # text: "운영.Trading",
    # name: "TRADING"
    pass


class NaverStockExchangeType(BaseModel):
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
