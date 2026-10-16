"""The MaaS API key of each user: the agents call the models as the user (models.maas.callAsUser).

The cluster MaaS counts and limits every model call on one subscription. A user's OpenShift token
matches the subscriptions of all their groups, and the MaaS refuses a call it cannot attribute (it
would need the X-MaaS-Subscription header, which OGX cannot send). An API key is bound to one
subscription: the backend mints one per user, with the user's own token, on the subscription of
their access profile (<prefix>-<profile> for a profile with a tokenQuota, the highest priority when
several; else <prefix>-users), and the agents give it to OGX for the user's requests (A2A metadata
"model_key"). The MaaS then applies the profile's quota and shows the usage of each person.

Without MAAS_API_URL (no authentication, or no cluster MaaS) the platform key is used. Keys stay in
memory (one backend replica) and are minted again before they expire; when minting fails, the
platform key is used and a warning is logged.
"""
import logging
import time
from typing import Dict, Optional, Tuple

import httpx

from app.core.auth import User, current_token, load_profiles, request_user
from app.core.config import settings

logger = logging.getLogger(__name__)

KEY_LIFETIME = "1d"            # expiresIn of the minted keys
KEY_REUSE_SECONDS = 20 * 3600  # minted again after 20 hours
_keys: Dict[Tuple[str, str], Tuple[float, str]] = {}   # (user, subscription) -> (minted at, key)


def subscription_of(user: User) -> str:
    """The MaaS subscription of the user's model calls."""
    profiles = load_profiles()
    quotas = [(profiles[pid]["tokenQuota"].get("priority", 0), pid)
              for pid in user.profiles if (profiles.get(pid) or {}).get("tokenQuota")]
    return f"{settings.maas_subscription_prefix}-{max(quotas)[1] if quotas else 'users'}"


async def agent_credentials() -> Dict[str, str]:
    """A2A metadata of an agent call for the user of the current request: the OpenShift token for
    the MCP Gateway, and the MaaS key for the models when they are called as the user."""
    token, user = current_token(), request_user()
    if not token:
        return {}
    credentials = {"user_token": token}
    if settings.maas_api_url and user:
        key = await user_key(user, token)
        if key:
            credentials["model_key"] = key
    return credentials


async def user_key(user: User, token: str) -> Optional[str]:
    subscription = subscription_of(user)
    minted = _keys.get((user.username, subscription))
    if minted and time.time() - minted[0] < KEY_REUSE_SECONDS:
        return minted[1]
    try:
        key = await _mint(token, subscription)
    except Exception as e:
        logger.warning("No MaaS key for %s on %s (%s): the platform key is used", user.username, subscription, e)
        return None
    _keys[(user.username, subscription)] = (time.time(), key)
    logger.info("MaaS key minted for %s on subscription %s", user.username, subscription)
    return key


async def _mint(token: str, subscription: str) -> str:
    """A key of the user (their token), bound to the subscription: POST /maas-api/v1/api-keys."""
    async with httpx.AsyncClient(timeout=20, verify=settings.maas_tls_verify) as client:
        resp = await client.post(f"{settings.maas_api_url.rstrip('/')}/api-keys",
                                 headers={"Authorization": f"Bearer {token}"},
                                 json={"name": f"multi-agents-{time.strftime('%Y%m%d-%H%M%S')}",
                                       "expiresIn": KEY_LIFETIME, "subscription": subscription})
        resp.raise_for_status()
        return resp.json()["key"]
