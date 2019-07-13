#!/usr/bin/env python
""" Provides an interface to the Coinbase Crypto Exchange Market (CEM).
"""
import logging
import requests
import time

from datetime import datetime
from requests.exceptions import *

from .coinbase.auth import CoinbaseAuth
from .coinbase.constants import CBConst
from .coinbase.exceptions import *
from .coinbase.keys import Keys
from .exchange.base import Exchange
from .exchange.granularity import Granularity
from .logs.setuplogger import logger

event_log = logging.getLogger('root.{}'.format(__name__))


class Coinbase(Exchange):
    """An `Exchange` subclass used for IO ops with Coinbase"""

    def __init__(self, auth: CoinbaseAuth = None, sandbox: bool = False):
        super().__init__()
        """An `Exchange` subclass used for IO ops with Coinbase

        Keyword arguments:
        auth -- required for account operations like buying or selling
        sandbox -- sends all api requests to Coinbase's sandbox if True
        """
        self._event_log = event_log
        self._event_log.info('initializing...')

        if sandbox:
            self.api_url = CBConst.Sandbox.rest_url
        else:
            self.api_url = CBConst.Live.rest_url

        self.__auth = auth
        self.__auth_map = {'auth': self.__auth}

        if not auth:
            self._account_active = False
        else:
            self._account_active = self.__test_auth()

        self.__valid_product_ids = self.__find_valid_product_ids()
        self.__available_granularity = Granularity(
            (60, 300, 900, 3600, 21600, 86400)
        )
        self.__rate_limits = {
            'public': 3, 'public_burst': 6, 'private': 5, 'private_burst': 10
        }
        self.__last_call = time.time()
        self.__call_count = 0
        self.__timeout = 0.5

    def accounts(self, account_id=None):
        """Get a list of trading accounts.

        Keyword arguments:
        account_id -- optional to get information for a specific account

        Returns:
        json style dict

        Return fields:
        id -- Coinbase account ID
        currency -- the primary currency of the account
        balance -- total funds in the account
        holds -- funds on hold (not available for use)
        available -- funds available to withdraw or trade
        margin_enabled -- true if the account belongs to a margin profile
        funded_amount -- amount of margin funding coinbase is providing
        default_amount -- amount of margin in default
        """
        url = self.api_url + '/{}'.format(CBConst.accounts)
        if account_id:
            url += '/{}'.format(account_id)

        try:
            accounts = requests.get(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if accounts.status_code == CBConst.Status.success:
            return accounts.json()

        message = accounts.json()['message']
        if CBConst.Errors.not_found in message:
            raise InvalidAccount(account_id)
        if CBConst.Errors.bad_request in message:
            raise InvalidArgument(account_id)
        raise ExchangeError(message)

    def account_history(self, account_id=None):
        """List account activity.
        Account activity either increases or decreases your account balance.
        Items are paginated and sorted latest first.

        Keyword arguments:
        account_id -- used to get history for a specific account

        Returns:
        json style dict

        Return fields:
        transfer -- Funds moved to/from Coinbase to coinbase
        match -- Funds moved as a result of a trade
        fee -- Fee as a result of a trade
        rebate -- Fee rebate as per our fee schedule

        If an entry is the result of a trade (match, fee), the details
        field will contain additional information about the trade.
        """
        if account_id:
            url = self.api_url + '/{}/{}/{}'.format(
                CBConst.accounts,
                account_id,
                CBConst.ledger
            )

            try:
                history = requests.get(url, auth=self.__auth)
            except HTTPError as e:
                self._event_log.exception(e)
                raise

            if history.status_code == CBConst.Status.success:
                return history.json()
            elif CBConst.Errors.bad_request in history.json()['message']:
                raise InvalidArgument(account_id)
            elif CBConst.Errors.not_found in history.json()['message']:
                raise InvalidAccount(account_id)
            else:
                raise ExchangeError(history.json()['message'])

        accounts = self.accounts()
        account_history = []

        for account in accounts:
            account_id = account['id']
            url = self.api_url + '/{}/{}/{}'.format(
                CBConst.accounts,
                account_id,
                CBConst.ledger
            )

            try:
                history = requests.get(url, auth=self.__auth)
            except HTTPError as e:
                self._event_log.exception(e)
                raise

            if history.status_code == CBConst.Status.success:
                account_history.append(history.json())
            else:
                raise ExchangeError(history.json()['message'])

        return account_history

    def active(self):
        return self.__test_auth()

    def add_auth(self, auth):
        self.__auth = auth
        self.__auth_map = {'auth': self.__auth}

        if self.__test_auth():
            self._account_active = True
        else:
            self._account_active = False
            self.__auth = None
            raise AuthenticationError

    def available_granularity(self):
        return self.__available_granularity

    def balance(self, product_id=None):
        """Returns account balance for all accounts associated with current
        coinbase auth.

        Keyword arguments:
        product_id -- optional string, list, or tuple.
        """
        accounts = self.accounts()
        balances = {}

        for account in accounts:
            if not product_id:
                balances[account['currency']] = account['balance']
            elif account['currency'] in product_id:
                balances[account['currency']] = account['balance']

        return balances

    def buy(self, size, product_id, price):
        """Places an order on the 'buy' side.

        Keyword arguments:
            size -- the volume of the buy order
            product_id -- a valid trade pair
            price -- the price of the buy order

        Preconditions:
            Coinbase account is enabled and authenticated
            Product_id is a valid currency pair symbol
            Price is a float > 0
            Size is a float > 0
            Price * volume <= usd balance

        Postconditions:
            Buy order is placed succesfully
            Receipt is returned as a json dict

        Throws:
            ExchangeError or a subclass of ExchangeError

        Returns:
            A json style dict with receipt details
        """
        url = self.api_url + '/{}'.format(CBConst.orders)
        data = {
            "price": price,
            "size": size,
            "side": CBConst.buy,
            "product_id": product_id,
        }

        try:
            receipt = requests.post(url, json=data, auth=self.__auth)
        except HTTPError as err:
            self._event_log.exception(err)
            raise err

        if receipt.status_code == CBConst.Status.success:
            return receipt.json()

        message = receipt.json()['message']
        if CBConst.Errors.cb_access_key_required in message:
            raise AuthenticationError
        if CBConst.Errors.insufficient_funds in message:
            raise InsufficientFunds
        if CBConst.Errors.internal_server_error in message:
            raise InternalServerErrror
        if CBConst.Errors.invalid_price in message:
            raise InvalidPrice(price)
        if CBConst.Errors.price_required in message:
            raise InvalidPrice(price)
        if CBConst.Errors.price_too_large in message:
            raise InvalidPrice(price)
        if CBConst.Errors.product_not_found in message:
            raise InvalidSymbol(product_id)
        if CBConst.Errors.size_required in message:
            raise InvalidSize(size)
        if CBConst.Errors.size_too_large in message:
            raise InvalidSize(size)
        if CBConst.Errors.size_too_small in message:
            raise InvalidSize(size)
        raise ExchangeError(message)

    def cancel_all_orders(self, product_id=None):
        """Cancels all active orders with option
        to cancel orders of a specific symbol.
        """
        url = self.api_url + '/{}/'.format(CBConst.orders)

        if product_id and product_id in self.__valid_product_ids:
            url += '?product_id={}'.format(product_id)
        elif product_id and product_id not in self.__valid_product_ids:
            raise InvalidSymbol(product_id)

        try:
            receipt = requests.delete(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if receipt.status_code == CBConst.Status.success:
            if receipt.json() == [] and product_id:
                raise EmptyResponse
            return receipt.json()

        raise ExchangeError(receipt.json()['message'])

    def cancel_order(self, order_id):
        """Cancels the order number specified in order_id.

        Preconditions:
            Coinbase account is enabled and authenticated
            order_id refers to an exisiting, live order

        Postconditions:
            The order is canceled
            Receipt is returned as a json dict
        """
        url = self.api_url + '/{}/{}'.format(CBConst.orders, order_id)

        try:
            receipt = requests.delete(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if receipt.status_code == CBConst.Status.success:
            return receipt.json()

        message = receipt.json()['message']
        if CBConst.Errors.invalid_order_id in message:
            raise InvalidOrder(order_id)
        raise ExchangeError(message)

    def candles(self, product_id, start, end, granularity):
        """Candle data for a product.
        This is effectively a wrapper around historic_rates
        It conforms to the `Exchange.candles` protocol required by the `MarketData` module
        """
        try:
            if self.__call_count < self.__rate_limits['public']:
                self.__call_count = self.__call_count + 1
                return self.historic_rates(product_id, start, end, granularity)
            else:
                time.sleep(self.__timeout)
                self.__call_count = 1
                return self.historic_rates(product_id, start, end, granularity)
        except ExchangeError as err:
            raise err



    def deposit(self, amount, currency, payment_method_id):
        url = self.api_url + '/{}/{}'.format(
            CBConst.deposits,
            CBConst.payment_method
        )
        data = {
            CBConst.amount: amount,
            CBConst.currency: currency,
            CBConst.payment_method_id: payment_method_id
        }

        try:
            receipt = requests.post(url, json=data, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if receipt.status_code == CBConst.Status.success:
            return receipt.json()

        message = receipt.json()['message']
        if CBConst.Errors.does_not_match in message:
            raise InvalidArgument(currency, payment_method_id)
        if CBConst.Errors.cannot_deposit_less_than in message:
            raise InvalidAmount(message)
        raise ExchangeError(message)

    def __enforce_rate_limit(self):
        pass

    def __find_valid_product_ids(self):
        products = self.products()
        valid_product_ids = []

        for product in products:
            if product['status'] == 'online':
                valid_product_ids.append(product['id'])
        return tuple(valid_product_ids)

    def historic_rates(
            self, product_id, start=False, end=False, granularity=3600):
        """Historic rates for a product.
        Rates are returned in grouped buckets based on requested granularity.
        Historic rates DO NOT exist for `Sandbox` mode.

        PARAMETERS
        start - Start time in ISO 8601
        end - End time in ISO 8601
        granularity - Desired timeslice in seconds (see below)

        Historical rate data may be incomplete.
        No data is published for intervals where there are no ticks.

        Historical rates should not be polled frequently.
        If you need real-time information,
        use the trade and book endpoints along with the websocket feed.

        If either one of the start or end fields are not provided
        the method will raise an `InvalidArgument` exception.
        If a custom time range is not declared then one ending now is selected.

        The granularity field must be one of the following values:
        {60, 300, 900, 3600, 21600, 86400}.
        Otherwise, your request will be rejected.
        These values correspond to timeslices representing one minute,
        five minutes, fifteen minutes, one hour, six hours,
        and one day, respectively.

        IMPORTANT
        If data points are readily available, your response may contain
        as many as 300 candles and some of those candles may precede
        your declared start value.

        The maximum number of data points for a single request is 350 candles.
        If your selection of start/end time and granularity will result in
        more than 300 data points, your request will be rejected.
        If you wish to retrieve fine granularity data over a larger time range,
        you will need to make multiple requests with new start/end ranges.

        RESPONSE ITEMS
        Each bucket is an array of the following information:
        time: bucket start time
        low: lowest price during the bucket interval
        high: highest price during the bucket interval
        open: opening price (first trade) in the bucket interval
        close: closing price (last trade) in the bucket interval
        volume: volume of trading activity during the bucket interval
        """
        errors = [
            (start and not end),
            (end and not start),
            (product_id not in self.__valid_product_ids),
            (granularity not in self.__available_granularity)
            ]
        if any(errors):
            msg = '{}'.format((product_id, start, end, granularity))
            self._event_log.error(msg)
            raise InvalidArgument(errors)

        if isinstance(start, datetime):
            if not isinstance(end, datetime):
                raise InvalidArgument(
                    'start: {} and end: {} must be same type'.format(
                        type(start), type(end)))
            start = start.isoformat()
            end = end.isoformat()

        url = self.api_url + '/{}/{}/{}'.format(
            CBConst.products, product_id, CBConst.candles)

        params = {'granularity': granularity}
        if start and end:
            params['start'] = start
            params['end'] = end

        try:
            rates = requests.get(url, params=params)
        except HTTPError as err:
            self._event_log.exception(err)
            raise

        if rates.status_code == CBConst.Status.success:
            return rates.json()
        message = rates.json()['message']
        errors = [
            CBConst.Errors.granularity_too_small in message,
            CBConst.Errors.not_found in message,
            CBConst.Errors.unsupported_granularity in message
        ]

        if any(errors):
            raise InvalidArgument(message)

        raise ExchangeError(message)

    def holds(self, account_id=None):
        """Holds are placed on an account for any active orders or
        pending withdraw requests. As an order is filled, the hold
        amount is updated. If an order is canceled, any remaining
        hold is removed. For a withdraw, once it is completed,
        the hold is removed.

        The type of the hold will indicate why the hold exists.
        The hold type is order for holds related to open orders
        and transfer for holds related to a withdraw.

        The ref field contains the id of the order or transfer
        which created the hold.

        By default, this method requires a specific account id,
        however some intelligence is done on our part to find
        holds for all accounts associated with the current auth.

        Include an account_id if you only want holds from a single
        Coinbase account.
        """
        if account_id:
            url = self.api_url + '/{}/{}/{}'.format(
                CBConst.accounts,
                account_id,
                CBConst.holds
            )

            try:
                holds = requests.get(url, auth=self.__auth)
            except HTTPError as e:
                self._event_log.exception(e)
                raise

            if holds.status_code == CBConst.Status.success:
                return holds.json()

            message = holds.json()['message']
            if CBConst.Errors.cb_access_key_required in message:
                raise AuthenticationError(self.__auth)
            elif CBConst.Errors.bad_request in message:
                raise InvalidArgument(account_id)
            elif CBConst.Errors.not_found in message:
                raise InvalidAccount(account_id)
            raise ExchangeError(message)

        accounts = self.accounts()
        account_holds = []

        for account in accounts:
            account_id = account['id']
            url = self.api_url + '/{}/{}/{}'.format(
                CBConst.accounts,
                account_id,
                CBConst.holds
            )

            try:
                holds = requests.get(url, auth=self.__auth)
            except HTTPError as e:
                self._event_log.exception(e)
                raise

            if holds.status_code == CBConst.Status.success:
                account_holds.append(holds.json())
            else:
                raise ExchangeError(holds.json()['message'])

        return account_holds

    def order_book(self, product_id, level=None):
        """Returns a list of all active orders on the Coinbase order books
        for a given product_id.

        An optional level may be specified:
            1 - Only the best bid and ask (default)
            2 - Top 50 bids and asks (aggregated)
            3 - Full order book (non aggregated)
        """
        url = self.api_url + '/{}/{}/{}'.format(
            CBConst.products,
            product_id,
            CBConst.book
        )

        if level:
            url += '?level={}'.format(level)

        try:
            book = requests.get(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if book.status_code == CBConst.Status.success:
            return book.json()

        message = book.json()['message']
        if CBConst.Errors.not_found in message:
            raise InvalidArgument(product_id)
        if CBConst.Errors.invalid_level in message:
            raise InvalidArgument(level)
        raise ExchangeError(message)

    def orders(self, status=None, product_id=None):
        """Returns a list of all active, done, open, or pending orders.

        Preconditions:
            Coinbase account is enabled and authenticated

        Postconditions:
            A list of json dicts is returned with all active orders
        """
        url = self.api_url + '/{}'.format(CBConst.orders)
        query_parameters = ''

        if status:
            if isinstance(status, (list, tuple)):
                query_parameters += '?'
                for s in status:
                    query_parameters += 'status={}&'.format(s)
                query_parameters = query_parameters[:-1]  # remove extra &
            elif isinstance(status, str):
                query_parameters += '?status={}'.format(status)
            else:
                raise InvalidArgument(status)

        if product_id:
            if '?' in query_parameters:
                query_parameters += '&product_id={}'.format(product_id)
            else:
                query_parameters += '?product_id={}'.format(product_id)

        url += query_parameters
        try:
            orders = requests.get(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if orders.status_code == CBConst.Status.success:
            return orders.json()

        message = orders.json()['message']
        if CBConst.Errors.cb_access_key_required in message:
            raise AuthenticationError(self.__auth)
        if CBConst.Errors.not_a_valid_status in message:
            raise InvalidArgument(status)
        if CBConst.Errors.not_a_valid_product_id in message:
            raise InvalidArgument(product_id)
        raise ExchangeError(message)

    def payment_methods(self):
        url = self.api_url + '/{}'.format(CBConst.payment_methods)

        try:
            methods = requests.get(url, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if methods.status_code == CBConst.Status.success:
            return methods.json()

        message = methods.json()['message']
        if CBConst.Errors.cb_access_key_required in message:
            raise AuthenticationError(self.__auth)
        raise ExchangeError(message)

    def products(self):
        """Get a list of available currency pairs for trading.
        """
        url = self.api_url + '/{}'.format(CBConst.products)

        try:
            products = requests.get(url)
        except HTTPError as e:
            self._event_log.exception(e)

        if products.status_code == CBConst.Status.success:
            return products.json()
        raise ExchangeError(products.json()['message'])

    def remove_auth(self):
        self.__auth = auth
        self.__auth_map = {'auth': self.__auth}
        self._account_active = False

    @staticmethod
    def server_time():
        """ Static method used to retrieve the Coinbase server time.
        """
        url = CBConst.Live.rest_url + '/{}'.format(CBConst.time)
        coinbase_time = requests.get(url)

        if coinbase_time.status_code == CBConst.Status.success:
            return coinbase_time.json()
        else:
            raise ExchangeError((coinbase_time.json()['message']))

    def sell(self, size, product_id, price):
        """Places an order on the 'sell' side.

        Preconditions:
            coinbase account is enabled and authenticated
            price is a float > 0
            size is a float > 0
            size <= crypto balance

        Postconditions:
            Sell order is placed succesfully
            Receipt is returned as a json dict
        """
        url = self.api_url + '/{}'.format(CBConst.orders)
        data = {
            "price": price,
            "size": size,
            "side": CBConst.sell,
            "product_id": product_id,
        }

        try:
            receipt = requests.post(url, json=data, auth=self.__auth)
        except HTTPError as err:
            self._event_log.exception(err)
            raise

        if receipt.status_code == CBConst.Status.success:
            return receipt.json()

        message = receipt.json()['message']
        if CBConst.Errors.cb_access_key_required in message:
            raise AuthenticationError
        if CBConst.Errors.insufficient_funds in message:
            raise InsufficientFunds
        if CBConst.Errors.internal_server_error in message:
            raise InternalServerErrror
        if CBConst.Errors.invalid_price in message:
            raise InvalidPrice(price)
        if CBConst.Errors.price_required in message:
            raise InvalidPrice(price)
        if CBConst.Errors.price_too_large in message:
            raise InvalidPrice(price)
        if CBConst.Errors.product_not_found in message:
            raise InvalidSymbol(product_id)
        if CBConst.Errors.size_required in message:
            raise InvalidSize(size)
        if CBConst.Errors.size_too_large in message:
            raise InvalidSize(size)
        if CBConst.Errors.size_too_small in message:
            raise InvalidSize(size)
        raise ExchangeError(message)

    def __test_auth(self):
        """Checks coinbase account status using the provided credentials.
        """
        self._account_active = False
        url = self.api_url + '/{}'.format(CBConst.coinbase_accounts)

        try:
            receipt = requests.get(url, **self.__auth_map).json()
        except HTTPError as e:
            self._account_active = False
            self._event_log.exception(e)
            raise
        except Exception as e:
            self._account_active = False
            self._event_log.exception(e)
            raise

        try:
            for i in range(0, len(receipt)):
                if receipt[i]['active']:
                    self._account_active = True
        except KeyError:
            self._account_active = False

        return self._account_active

    def ticker(self, symbol):
        url = self.api_url + '/{}/{}/{}'.format(
            CBConst.products,
            symbol,
            CBConst.ticker
        )

        try:
            ticker = requests.get(url)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if ticker.status_code == CBConst.Status.success:
            return ticker.json()
        else:
            raise ExchangeError(ticker.json()['message'])

    def trades(self, product_id):
        url = self.api_url + '/{}/{}/{}'.format(
            CBConst.products,
            product_id,
            CBConst.trades
        )

        try:
            trades = requests.get(url)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if trades.status_code == CBConst.Status.success:
            return trades.json()

        message = trades.json()['message']
        raise ExchangeError(message)


    def withdraw(self, amount, currency, payment_method_id):
        """Withdraw funds to a payment method.
        """
        url = self.api_url + '/{}/{}'.format(
            CBConst.withdrawals,
            CBConst.payment_method
        )
        data = {
            CBConst.amount: amount,
            CBConst.currency: currency,
            CBConst.payment_method_id: payment_method_id
        }

        try:
            receipt = requests.post(url, json=data, auth=self.__auth)
        except HTTPError as e:
            self._event_log.exception(e)
            raise

        if receipt.status_code == CBConst.Status.success:
            return receipt.json()

        message = receipt.json()['message']
        if CBConst.Errors.amount_is_required in message:
            raise InvalidArgument(message)
        if CBConst.Errors.amount_must_be_positive in message:
            raise InvalidArgument(message)
        if CBConst.Errors.does_not_exist in message:
            raise InvalidArgument(message)
        if CBConst.Errors.does_not_match in message:
            raise InvalidArgument(message)
        if CBConst.Errors.invalid_api_key in message:
            raise InvalidAccount(message)
        if CBConst.Errors.insufficient_funds in message:
            raise InsufficientFunds(message)
        if CBConst.Errors.unsupported_currency in message:
            raise InvalidArgument(message)
        raise ExchangeError(message)

    def valid_product_ids(self):
        return self.__valid_product_ids

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


if __name__ == '__main__':
    # Setup the logging environment.
    log_fmt = '%(asctime)s %(levelname)s %(name)s.%(funcName)s() %(message)s'
    # Have to move this ugly mess in to a wrapper some day.
    logging.basicConfig(
        datefmt='%m/%d/%y %H:%M:%S',
        format=log_fmt,
        filename='events.log',
        level=logging.DEBUG
    )

    keys = Keys('COINBASE_SANDBOX')
    auth = CoinbaseAuth(
        api_key=keys.api_key,
        secret_key=keys.secret_key,
        passphrase=keys.passphrase
    )

    exchange = Coinbase()
    print(exchange.valid_product_ids())
