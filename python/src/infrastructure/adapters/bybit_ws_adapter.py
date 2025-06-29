# infrastructure/adapters/bybit_ws_adapter.py
import websockets
import json
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BybitWSAdapter:
    def __init__(self, symbol="BTCUSDT", testnet=True):
        # Выбор URL в зависимости от режима (testnet/production)
        self.ws_url = "wss://stream-testnet.bybit.com/realtime" if testnet else "wss://stream.bybit.com/realtime"
        self.symbol = symbol
        self.is_connected = False
        
    async def stream_orderbook(self, queue: asyncio.Queue):
        """Асинхронный поток данных стакана с Bybit"""
        logger.info(f"Connecting to Bybit WebSocket: {self.ws_url}")
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self.is_connected = True
                    # Подписка на канал стакана
                    await ws.send(json.dumps({
                        "op": "subscribe",
                        "args": [f"orderBookL2_25.{self.symbol}"]
                    }))
                    logger.info(f"Subscribed to orderBookL2_25.{self.symbol}")
                    
                    while True:
                        try:
                            # Получение данных с таймаутом
                            data = await asyncio.wait_for(ws.recv(), timeout=10)
                            json_data = json.loads(data)
                            
                            # Добавление временной метки
                            if 'data' in json_data:
                                json_data['timestamp'] = datetime.now(timezone.utc)
                            
                            await queue.put(json_data)
                        except asyncio.TimeoutError:
                            logger.warning("WebSocket timeout, reconnecting...")
                            await self._reconnect(ws)
                        except json.JSONDecodeError:
                            logger.error("JSON decode error", exc_info=True)
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed unexpectedly")
                self.is_connected = False
                await asyncio.sleep(5)  # Пауза перед переподключением
            except Exception as e:
                logger.error("WebSocket connection failed", exc_info=True)
                self.is_connected = False
                await asyncio.sleep(10)  # Большая пауза при критических ошибках

    async def _reconnect(self, ws):
        """Обработка переподключения при таймауте"""
        try:
            await ws.close()
            self.is_connected = False
        except:
            pass
        await asyncio.sleep(1)
