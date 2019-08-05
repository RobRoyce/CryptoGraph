class Keys():
    """
    Insert your API keys and passphrase.
    """
    def __init__(self, name):
        if name is 'COINBASE':
            self.api_key = ''
            self.secret_key = ''
            self.passphrase = ''
        elif name is 'COINBASE_SANDBOX':
            self.api_key = ''
            self.secret_key = ''
            self.passphrase = ''
        else:
            raise Exception(
                'unable to locate {} in the list of Keys'.format(name))

        errors = [(not self.api_key), (not self.secret_key),
                  (not self.passphrase)]
        if any(errors):
            msg = 'API auth key sequence undetected or invalid'
            raise NotImplementedError(msg)
