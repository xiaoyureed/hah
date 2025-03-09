
from app.clients.binance_client import BinanceF


def test_binance_client():
    client = BinanceF(api_secret="123")
    res = client._hash("hello")
    print(res)
    
    
    pass
