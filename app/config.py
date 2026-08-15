from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    discord_token: str
    application_id: int
    database_url: str
    timezone: str
    log_level: str
    dev_guild_id: Optional[int]

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise ValueError("DISCORD_TOKEN is required")
        app_id = int(os.getenv("DISCORD_APPLICATION_ID", "0"))
        return cls(
            discord_token=token,
            application_id=app_id,
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/briar.db"),
            timezone=os.getenv("TZ", "Asia/Seoul"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            dev_guild_id=int(os.environ["DISCORD_DEV_GUILD_ID"])
            if os.getenv("DISCORD_DEV_GUILD_ID")
            else None,
        )

    def ensure_data_directory(self) -> None:
        if self.database_url.startswith("sqlite:///"):
            path = self.database_url.removeprefix("sqlite:///")
            if path.startswith("/"):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            else:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
