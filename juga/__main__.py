import asyncio
from functools import wraps

import typer

from juga.naver_stock_api import NaverStockAPI


app = typer.Typer()


# REF: https://github.com/pallets/click/issues/85
def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@app.command()
@coro
async def stock(ticker: str):
    api = await NaverStockAPI.from_query(ticker)
    typer.echo(f"stock: {ticker}")
    typer.echo(await api.fetch_stock_data())


@app.command()
@coro
async def search(query: str):
    typer.echo(await NaverStockAPI.fetch_metadata(query))


def run_cli():
    app()
