# python\src\domain\order_book.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class OrderBook:
    """Модель стакана ордеров"""
    symbol: str
    timestamp: float
    bids: List[Tuple[float, float]]  # (price, quantity)
    asks: List[Tuple[float, float]]
    
    def get_spread(self) -> float:
        """Вычисляет спред между лучшим бидом и аском"""
        if self.bids and self.asks:
            return self.asks[0][0] - self.bids[0][0]
        return 0.0
    
    def get_mid_price(self) -> float:
        """Вычисляет среднюю цену между лучшим бидом и аском"""
        if self.bids and self.asks:
            return (self.bids[0][0] + self.asks[0][0]) / 2
        return 0.0
