from app_instances.errors import AppInstancesError


class DatalibAppError(AppInstancesError):
    """Base error for the Datalib tab's own failures."""


class DatalibBinaryMissingError(DatalibAppError, FileNotFoundError):
    """The pinned datalib-http binary is not installed yet (the env.d unit has not run)."""
