import logging
import requests
import time
import typing
import collections

from urllib.parse import urlencode

import hmac
import hashlib

import websocket
import json

import threading

from Exchange_Data import *
from Strategies import TechnicalStrategy, BreakoutStrategy


logger = logging.getLogger()


class BinanceClient:
    def __init__(self, public_key: str, secret_key: str):

        """
        https://binance-docs.github.io/apidocs/futures/en
        :param public_key:
        :param secret_key:
        """

        
        self._main_url = "https://testnet.binancefuture.com"
        self._ws_url = "wss://stream.binancefuture.com/ws"
                

        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        self.logs = []

        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnected = True
        self.ws_connected = False
        self.ws_subscriptions = {"bookTicker": [], "aggTrade": []}

        thr = threading.Thread(target=self._start_ws)
        thr.start()

        logger.info("Binance Futures Testnet Client successfully started")

    def _add_log(self, msg: str):

        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    def _generate_signature(self, data: typing.Dict) -> str:

        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    def _do_request(self, method: str, endpoint: str, data: typing.Dict):

        if method == "GET":
            try:
                response = requests.get(self._main_url + endpoint, params=data, headers=self._headers)
            except Exception as e:  # Takes into account any possible error, most likely network errors
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "POST":
            try:
                response = requests.post(self._main_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "DELETE":
            try:
                response = requests.delete(self._main_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError()

        if response.status_code == 200:  # 200 is the response code of successful requests
            return response.json()
        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self) -> typing.Dict[str, ContractData]:

        exchange_info = self._do_request("GET", "/fapi/v1/exchangeInfo", dict())

        contracts = dict()

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['symbol']] = ContractData(contract_data)

        return collections.OrderedDict(sorted(contracts.items()))  # Sort keys of the dictionary alphabetically

    def get_historical_candles(self, contract: ContractData, interval: str) -> typing.List[CandleData]:

        params_data = dict()
        params_data['symbol'] = contract.symbol
        params_data['interval'] = interval
        params_data['limit'] = 1000  

        raw_candles = self._do_request("GET", "/fapi/v1/klines", params_data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append(CandleData(c, interval))

        return candles

    def get_bid_ask(self, contract: ContractData) -> typing.Dict[str, float]:

        params_data = dict()
        params_data['symbol'] = contract.symbol

        
        ob_data = self._do_request("GET", "/fapi/v1/ticker/bookTicker", params_data)

        if ob_data is not None:
            if contract.symbol not in self.prices:  # Add the symbol to the dictionary if needed
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]

    def get_balances(self) -> typing.Dict[str, BalanceData]:

        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        balances = dict()

        account_data = self._do_request("GET", "/fapi/v1/account", data)

        if account_data is not None:
            
            for a in account_data['assets']:
                balances[a['asset']] = BalanceData(a)

        return balances

    def place_order(self, contract: ContractData, order_type: str, quantity: float, side: str, price=None, tif=None) -> OrderStatusData:

        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side.upper()
        data['quantity'] = round(int(quantity / contract.lot_size) * contract.lot_size, 8)  # int() to round down
        data['type'] = order_type.upper()  # Makes sure the order type is in uppercase

        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)
            data['price'] = '%.*f' % (contract.price_decimals, data['price'])  # Avoids scientific notation

        if tif is not None:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        
        order_status = self._do_request("POST", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatusData(order_status)

        return order_status

    def cancel_order(self, contract: ContractData, order_id: int) -> OrderStatusData:

        data = dict()
        data['orderId'] = order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        
        order_status = self._do_request("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatusData(order_status)

        return order_status

    def get_order_status(self, contract: ContractData, order_id: int) -> OrderStatusData:

        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._do_request("GET", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatusData(order_status)

        return order_status

    def _start_ws(self):

        self.ws = websocket.WebSocketApp(self._ws_url, on_open=self._on_open, on_close=self._on_close,
                                         on_error=self._on_error, on_message=self._on_message)

        while True:
            try:
                if self.reconnected:  # Reconnect unless the interface is closed by the user
                    self.ws.run_forever()  # Blocking method that ends only if the websocket connection drops
                else:
                    break
            except Exception as e:
                logger.error("Binance error in run_forever() method: %s", e)
            time.sleep(2)

    def _on_open(self, ws):
        
        logger.info("Binance connection opened")

        self.ws_connected = True

        # The aggTrade channel is subscribed to in the _switch_strategy() method of strategy_component.py

        for channel in ["bookTicker", "aggTrade"]:
            for symbol in self.ws_subscriptions[channel]:
                self.subscribe_channel([self.contracts[symbol]], channel, reconnection=True)

        if "XRPUSDT" not in self.ws_subscriptions["bookTicker"]:
            self.subscribe_channel([self.contracts["XRPUSDT"]], "bookTicker")

    def _on_close(self, ws):

        logger.warning("Binance Websocket connection closed")
        self.ws_connected = False

    def _on_error(self, ws, msg: str):

        logger.error("Binance connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        if "e" in data:
            if data['e'] == "bookTicker":

                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])

                # PNL Calculation

                try:
                    for b_index, strat in self.strategies.items():
                        if strat.contract.symbol == symbol:
                            for trade in strat.trades:
                                if trade.status == "open" and trade.entry_price is not None:
                                    if trade.side == "long":
                                        trade.pnl = (self.prices[symbol]['bid'] - trade.entry_price) * trade.quantity
                                    elif trade.side == "short":
                                        trade.pnl = (trade.entry_price - self.prices[symbol]['ask']) * trade.quantity
                except RuntimeError as e:  # Handles the case  the dictionary is modified while loop through it
                    logger.error("Error while looping through the Binance strategies: %s", e)

            if data['e'] == "aggTrade":

                symbol = data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == symbol:
                        res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])  # Updates candlesticks
                        strat.check_trade(res)

    def subscribe_channel(self, contracts: typing.List[ContractData], channel: str, reconnection=False):

        if len(contracts) > 200:
            logger.warning("Subscribing to more than 200 symbols will most likely fail. "
                           "Consider subscribing only when adding a symbol to your Watchlist or when starting a "
                           "strategy for a symbol.")

        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        if len(contracts) == 0:
            data['params'].append(channel)
        else:
            for contract in contracts:
                if contract.symbol not in self.ws_subscriptions[channel] or reconnection:
                    data['params'].append(contract.symbol.lower() + "@" + channel)
                    if contract.symbol not in self.ws_subscriptions[channel]:
                        self.ws_subscriptions[channel].append(contract.symbol)

            if len(data['params']) == 0:
                return

        data['id'] = self._ws_id

        try:
            self.ws.send(json.dumps(data))  # Converts the JSON object (dictionary) to a JSON string
            logger.info("Binance: subscribing to: %s", ','.join(data['params']))
        except Exception as e:
            logger.error("Websocket error while subscribing to @bookTicker and @aggTrade: %s", e)

        self._ws_id += 1

    def get_trade_size(self, contract: ContractData, price: float, balance_pct: float):

        logger.info("Getting Binance trade size...")

        balance = self.get_balances()

        if balance is not None:
            if contract.quote_asset in balance:               
                balance = balance[contract.quote_asset].wallet_balance
            else:
                return None
        else:
            return None

        trade_size = (balance * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)  # Removes extra decimals

        logger.info("Binance current %s balance = %s, trade size = %s", contract.quote_asset, balance, trade_size)

        return trade_size









