class ExchangeError(Exception):
    "Base exception for Exchange errors."
    pass


class AuthenticationError(ExchangeError):
    "Raised when the server is unable to authenticate."
    pass


class EmptyResponse(ExchangeError):
    "Raised when a response is empty or contains no information."
    pass


class InsufficientFunds(ExchangeError):
    "Raised when a transaction cannot be processed due to insufficient funds."
    pass


class InternalServerErrror(ExchangeError):
    "Raised when a 500 status error is returned and/or an invalid parameter is used"
    pass


class InvalidAccount(ExchangeError):
    "Raised when gdax cannot find an account."
    pass


class InvalidAmount(ExchangeError):
    "Raised when the amount of a transaction is not valid."
    pass


class InvalidArgument(ExchangeError):
    "Raised when an invalid argument is passed to a method."
    pass


class InvalidOrder(ExchangeError):
    "Raised when an order id does not exist."
    pass


class InvalidPrice(ExchangeError):
    "Raised when the price of a buy/sell is not valid."
    pass


class InvalidSize(ExchangeError):
    "Raised when the size of a buy/sell is not valid."
    pass


class InvalidSymbol(ExchangeError):
    "Raised when an unsupported symbol is used."
    pass
