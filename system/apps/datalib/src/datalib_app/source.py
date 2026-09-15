from collections.abc import Mapping
from typing import Final

from app_instances.data_types import InstanceLifetime, InstanceRecord, InstanceStatus
from app_instances.errors import (
    InvalidParamsError,
    LocationNotTrackedError,
    NotRenameableError,
    UnknownActionError,
)
from app_instances.interfaces import InstanceSourceInterface
from app_instances.primitives import (
    InstanceKey,
    InstanceTitle,
    InstanceUrl,
    LocationTarget,
)
from app_manifest.primitives import ActionId
from imbue.imbue_common.pure import pure
from pydantic import Field

from datalib_app.token import ApiToken

# The one action the manifest declares and the one instance it produces.
OPEN_ACTION: Final[ActionId] = ActionId("open")
UI_INSTANCE_KEY: Final[InstanceKey] = InstanceKey("ui")
UI_INSTANCE_TITLE: Final[InstanceTitle] = InstanceTitle("Datalib")

# datalib-http's query key for the token on a launch URL (auth.rs, TOKEN_QUERY_KEY).
TOKEN_QUERY_KEY: Final[str] = "token"


@pure
def launch_url(token: ApiToken) -> InstanceUrl:
    """The page the tab opens: the root of datalib's UI with the token on the query string.

    datalib-http answers a document request that carries the token by setting its session cookie and
    redirecting to the same path without it, so this is the one URL a browser can enter through.
    """
    return InstanceUrl(f"/?{TOKEN_QUERY_KEY}={token}")


class DatalibInstanceSource(InstanceSourceInterface):
    """datalib's UI as the shell sees it: exactly one page, for as long as the program runs.

    The record never changes, so there is nothing to lock: every method reads the frozen token.
    """

    token: ApiToken = Field(
        frozen=True, description="The token datalib-http was started with"
    )

    def list_instances(self) -> list[InstanceRecord]:
        return [self._record()]

    def create_instance(
        self, action: ActionId, params: Mapping[str, str]
    ) -> InstanceRecord:
        # "Open Datalib" always means the one page there is; a second create returns the same
        # record, and the shell focuses the tab that already shows it.
        if action != OPEN_ACTION:
            raise UnknownActionError(f"unknown action {action!r}")
        if params:
            raise InvalidParamsError(
                f"the {OPEN_ACTION!r} action takes no params, got {sorted(params)}"
            )
        return self._record()

    def delete_instance(self, key: InstanceKey) -> None:
        # The page is the program: closing its tab needs no bookkeeping, and stopping datalib is the
        # app-level Stop verb. A delete is accepted and changes nothing.
        return None

    def rename_instance(self, key: InstanceKey, title: InstanceTitle) -> InstanceRecord:
        raise NotRenameableError("the Datalib page cannot be renamed")

    def set_location(self, key: InstanceKey, path: LocationTarget) -> InstanceRecord:
        raise LocationNotTrackedError("the Datalib page does not track its location")

    def _record(self) -> InstanceRecord:
        return InstanceRecord(
            key=UI_INSTANCE_KEY,
            url=launch_url(self.token),
            title=UI_INSTANCE_TITLE,
            status=InstanceStatus.IDLE,
            lifetime=InstanceLifetime.EXPLICIT,
            last_active=None,
            renameable=False,
        )
