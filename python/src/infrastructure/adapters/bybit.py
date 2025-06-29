# src/infrastructure/adapters/bybit.py
from __future__ import annotations

import aiohttp
from aiohttp import ClientTimeout
import numpy as np

from domain.order_book import OrderBook


class BybitClient:
    """Мини-клиент для REST-API Bybit Testnet."""

    BASE_URL = "https://api-testnet.bybit.com"

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 200) -> dict:
        """Берём L2-снимок стакана."""
        session = await self._get_session()
        url = f"{self.BASE_URL}/v5/market/orderbook"
        params = {"category": "linear", "symbol": symbol, "limit": limit}

        async with session.get(url, params=params, timeout=ClientTimeout(total=5)) as resp:
            data = await resp.json()
        return data.get("result", {})

    async def calculate_delta(self, prev_: dict, new_: dict) -> float:
        """Δ = (∑ bid_qty − ∑ ask_qty) нового кадра − предыдущего."""
        b_prev = np.array(prev_.get("b", []), dtype=float)
        a_prev = np.array(prev_.get("a", []), dtype=float)
        b_new  = np.array(new_.get("b", []), dtype=float)
        a_new  = np.array(new_.get("a", []), dtype=float)

        delta_prev = b_prev[:, 1].sum() - a_prev[:, 1].sum() if b_prev.size and a_prev.size else 0.0
        delta_new  = b_new[:, 1].sum() - a_new[:, 1].sum() if b_new.size and a_new.size else 0.0
        return float(delta_new - delta_prev)

    # --------------------------------------------------------------------- #
    #                      Вспомогательная конвертация                       #
    # --------------------------------------------------------------------- #

    @staticmethod
    def parse_orderbook(symbol: str, raw: dict) -> OrderBook:
        """Конвертируем JSON в доменную модель."""
        bids_raw = raw.get("b") or raw.get("bids", [])
        asks_raw = raw.get("a") or raw.get("asks", [])
        bids = [(float(p), float(q)) for p, q in bids_raw]
        asks = [(float(p), float(q)) for p, q in asks_raw]
        ts_ms = raw.get("t") or raw.get("ts", 0)
        return OrderBook(symbol, ts_ms / 1_000, bids, asks)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
