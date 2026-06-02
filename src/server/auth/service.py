from __future__ import annotations

from dataclasses import dataclass
import logging
from time import monotonic

import httpx

from src.config.settings import Config


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AuthenticatedUser:
    id: int | str
    username: str
    api_key: str


class Authenticator:
    async def authenticate(self, api_key: str) -> AuthenticatedUser | None:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None


@dataclass(slots=True)
class _CacheEntry:
    user: AuthenticatedUser
    expires_at: float


class RemoteAuthenticator(Authenticator):
    def __init__(
        self,
        endpoint: str,
        http_method: str,
        timeout: float,
        cache_ttl_seconds: int,
    ) -> None:
        self._endpoint = endpoint
        self._http_method = http_method.upper()
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._http = httpx.AsyncClient(timeout=timeout)

    async def authenticate(self, api_key: str) -> AuthenticatedUser | None:
        cached_user = self._get_cached(api_key)
        if cached_user is not None:
            return cached_user

        try:
            response = await self._request_remote_auth(api_key)
        except httpx.HTTPError:
            logger.exception("Remote authentication request failed")
            return None

        if response.status_code == 401:
            self._cache.pop(api_key, None)
            return None

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception(
                "Remote authentication endpoint returned %s",
                response.status_code,
            )
            return None

        try:
            payload = response.json()
            if isinstance(payload, dict) and isinstance(payload.get("user"), dict):
                payload = payload["user"]
            user = AuthenticatedUser(
                id=payload["id"],
                username=payload["username"],
                api_key=api_key,
            )
        except (KeyError, TypeError, ValueError):
            logger.exception("Remote authentication response payload is invalid")
            return None

        self._cache[api_key] = _CacheEntry(
            user=user,
            expires_at=monotonic() + self._cache_ttl_seconds,
        )
        return user

    async def aclose(self) -> None:
        await self._http.aclose()

    def _get_cached(self, api_key: str) -> AuthenticatedUser | None:
        entry = self._cache.get(api_key)
        if entry is None:
            return None
        if entry.expires_at <= monotonic():
            self._cache.pop(api_key, None)
            return None
        return entry.user

    async def _request_remote_auth(self, api_key: str) -> httpx.Response:
        headers = {"X-API-Key": api_key}
        if self._http_method == "POST":
            return await self._http.post(self._endpoint, headers=headers)
        return await self._http.get(self._endpoint, headers=headers)


def build_authenticator(config: Config) -> Authenticator | None:
    if not config.multi_tenant:
        return None
    return RemoteAuthenticator(
        endpoint=config.remote_auth_url,
        http_method=config.remote_auth_http_method,
        timeout=config.remote_auth_timeout_seconds,
        cache_ttl_seconds=config.remote_auth_cache_ttl_seconds,
    )