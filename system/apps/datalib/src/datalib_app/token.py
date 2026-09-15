import re
import secrets
from pathlib import Path
from typing import Any, Final, Self

from imbue.imbue_common.pure import pure
from loguru import logger
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from datalib_app.errors import DatalibAppError

# datalib-http's own rule for a token handed in through DATALIB_TOKEN (auth.rs, is_url_safe):
# the unreserved URL characters, so it can ride a query string unencoded.
TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9._~-]+$")

# The shape datalib-http mints itself: 64 hex characters (two UUIDs' worth of randomness).
MINTED_TOKEN_BYTES: Final[int] = 32

# Where datalib-http publishes the token it runs with, relative to the data root; the datalib
# skill reads the same file for its bearer token.
TOKEN_FILE_RELATIVE_PATH: Final[Path] = Path("system") / "api-token"


class ApiToken(str):
    """The bearer token datalib-http requires on every request, in the form it accepts from DATALIB_TOKEN."""

    def __new__(cls, value: str) -> Self:
        if not TOKEN_PATTERN.fullmatch(value):
            raise DatalibAppError(
                "invalid datalib API token: expected one or more of A-Z a-z 0-9 - . _ ~"
            )
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema()
        )


@pure
def token_file_path(data_root: Path) -> Path:
    """Where datalib-http writes the token for a store at ``data_root``."""
    return data_root / TOKEN_FILE_RELATIVE_PATH


def mint_token() -> ApiToken:
    """A fresh random token, in the shape datalib-http mints for itself."""
    return ApiToken(secrets.token_hex(MINTED_TOKEN_BYTES))


def read_or_mint_token(data_root: Path) -> ApiToken:
    """The token the last datalib-http on ``data_root`` ran with, or a fresh one when there is none usable.

    Reusing the published token keeps it stable across restarts of the program, so a browser that
    already holds datalib's session cookie stays signed in and the skill's copy stays valid. datalib-http
    rewrites the file with whatever it is started with, so a token this cannot reuse is simply replaced.
    """
    path = token_file_path(data_root)
    if not path.is_file():
        return mint_token()
    published = path.read_text(encoding="utf-8", errors="replace").strip()
    if not TOKEN_PATTERN.fullmatch(published):
        logger.warning(
            "The token file {} does not hold a usable token; minting a new one", path
        )
        return mint_token()
    return ApiToken(published)
