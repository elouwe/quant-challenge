# application/backtest_service.py
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Backtester:
    def __init__(self, initial_balance: float = 10_000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0.0          # в базовой валюте (ETH)
        self.trades: list[dict] = []
        self.start_time: Optional[datetime] = None  # Время начала бэктеста
        self.end_time: Optional[datetime] = None    # Время окончания бэктеста


    def execute_trade(self, side: str, price: float, qty: float, ts: Optional[datetime] = None) -> None:
        """
        Выполняет торговую операцию с проверкой достаточности средств/позиции.
        
        Args:
            side: Направление сделки (BUY/SELL)
            price: Цена актива
            qty: Количество актива
            ts: Временная метка операции (если None - используется текущее время UTC)
        """
        # Установка временной метки
        timestamp = ts if ts else datetime.now(timezone.utc)
        
        # Проверка достаточности баланса для покупки
        if side == "BUY":
            required = price * qty
            if self.balance < required:
                logger.warning(f"Недостаточно средств для покупки: {required:.2f}/{self.balance:.2f}")
                return
            self.balance -= required
            self.position += qty
            
        # Проверка достаточности позиции для продажи
        elif side == "SELL":
            if self.position < qty:
                logger.warning(f"Недостаточно активов для продажи: {qty:.6f}/{self.position:.6f}")
                return
            self.balance += price * qty
            self.position -= qty
            
        else:
            logger.error(f"Неподдерживаемое направление сделки: {side}")
            return

        # Фиксация времени первой и последней сделки
        if not self.start_time:
            self.start_time = timestamp
        self.end_time = timestamp

        # Регистрация сделки
        self.trades.append({
            "ts": timestamp.isoformat(timespec="seconds"),
            "side": side,
            "price": price,
            "qty": qty
        })

    def get_performance_report(self, last_price: float) -> dict:
        """
        Формирует отчет о результатах бэктеста.
        
        Args:
            last_price: Последняя известная цена актива
            
        Returns:
            Словарь с метриками производительности
        """
        # Расчет текущей стоимости позиции
        pos_val = self.position * last_price
        
        # Расчет итогового капитала
        final_val = self.balance + pos_val
        
        # Расчет прибыли/убытка
        pnl = final_val - self.initial_balance
        
        # Форматирование временного периода
        timeframe = "N/A"
        if self.start_time and self.end_time:
            timeframe = f"{self.start_time.isoformat(timespec='seconds')} - {self.end_time.isoformat(timespec='seconds')}"

        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "position": self.position,
            "position_value": pos_val,
            "total_value": final_val,
            "pnl": pnl,
            "pnl_pct": (pnl / self.initial_balance) * 100 if self.initial_balance else 0,
            "total_trades": len(self.trades),
            "timeframe": timeframe,
        }


class OrderBookPoller:
    """
    Класс для периодического опроса стакана через REST API.
    
    Attributes:
        api_url: URL конечной точки API
        symbol: Торговая пара (например, 'ETH-USDT')
        interval: Интервал опроса в секундах
    """
    def __init__(self, api_url: str, symbol: str, interval: int = 5):
        self.api_url = api_url
        self.symbol = symbol
        self.interval = interval
        self.last_poll_time = None

    def fetch_order_book(self) -> dict:
        """
        Запрашивает текущий стакан с биржи.
        
        Returns:
            Словарь с данными стакана в формате:
            {
                'timestamp': datetime.now(timezone.utc),
                'bids': [[цена, объем], ...],
                'asks': [[цена, объем], ...]
            }
        """
        # Здесь должна быть реальная реализация запроса к API
        # Для примера возвращаем заглушку
        current_time = datetime.now(timezone.utc)
        logger.info(f"Получение стакана для {self.symbol} в {current_time.isoformat()}")
        
        return {
            'timestamp': current_time,
            'bids': [[3000.0, 2.5], [2999.5, 3.2]],
            'asks': [[3000.5, 1.8], [3001.0, 2.3]]
        }


class BacktestRunner:
    """
    Координатор процесса бэктестирования.
    
    Attributes:
        backtester: Экземпляр бэктестера
        strategy: Торговая стратегия
        poller: Пуллер стакана
    """
    def __init__(self, backtester: Backtester, strategy: Any, poller: OrderBookPoller):
        self.backtester = backtester
        self.strategy = strategy
        self.poller = poller
        self.is_running = False

    def run(self, duration: int = 60) -> dict:
        """
        Запускает процесс бэктестирования.
        
        Args:
            duration: Длительность теста в секундах
            
        Returns:
            Отчет о производительности
        """
        from time import time, sleep
        self.is_running = True
        start_time = time()
        
        while self.is_running and time() - start_time < duration:
            # Получение данных стакана
            order_book = self.poller.fetch_order_book()
            
            # Получение торговых решений от стратегии
            decision = self.strategy.evaluate(order_book)
            
            # Исполнение сделки при наличии решения
            if decision:
                self.backtester.execute_trade(
                    side=decision['side'],
                    price=decision['price'],
                    qty=decision['qty'],
                    ts=order_book['timestamp']
                )
            
            # Ожидание следующего опроса
            sleep(self.poller.interval)
        
        # Формирование отчета с использованием последней цены
        last_price = self._get_last_price(order_book)
        return self.backtester.get_performance_report(last_price)

    def _get_last_price(self, order_book: dict) -> float:
        """Вычисляет справедливую цену как среднее между лучшим bid и ask."""
        best_bid = order_book['bids'][0][0] if order_book['bids'] else 0
        best_ask = order_book['asks'][0][0] if order_book['asks'] else 0
        return (best_bid + best_ask) / 2 if best_bid and best_ask else 0


class MovingAverageStrategy:
    """
    Пример стратегии: пересечение скользящих средних.
    
    Attributes:
        window_short: Период короткой MA
        window_long: Период длинной MA
        trade_size: Размер позиции для торговли
        price_history: История цен
    """
    def __init__(self, trade_size: float = 0.1):
        self.trade_size = trade_size
        self.price_history = []

    def evaluate(self, order_book: dict) -> Optional[dict]:
        """
        Принимает торговое решение на основе стратегии.
        
        Args:
            order_book: Данные текущего стакана
            
        Returns:
            Торговое решение или None
        """
        # Расчет справедливой цены
        best_bid = order_book['bids'][0][0] if order_book['bids'] else None
        best_ask = order_book['asks'][0][0] if order_book['asks'] else None
        
        if not best_bid or not best_ask:
            return None
        
        mid_price = (best_bid + best_ask) / 2
        self.price_history.append(mid_price)
        
        # Рассчитываем скользящие средние
        if len(self.price_history) >= 50:
            ma_short = sum(self.price_history[-20:]) / 20
            ma_long = sum(self.price_history[-50:]) / 50
            
            # Сигнал на покупку: короткая MA выше длинной
            if ma_short > ma_long:
                return {
                    'side': 'BUY',
                    'price': best_ask,
                    'qty': self.trade_size
                }
            
            # Сигнал на продажу: короткая MA ниже длинной
            elif ma_short < ma_long:
                return {
                    'side': 'SELL',
                    'price': best_bid,
                    'qty': self.trade_size
                }
        
        return None