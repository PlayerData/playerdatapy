class RefreshFailedError(Exception):
    """The access token could not be refreshed.

    The server rejected the refresh token (it was revoked, has expired or was
    already used) or answered without a usable token. Log in again.
    """
