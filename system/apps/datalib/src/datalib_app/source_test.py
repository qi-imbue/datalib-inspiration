import pytest
from app_instances.errors import (
    InvalidParamsError,
    LocationNotTrackedError,
    NotRenameableError,
    UnknownActionError,
)
from app_instances.primitives import InstanceKey, InstanceTitle, LocationPath
from app_manifest.primitives import ActionId

from datalib_app.source import (
    OPEN_ACTION,
    UI_INSTANCE_KEY,
    DatalibInstanceSource,
    launch_url,
)
from datalib_app.token import ApiToken

_TOKEN = ApiToken("0123456789abcdef")


def test_the_launch_url_carries_the_token_as_datalib_http_reads_it() -> None:
    assert launch_url(_TOKEN) == "/?token=0123456789abcdef"


def test_the_source_lists_exactly_one_explicit_page_at_the_launch_url() -> None:
    source = DatalibInstanceSource(token=_TOKEN)

    [record] = source.list_instances()

    assert record.model_dump(mode="json") == {
        "key": "ui",
        "url": "/?token=0123456789abcdef",
        "title": "Datalib",
        "status": "idle",
        "lifetime": "explicit",
        "last_active": None,
        "renameable": False,
        "stoppable": False,
    }


def test_open_returns_the_same_page_every_time() -> None:
    source = DatalibInstanceSource(token=_TOKEN)

    first = source.create_instance(OPEN_ACTION, {})
    second = source.create_instance(OPEN_ACTION, {})

    assert first == second
    assert first.key == UI_INSTANCE_KEY
    assert source.list_instances() == [first]


def test_open_refuses_params_and_other_actions_are_unknown() -> None:
    source = DatalibInstanceSource(token=_TOKEN)

    with pytest.raises(InvalidParamsError, match="takes no params"):
        source.create_instance(OPEN_ACTION, {"path": "/x"})
    with pytest.raises(UnknownActionError, match="unknown action 'new'"):
        source.create_instance(ActionId("new"), {})


def test_delete_changes_nothing_and_rename_and_location_are_refused() -> None:
    source = DatalibInstanceSource(token=_TOKEN)

    source.delete_instance(UI_INSTANCE_KEY)
    source.delete_instance(InstanceKey("never-existed"))

    assert [record.key for record in source.list_instances()] == ["ui"]
    with pytest.raises(NotRenameableError):
        source.rename_instance(UI_INSTANCE_KEY, InstanceTitle("Mine"))
    with pytest.raises(LocationNotTrackedError):
        source.set_location(UI_INSTANCE_KEY, LocationPath("/manage"))
