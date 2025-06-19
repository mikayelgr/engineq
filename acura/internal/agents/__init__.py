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

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from internal.conf import Config


def decide_llm():
    """Decides which LLM to use based on the configuration."""

    return OpenAIModel(
        "gpt-4o-mini" if not Config().OLLAMA_MODEL_NAME else Config().OLLAMA_MODEL_NAME,
        provider=OpenAIProvider(base_url=Config().OLLAMA_API_URL if Config().OLLAMA_API_URL else None),
    )
