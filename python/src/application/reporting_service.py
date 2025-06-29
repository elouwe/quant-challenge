# application/reporting_service.py
import logging
import csv

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Генератор итогового txt-отчёта и CSV с трейдами."""

    def generate_report(self, symbol: str, trades: list, performance: dict) -> None:
        # Генерация текстового отчета 
        report = (
            "\n==================== RESEARCH REPORT ====================\n"
            "Strategy: Orderbook Delta Momentum\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {performance.get('timeframe', 'N/A')}\n"
            f"Total Iterations: {performance.get('iterations', 0)}\n"
            "---------------------------------------------------------\n"
            "Performance Metrics:\n"
            f"Initial Balance: ${performance['initial_balance']:.2f}\n"
            f"Final Balance:   ${performance['final_balance']:.2f}\n"
            f"Position:        {performance['position']:.6f} {symbol[:-4]}\n"
            f"Position Value:  ${performance['position_value']:.2f}\n"
            f"Total Value:     ${performance['total_value']:.2f}\n"
            f"PNL:             ${performance['pnl']:.2f}\n"
            f"Total Trades:    {performance['total_trades']}\n"
            "---------------------------------------------------------\n"
            "Conclusion: This research demonstrates a basic strategy\n"
            "based on orderbook delta momentum. The strategy showed\n"
            f"a {'profit' if performance['pnl'] > 0 else 'loss'} "
            f"of ${abs(performance['pnl']):.2f} over "
            f"{performance.get('iterations', 0)} iterations.\n"
            "=========================================================\n"
        )

        with open("research_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(report)
        
        # Генерация CSV с трейдами
        if trades:
            csv_filename = "trades_report.csv"
            with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["timestamp", "side", "price", "quantity"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for trade in trades:
                    writer.writerow({
                        "timestamp": trade["ts"],
                        "side": trade["side"],
                        "price": trade["price"],
                        "quantity": trade["qty"]
                    })
            logger.info(f"Saved {len(trades)} trades to {csv_filename}")
        else:
            logger.info("No trades to save in CSV")
