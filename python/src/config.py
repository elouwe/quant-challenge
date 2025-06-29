# config.py
# Режим работы
USE_WEBSOCKET = False

# Параметры Bybit
SYMBOL = "ETHUSDT"  # Пробуем другой символ с большей волатильностью
TESTNET = True

# Параметры стратегии
DELTA_THRESHOLD = 0.1  # Уменьшаем порог для чувствительности

# Параметры бэктеста
INITIAL_BALANCE = 10000.0
TRADE_QUANTITY = 0.1  # Увеличиваем количество для заметных сделок

# Сколько тиков симуляции крутим
MAX_ITERATIONS = 100