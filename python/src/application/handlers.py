# application/handlers.py
from application.contracts import Handler, FetchOrderBookCommand, CalculateDeltaCommand, EvaluateStrategyCommand, ExecuteTradeCommand, GenerateReportCommand, GetPerformanceQuery
from application.data_service import DataService
from application.strategy_service import DeltaStrategy
from application.backtest_service import Backtester
from application.reporting_service import ReportGenerator
from domain.order_book import OrderBook
import logging

logger = logging.getLogger(__name__)

class FetchOrderBookHandler(Handler[FetchOrderBookCommand, OrderBook]):
    def __init__(self, data_service: DataService):
        self.data_service = data_service
    
    def handle(self, command: FetchOrderBookCommand) -> OrderBook:
        """Обработчик для получения последнего стакана"""
        return self.data_service.latest_orderbook

class CalculateDeltaHandler(Handler[CalculateDeltaCommand, float]):
    def __init__(self, data_service: DataService):
        self.data_service = data_service
    
    def handle(self, command: CalculateDeltaCommand) -> float:
        """Обработчик для расчета дельты стакана"""
        return self.data_service.delta

class StrategyHandler(Handler[EvaluateStrategyCommand, str]):
    def __init__(self, strategy: DeltaStrategy):
        self.strategy = strategy
    
    def handle(self, command: EvaluateStrategyCommand) -> str:
        """Обработчик для генерации торгового сигнала"""
        return self.strategy.evaluate(command.delta)

class TradeHandler(Handler[ExecuteTradeCommand, None]):
    def __init__(self, backtester: Backtester):
        self.backtester = backtester
    
    def handle(self, command: ExecuteTradeCommand) -> None:
        """Обработчик для исполнения торговой операции"""
        self.backtester.execute_trade(
            command.signal, 
            command.price, 
            command.quantity
        )
        logger.info(f"Trade executed: {command.signal} {command.quantity} @ {command.price}")

class ReportHandler(Handler[GenerateReportCommand, None]):
    def __init__(self, reporter: ReportGenerator):
        self.reporter = reporter
    
    def handle(self, command: GenerateReportCommand) -> None:
        """Обработчик для генерации отчетов"""
        self.reporter.generate_report(
            command.symbol, 
            command.trades, 
            command.performance
        )
        logger.info(f"Report generated for {command.symbol}")

class PerformanceHandler(Handler[GetPerformanceQuery, dict]):
    def __init__(self, backtester: Backtester):
        self.backtester = backtester
    
    def handle(self, query: GetPerformanceQuery) -> dict:
        """Обработчик для получения метрик производительности"""
        # Используется только last_price, iterations больше не нужен
        return self.backtester.get_performance_report(query.last_price)
