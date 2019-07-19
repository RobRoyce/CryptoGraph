import logging
import hashlib
import requests
import base64
import hmac
from requests.exceptions import HTTPError
from requests.auth import AuthBase
from .constants import CBConst


class CoinbaseAuth(AuthBase):
    """ Authenticator used for Coinbase API calls that require credentials.

        Each Coinbase object may be initialized with a
        CoinbaseAuth, or one can be added later by calling
        add_auth() from your Coinbase object

        Using the requests module, any POST method should be
        called using the 'auth' parmeter.
        Example:
            receipt = requests.post(url, json=data, auth=self.__auth)

        It is also sometimes necessary to call a GET or DELETE
        method and include an auth mapping in **kwargs
        Example:
            auth = {'auth': self.auth}
            receipt = requests.delete(url, **auth)

        Each time a CoinbaseAuth object is called, it takes the
        base request and updates the various headers including:
            CB-ACCESS-SIGN,
            CB-ACCESS-TIMESTAMP,
            CB-ACCESS-KEY,
            CB-ACCESS-PASSPHRASE

        These headers are then used as arguments in
        the various REST methods.
    """

    def __init__(self, api_key: str, secret_key: str, passphrase: str):
        self.__log = logging.getLogger('root.{}'.format(__name__))
        self.__log.debug('encrypting message...')

        errors = [
            (not isinstance(api_key, str)),
            (not isinstance(secret_key, str)),
            (not isinstance(passphrase, str))]

        if any(errors):
            msg = 'arguments must be str type'
            self.__log.exception(msg)
            raise Exception(msg)

        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__passphrase = passphrase

    def __call__(self, request):
        try:
            timestamp = str(self.__server_time())
        except Exception as err:
            self.__log('unable to get system time - {}'.format(err))
            raise err

        method = request.method
        path_url = request.path_url
        body = '' if request.body is None else request.body.decode('utf-8')

        message = '{}{}{}{}'.format(
            timestamp,
            method,
            path_url,
            body
        ).encode()

        hmac_key = base64.b64decode(self.__secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            CBConst.cb_access_sign: signature_b64,
            CBConst.cb_access_timestamp: timestamp,
            CBConst.cb_access_key: self.__api_key,
            CBConst.cb_access_passphrase: self.__passphrase,
            CBConst.content_type: CBConst.application_json
        })

        return request

    def __server_time(self):
        url = CBConst.Live.rest_url + '/{}'.format(CBConst.time)

        try:
            time = requests.get(url)
        except Exception as err:
            msg = 'unable to get system time - {}'.format(err)
            self.__log.exception(msg)
            raise err

        if time.status_code == 200:
            return time.json()['epoch']
        else:
            raise requests.exceptions.HTTPError
