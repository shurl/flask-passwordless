import hashlib
import uuid
from .token_store import TOKEN_STORES
from .login_url import LOGIN_URLS
from .delivery_methods import DELIVERY_METHODS


class Passwordless(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
        self.single_use = False

    def init_app(self, app):
        config = app.config['PASSWORDLESS']
        token_store = config['TOKEN_STORE']
        self.token_store = TOKEN_STORES[token_store](config)
        # does the token expire after a single login session? ie is it bookmarkable
        self.single_use = config.get('SINGLE_USE', True)

        delivery_method = config['DELIVERY_METHOD']
        self.delivery_method = DELIVERY_METHODS[delivery_method](app.config)

        login_url = config['LOGIN_URL']
        self.login_url = LOGIN_URLS[login_url](app.config)

    def request_token(self, user):
        token = uuid.uuid4().hex
        uid = hashlib.sha224(user).hexdigest()
        if self.token_store.get_by_userid(uid) is None:
            self.token_store.store_or_update(token, uid)
            self.delivery_method(
                self.login_url.generate(token, uid),
                email=user
            )

    def authenticate(self, flask_request):
        token, uid = self.login_url.parse(flask_request)
        is_authenticated = self.token_store.get_by_userid(uid) == token
        if is_authenticated and self.single_use:
            self.token_store.invalidate_token(uid)

        return is_authenticated
