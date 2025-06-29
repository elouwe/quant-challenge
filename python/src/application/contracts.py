# application/contracts.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Type, Optional, TypeVar, Generic
import logging
import time

logger = logging.getLogger(__name__)

# Типы для дженериков
C = TypeVar('C', bound='Command')
R = TypeVar('R')
Q = TypeVar('Q', bound='Query')

class Command:
    """Базовый класс команды для изменения состояния системы."""
    pass

class Query:
    """Базовый класс запроса для получения данных из системы."""
    pass

class Handler(ABC, Generic[C, R]):
    """Абстрактный обработчик команд и запросов."""
    
    @abstractmethod
    def handle(self, request: C) -> R:
        """Обрабатывает переданную команду или запрос."""
        raise NotImplementedError

class Middleware(ABC):
    """Промежуточное ПО для обработки команд/запросов"""
    
    @abstractmethod
    def execute(self, request: Command | Query, next_fn: Callable) -> Any:
        raise NotImplementedError

class LoggingMiddleware(Middleware):
    """Middleware для логирования команд и времени выполнения"""
    
    def execute(self, request: Command | Query, next_fn: Callable) -> Any:
        start_time = time.monotonic()
        logger.info(f"Handling {type(request).__name__}: {request}")
        
        try:
            result = next_fn(request)
            duration = (time.monotonic() - start_time) * 1000
            logger.info(f"Handled {type(request).__name__} in {duration:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Error handling {type(request).__name__}: {str(e)}")
            raise

class ValidationMiddleware(Middleware):
    """Middleware для валидации команд"""
    
    def execute(self, request: Command | Query, next_fn: Callable) -> Any:
        if hasattr(request, 'validate'):
            request.validate()
        return next_fn(request)

class CommandBus:
    """Шина обработки команд с поддержкой middleware"""
    
    def __init__(self, handlers: dict[Type, Handler], middlewares: list[Middleware] = None):
        self.handlers = handlers
        self.middlewares = middlewares or [
            LoggingMiddleware(),
            ValidationMiddleware()
        ]
    
    def dispatch(self, command: Command | Query) -> Any:
        """Выполняет команду через цепочку middleware"""
        handler = self.handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler for command {type(command).__name__}")
        
        def core_handle(cmd):
            return handler.handle(cmd)
        
        # Строим цепочку вызовов middleware
        handle_chain = core_handle
        for middleware in reversed(self.middlewares):
            handle_chain = lambda cmd, mw=middleware, next=handle_chain: mw.execute(cmd, next)
        
        return handle_chain(command)

# Конкретные команды и запросы

@dataclass
class FetchOrderBookCommand(Command):
    """Команда для получения данных стакана"""
    symbol: str
    depth: int = 25
    testnet: bool = True
    
    def validate(self):
        if not self.symbol:
            raise ValueError("Symbol is required")
        if self.depth <= 0:
            raise ValueError("Depth must be positive")

@dataclass
class CalculateDeltaCommand(Command):
    """Команда для расчета дельты ордербука"""
    orderbook: Any  # OrderBookData
    depth: int = 10
    
    def validate(self):
        if not self.orderbook:
            raise ValueError("Orderbook is required")
        if self.depth <= 0:
            raise ValueError("Depth must be positive")

@dataclass
class EvaluateStrategyCommand(Command):
    """Команда для оценки торгового сигнала"""
    delta: float
    threshold: float = 1000.0
    smoothing: int = 5


@dataclass
class ExecuteTradeCommand(Command):
    """Команда для исполнения сделки"""
    signal: str  # BUY/SELL
    price: float
    quantity: float = 0.001
    
    def validate(self):
        if self.signal not in ("BUY", "SELL"):
            raise ValueError("Invalid signal type")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

@dataclass
class GenerateReportCommand(Command):
    """Команда для генерации отчета"""
    symbol: str
    trades: list
    performance: dict

@dataclass
class GetPerformanceQuery(Query):
    """Запрос получения метрик производительности"""
    last_price: float
    iterations: int

# Заглушки

class EmptyCommand(Command):
    """Команда-заглушка без логики"""
    pass

class EmptyQuery(Query):
    """Запрос-заглушка без логики"""
    pass

class EmptyHandler(Handler):
    """Обработчик-заглушка"""
    
    def handle(self, request: Command | Query) -> None:
        return None
