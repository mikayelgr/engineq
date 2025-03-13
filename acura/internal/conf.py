import os


class Config:
    """
    The Config class is a singleton class that holds all the configuration
    variables for the application. All the configuration variables are stored
    as class attributes.

    Note: Dotenv initialization must happen in the main file before the Config
    class is used.
    """
    _instance = None  # The singleton instance of the Config class.
    # Not an env variable. Static configuration for RabbitMQ, which doesn't include any sensitive information.
    MQ_SETTINGS: dict
    AMQP_URL: str
    OLLAMA_URL: str
    OPENAI_API_KEY: str
    DISCOGS_USER_TOKEN: str
    PYTHON_ENV: str
    POSTGRES_URL: str
    BRAVE_SEARCH_TOKEN: str

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.MQ_SETTINGS = {"queue": "curator"}
            self.PYTHON_ENV = os.getenv("PYTHON_ENV")
            if self.PYTHON_ENV is None:
                self.PYTHON_ENV = "development"

            self.AMQP_URL = os.getenv("AMQP_URL")
            self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            self.DISCOGS_USER_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
            self.OLLAMA_URL = os.getenv("OLLAMA_URL")
            self.POSTGRES_URL = os.getenv("POSTGRES_URL")
            self.BRAVE_SEARCH_TOKEN = os.getenv("BRAVE_SEARCH_TOKEN")

            self.initialized = True

            if self.PYTHON_ENV != "production":
                print(self.__dict__)
                print("-" * 50)
