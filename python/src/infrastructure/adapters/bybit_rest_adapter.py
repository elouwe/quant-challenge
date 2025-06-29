# infrastructure/adapters/bybit_rest_adapter.py
from __future__ import annotations

import asyncio
import logging

from domain.order_book import OrderBook
from .bybit import BybitClient

logger = logging.getLogger(__name__)


class BybitRestAdapter:
    """Периодический поллинг стакана через REST."""

    def __init__(self, symbol: str, testnet: bool, interval: float = 1.0) -> None:
        self.symbol   = symbol
        self.interval = interval
        self.client   = BybitClient()
        self.running  = False

        self.latest_orderbook: OrderBook | None = None
        self.previous_orderbook: OrderBook | None = None
        self.delta: float = 0.0

    async def start_polling(self) -> None:
        if self.running:
            return
        self.running = True
        logger.info(f"Starting orderbook polling for {self.symbol}")

        while self.running:
            try:
                raw = await self.client.fetch_orderbook_snapshot(self.symbol)
                if not raw:
                    logger.warning("Empty snapshot, skip")
                    await asyncio.sleep(self.interval)
                    continue

                ob = self._parse_orderbook(raw)

                self.previous_orderbook = self.latest_orderbook
                self.latest_orderbook   = ob

                if self.previous_orderbook:
                    prev_data = {
                        "b": [[p, q] for p, q in self.previous_orderbook.bids],
                        "a": [[p, q] for p, q in self.previous_orderbook.asks],
                    }
                    new_data = {
                        "b": [[p, q] for p, q in self.latest_orderbook.bids],
                        "a": [[p, q] for p, q in self.latest_orderbook.asks],
                    }
                    self.delta = await self.client.calculate_delta(prev_data, new_data)

                await asyncio.sleep(self.interval)

            except Exception as exc:
                logger.error(f"Polling error: {exc!r}")
                await asyncio.sleep(5)

    async def close(self) -> None:
        self.running = False
        await self.client.close()

    def _parse_orderbook(self, data: dict) -> OrderBook:
        bids_raw = data.get("b") or data.get("bids", [])
        asks_raw = data.get("a") or data.get("asks", [])
        bids = [(float(p), float(q)) for p, q in bids_raw]
        asks = [(float(p), float(q)) for p, q in asks_raw]
        ts_ms = data.get("t") or data.get("ts", 0)
        return OrderBook(self.symbol, ts_ms / 1_000, bids, asks)
