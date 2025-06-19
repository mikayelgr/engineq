"""
EngineQ: An AI-enabled music management system.
Copyright (C) 2025  Mikayel Grigoryan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For inquiries, contact: michael.grigoryan25@gmail.com
"""

import os

class Config:
    """
    The Config class is a singleton class that holds all the configuration
    variables for the application. All the configuration variables are stored
    as class attributes.

    Note: Dotenv initialization must happen in the main file before the Config
    class is used.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.DEBUG = False
        self.AMQP_URL = os.getenv("AMQP_URL")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        # self.DISCOGS_USER_TOKEN = os.getenv("DISCOGS_USER_TOKEN")
        self.POSTGRES_URL = os.getenv("POSTGRES_URL")
        self.BRAVE_SEARCH_TOKEN = os.getenv("BRAVE_SEARCH_TOKEN")
        self.SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
        self.SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
        self.OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")
        self.OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")

        if os.getenv("DEBUG"):
            self.DEBUG = True

        if self.DEBUG:
            print(self.__dict__)
            print("-" * 50)
