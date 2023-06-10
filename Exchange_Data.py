import dateutil
import datetime


class BalanceData:
    def __init__(self, infos):
        
        self.initial_margin = float(infos['initialMargin'])
        self.maintenance_margin = float(infos['maintMargin'])
        self.margin_balance = float(infos['marginBalance'])
        self.wallet_balance = float(infos['walletBalance'])
        self.unrealized_pnl = float(infos['unrealizedProfit'])


class CandleData:
    def __init__(self, candle_infos):
        
        self.timestamp = candle_infos[0]
        self.open = float(candle_infos[1])
        self.high = float(candle_infos[2])
        self.low = float(candle_infos[3])
        self.close = float(candle_infos[4])
        self.volume = float(candle_infos[5])


class ContractData:
    def __init__(self, contract_infos):
        
        self.symbol = contract_infos['symbol']
        self.base_asset = contract_infos['baseAsset']
        self.quote_asset = contract_infos['quoteAsset']
        self.price_decimals = contract_infos['pricePrecision']
        self.quantity_decimals = contract_infos['quantityPrecision']
        self.tick_size = 1 / pow(10, contract_infos['pricePrecision'])
        self.lot_size = 1 / pow(10, contract_infos['quantityPrecision'])


class OrderStatusData:
    def __init__(self, order_infos):
        
        self.order_id = order_infos['orderId']
        self.status = order_infos['status'].lower()
        self.avg_price = float(order_infos['avgPrice'])
        self.executed_qty = float(order_infos['executedQty'])


class TradeData:
    def __init__(self, trade_infos):
        
        self.time: int = trade_infos['time']
        self.contract: ContractData = trade_infos['contract']
        self.strategy: str = trade_infos['strategy']
        self.side: str = trade_infos['side']
        self.entry_price: float = trade_infos['entry_price']
        self.status: str = trade_infos['status']
        self.pnl: float = trade_infos['pnl']
        self.quantity = trade_infos['quantity']
        self.entry_id = trade_infos['entry_id']






