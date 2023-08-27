import asyncio
from functools import wraps

import typer

from juga.naver_stock_api import NaverStockAPI, InvalidStockQuery


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
    try:
        api = await NaverStockAPI.from_query(ticker)
    except InvalidStockQuery:
        typer.echo(f"failed to find stock. query: {ticker}")
        raise typer.Exit(code=1)
    typer.echo(f"stock: {ticker}")
    typer.echo(await api.fetch_stock_data())


@app.command()
@coro
async def search(query: str):
    typer.echo(await NaverStockAPI.fetch_metadata(query))


def run_cli():
    app()
