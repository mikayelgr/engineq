import os


class Config:
    """
    The Config class is a singleton class that holds all the configuration
    variables for the application. All the configuration variables are stored
    as class attributes.

    Note: Dotenv initialization must happen in the main file before the Config
    class is used.
    """
    # Not an env variable. Static configuration for RabbitMQ, which doesn't include any sensitive information.
    DEBUG: bool
    AMQP_URL: str
    POSTGRES_URL: str
    OPENAI_API_KEY: str
    DISCOGS_USER_TOKEN: str
    BRAVE_SEARCH_TOKEN: str
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    LOGFIRE_TOKEN: str

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.DEBUG = False
            self.AMQP_URL = os.getenv("AMQP_URL")
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            self.DISCOGS_USER_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
            self.POSTGRES_URL = os.getenv("POSTGRES_URL")
            self.BRAVE_SEARCH_TOKEN = os.getenv("BRAVE_SEARCH_TOKEN")
            self.SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
            self.SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
            self.LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

            if os.getenv("DEBUG"):
                self.DEBUG = True

            if self.DEBUG:
                print(self.__dict__)
                print("-" * 50)
