from pathlib import Path

import pytest

from datalib_app.errors import DatalibAppError
from datalib_app.token import (
    ApiToken,
    mint_token,
    read_or_mint_token,
    token_file_path,
)


def test_the_token_file_is_where_datalib_http_publishes_it() -> None:
    assert token_file_path(Path("data/.skills/datalib")) == Path(
        "data/.skills/datalib/system/api-token"
    )


def test_a_minted_token_is_64_hex_characters_and_unique() -> None:
    first = mint_token()
    second = mint_token()

    assert len(first) == 64
    assert int(first, 16) >= 0
    assert first != second


@pytest.mark.parametrize("value", ["", "has space", "semi;colon", "slash/"])
def test_a_token_datalib_http_would_refuse_is_refused_here(value: str) -> None:
    with pytest.raises(DatalibAppError, match="invalid datalib API token"):
        ApiToken(value)


def test_the_published_token_is_reused(tmp_path: Path) -> None:
    published = tmp_path / "system" / "api-token"
    published.parent.mkdir()
    published.write_text("abc-DEF_123.~\n")

    assert read_or_mint_token(tmp_path) == "abc-DEF_123.~"


def test_a_missing_token_file_mints_one(tmp_path: Path) -> None:
    token = read_or_mint_token(tmp_path)

    assert len(token) == 64
    assert not (tmp_path / "system" / "api-token").exists()


def test_an_unusable_token_file_is_replaced_by_a_minted_one(tmp_path: Path) -> None:
    published = tmp_path / "system" / "api-token"
    published.parent.mkdir()
    published.write_text("not a token\n")

    token = read_or_mint_token(tmp_path)

    assert len(token) == 64
    assert token != "not a token"
