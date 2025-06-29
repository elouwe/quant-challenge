# application/strategy_service.py
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

class DeltaStrategy:
    """
    Простая стратегия по дельте стакана.
    BUY  – если дельта >  threshold
    SELL – если дельта < -threshold
    HOLD – иначе
    """

    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        logger.info(f"Delta strategy initialized with threshold: {self.threshold}")

    def evaluate(self, delta: float) -> str:
        if delta > self.threshold:
            return "BUY"
        if delta < -self.threshold:
            return "SELL"
        return "HOLD"
