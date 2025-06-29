# python\src\application\data_service.py
from __future__ import annotations
import asyncio
import logging
import contextlib  

from infrastructure.adapters.bybit_rest_adapter import BybitRestAdapter

logger = logging.getLogger(__name__)


class DataService:
    """Фасад над BybitRestAdapter, хранит свежий стакан и дельту."""

    def __init__(self, symbol: str, testnet: bool, use_websocket: bool = False):
        self.symbol        = symbol
        self.testnet       = testnet
        self.use_websocket = use_websocket

        self.adapter = BybitRestAdapter(symbol, testnet)
        self._task: asyncio.Task | None = None

    # Публичные свойства

    @property
    def latest_orderbook(self):
        return self.adapter.latest_orderbook

    @property
    def delta(self) -> float:
        return self.adapter.delta

    # Запуск / остановка

    async def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.adapter.start_polling())

    async def close(self):
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self.adapter.close()
