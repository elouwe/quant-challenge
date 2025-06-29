# Точка входа для реализации
import asyncio
import logging
import sys

import config
from application.data_service import DataService
from application.strategy_service import DeltaStrategy
from application.backtest_service import Backtester
from application.reporting_service import ReportGenerator
from application.contracts import (
    CommandBus, FetchOrderBookCommand, CalculateDeltaCommand,
    EvaluateStrategyCommand, ExecuteTradeCommand, GenerateReportCommand,
    GetPerformanceQuery
)
from application.handlers import (
    FetchOrderBookHandler, CalculateDeltaHandler,
    StrategyHandler, TradeHandler, ReportHandler, PerformanceHandler
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("main")

async def main() -> None:
    data_service: DataService | None = None
    try:
        logger.info("Starting Delta Orderbook Strategy Research")
        logger.info(f"Symbol: {config.SYMBOL}, Testnet: {config.TESTNET}")

        # Init
        data_service = DataService(
            symbol=config.SYMBOL,
            testnet=config.TESTNET,
            use_websocket=config.USE_WEBSOCKET
        )
        strategy   = DeltaStrategy(config.DELTA_THRESHOLD)
        backtester = Backtester(config.INITIAL_BALANCE)
        reporter   = ReportGenerator()

        await data_service.start()
        logger.info("Data ingestion started")

        # Создаем обработчики
        handlers_registry = {
            FetchOrderBookCommand: FetchOrderBookHandler(data_service),
            CalculateDeltaCommand: CalculateDeltaHandler(data_service),
            EvaluateStrategyCommand: StrategyHandler(strategy),
            ExecuteTradeCommand: TradeHandler(backtester),
            GenerateReportCommand: ReportHandler(reporter),
            GetPerformanceQuery: PerformanceHandler(backtester)
        }

        command_bus = CommandBus(handlers_registry)

        counter = 0
        logger.info("Starting backtesting simulation")

        while counter < config.MAX_ITERATIONS:
            counter += 1

            # Получаем стакан через команду
            ob_cmd = FetchOrderBookCommand(symbol=config.SYMBOL, depth=25)
            orderbook = command_bus.dispatch(ob_cmd)

            if not orderbook or not orderbook.bids or not orderbook.asks:
                await asyncio.sleep(1)
                continue

            # Рассчитываем дельту
            delta_cmd = CalculateDeltaCommand(orderbook=orderbook)
            delta = command_bus.dispatch(delta_cmd)

            # Генерируем сигнал
            strategy_cmd = EvaluateStrategyCommand(
                delta=delta, 
                threshold=config.DELTA_THRESHOLD
            )
            signal = command_bus.dispatch(strategy_cmd)

            # Исполняем сделку
            if signal != "HOLD":
                price = orderbook.get_mid_price()
                trade_cmd = ExecuteTradeCommand(
                    signal=signal, 
                    price=price, 
                    quantity=config.TRADE_QUANTITY
                )
                command_bus.dispatch(trade_cmd)
                logger.info(f"Trade executed: {signal} {config.TRADE_QUANTITY} @ {price:.2f}")

            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")

    except Exception:
        logger.exception("Critical error in main loop")

    finally:
        if data_service:
            await data_service.close()

        logger.info("Generating performance report")
        last_price = (
            data_service.latest_orderbook.get_mid_price()
            if data_service and data_service.latest_orderbook else 0.0
        )
        perf_query = GetPerformanceQuery(last_price=last_price, iterations=counter)
        perf = command_bus.dispatch(perf_query)


        report_cmd = GenerateReportCommand(
            symbol=config.SYMBOL,
            trades=backtester.trades,
            performance=perf
        )
        command_bus.dispatch(report_cmd)
        logger.info("Research completed")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
