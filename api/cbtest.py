import logging
import unittest

from coinbase.auth import CoinbaseAuth
from coinbase.exceptions import *
from coinbase.keys import Keys
from cbexchange import Coinbase
from logs.setuplogger import logger
event_log = logging.getLogger('root.{}'.format(__name__))

class CoinbaseTestCase(unittest.TestCase):
    def setUp(self):
        keys = Keys('COINBASE_SANDBOX')
        self.symbol = 'BTC-USD'
        self.auth = CoinbaseAuth(
            keys.api_key, keys.secret_key, keys.passphrase)

    def tearDown(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        exchange.cancel_all_orders()

    def test_auth(self):
        errors = False
        exchange = Coinbase(auth=self.auth, sandbox=True)
        try:
            success = exchange.active()
        except ExchangeError as err:
            errors = True
        self.assertTrue(success)
        self.assertFalse(errors)

        exchange = Coinbase(auth=None, sandbox=True)
        try:
            success = exchange.active()
        except ExchangeError:
            errors = True
        self.assertFalse(success)
        self.assertFalse(errors)

        exchange = Coinbase(auth=None, sandbox=False)
        try:
            success = exchange.add_auth(self.auth)
            # Note that sandbox is set to False but
            # self.auth is a sandbox auth
        except AuthenticationError:
            errors = True
        self.assertFalse(success)
        self.assertTrue(errors)

    def test_buy(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        try:
            receipt = exchange.buy(1, 'BTC-USD', 1)
        except ExchangeError:
            errors = True
        self.assertFalse(errors)
        self.assertTrue(receipt is not None)
        self.assertTrue('id' in receipt)
        self.assertTrue('price' in receipt)
        self.assertTrue('size' in receipt)
        self.assertTrue(receipt['side'] == 'buy')

    def test_buy_auth(self):
        receipt = None
        errors = False
        exchange = Coinbase(sandbox=True)
        try:
            receipt = exchange.buy(1, 'BTC-USD', 1)
        except AuthenticationError:
            errors = True
        self.assertTrue(errors)
        self.assertTrue(receipt is None)

    def test_buy_insufficient_funds(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        try:
            receipt = exchange.buy(1, 'BTC-USD', 10000000000)
        except InsufficientFunds:
            errors = True
        self.assertTrue(errors)
        self.assertTrue(receipt is None)

    def test_buy_price(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None

        errors = False
        price = 0
        try:
            receipt = exchange.buy(1, 'BTC-USD', price)
        except InvalidPrice:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

        errors = False
        price = -1
        try:
            receipt = exchange.buy(1, 'BTC-USD', price)
        except InvalidPrice:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

        errors = False
        price = 1000000000000
        try:
            receipt = exchange.buy(1, 'BTC-USD', price)
        except InternalServerErrror:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

    def test_buy_size(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        size = 0
        try:
            receipt = exchange.buy(size, 'BTC-USD', 1)
        except InvalidSize:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

        errors = False
        size = 1000000000
        try:
            receipt = exchange.buy(size, 'BTC-USD', 1)
        except InvalidSize:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

    def test_buy_symbol(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        try:
            receipt = exchange.buy(1, 'BTC', 1)
        except InvalidSymbol:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

    def test_cancel(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        buy = exchange.buy(1, self.symbol, 1)
        cancel = exchange.cancel_order(buy['id'])
        self.assertTrue(buy['id'] in cancel)

        error = False
        try:
            cancel = exchange.cancel_order('invalid')
        except InvalidOrder:
            error = True
        self.assertTrue(error)

    def test_cancel_all(self):
        pass

    def test_historic_rates(self):
        error = False
        exchange = Coinbase()

        try:  # correctly-spelled product
            rates = exchange.historic_rates('ETH-USD')
        except ExchangeError:
            pass
        self.assertTrue(rates)

        try:  # incorrectly-spelled product
            rates = exchange.historic_rates('ETH-UtSD')
        except InvalidArgument:
            error = True
        self.assertTrue(error)
        error = False

        try:  # granularity too small
            rates = exchange.historic_rates(
                'ETH-USD', start='2019-01-01', end='2019-06-01')
        except InvalidArgument:
            error = True
        self.assertTrue(error)
        error = False

        try:  # missing end date
            rates = exchange.historic_rates('ETH-USD', start='2019-01-01')
        except InvalidArgument:
            error = True
        self.assertTrue(error)
        error = False

        try:  # missing start date
            rates = exchange.historic_rates('ETH-USD', end='2019-01-01')
        except InvalidArgument:
            error = True
        self.assertTrue(error)
        error = False

    def test_ticker(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        ticker = None
        try:
            ticker = exchange.ticker('BTC-USD')
        except ExchangeError:
            pass
        self.assertTrue(ticker is not None)
        self.assertTrue('time' in ticker)

    def test_sell(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        try:
            receipt = exchange.sell(1, 'BTC-USD', 1)
        except ExchangeError:
            errors = True
        self.assertFalse(errors)
        self.assertTrue(receipt is not None)
        self.assertTrue('id' in receipt)
        self.assertTrue('price' in receipt)
        self.assertTrue('size' in receipt)
        self.assertTrue(receipt['side'] == 'sell')

    def test_sell_auth(self):
        receipt = None
        errors = False
        exchange = Coinbase(sandbox=True)
        try:
            receipt = exchange.sell(1, 'BTC-USD', 1)
        except AuthenticationError:
            errors = True
        self.assertTrue(errors)
        self.assertTrue(receipt is None)

    def test_sell_price(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        price = 0
        try:
            receipt = exchange.sell(1, 'BTC-USD', price)
        except InvalidPrice:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

        errors = False
        price = 10000000000000000000
        try:
            receipt = exchange.sell(1, 'BTC-USD', price)
        except InternalServerErrror:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

    def test_sell_size(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        size = 0
        try:
            receipt = exchange.sell(size, 'BTC-USD', 1)
        except InvalidSize:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

        errors = False
        size = 1000000000
        try:
            receipt = exchange.sell(size, 'BTC-USD', 1)
        except InvalidSize:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)

    def test_sell_symbol(self):
        exchange = Coinbase(auth=self.auth, sandbox=True)
        receipt = None
        errors = False
        try:
            receipt = exchange.sell(1, 'BTC', 1)
        except InvalidSymbol:
            errors = True
        self.assertTrue(receipt is None)
        self.assertTrue(errors)


if __name__ == '__main__':
    unittest.main()
