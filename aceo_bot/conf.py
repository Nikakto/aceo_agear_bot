from typing import Optional

from pydantic import BaseSettings
from pydantic import Field


__all__ = ["settings"]


class Settings(BaseSettings):
    debug: Optional[bool] = Field(False, alias="DEBUG")
    safe_read: Optional[bool] = Field(True, alias="SAFE_READ")


settings = Settings()
