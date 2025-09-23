from redis.asyncio.connection import Connection, RedisSSLContext
import ssl

class CustomSSLConnection(Connection):
    def __init__(self, ssl_context=None, **kwargs):
        super().__init__(**kwargs)
        self.ssl_context = RedisSSLContext(ssl_context)

    def get_ssl_context(self):
        return self.ssl_context.get()

def get_custom_ssl_context():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # or ssl.CERT_REQUIRED based on your Redis cert config
    return ssl_context
