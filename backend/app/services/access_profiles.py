"""Access profiles of the users, managed from the administration page.

A profile is an OpenShift group (AUTH_PROFILES); what the profile may use is OpenShift RBAC
(helm/multi-agents/templates/auth/profiles-rbac.yaml). Giving a profile to a user = adding the user
to the group, so the same rule applies to the UI, the agents and the MCP Gateway.

The backend's ServiceAccount may only read the users and update the profile groups
(ClusterRole <namespace>-profile-manager, restricted to these groups by name). The change applies
within seconds: the backend drops its cached rights of the user, the OpenShift token cache
expires after a few seconds.
"""
import logging
import re
from typing import Dict, List, Optional, Set

import httpx

from app.core.auth import User, forget_user, kubernetes, load_profiles

logger = logging.getLogger(__name__)

GROUPS_API = "/apis/user.openshift.io/v1/groups"
USERS_API = "/apis/user.openshift.io/v1/users"
USERNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@+-]{0,252}$")  # OpenShift user names (no "system:")


class ProfileError(Exception):
    """Invalid request (HTTP 400)."""


async def _get(path: str) -> Optional[Dict]:
    resp = await kubernetes.http().get(path)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def _groups(profiles: Dict[str, Dict]) -> Dict[str, Optional[Dict]]:
    return {pid: await _get(f"{GROUPS_API}/{p['group']}") for pid, p in profiles.items()}


def _profile_list(profiles: Dict[str, Dict], groups: Dict[str, Optional[Dict]]) -> List[Dict]:
    return [{"id": pid, "displayName": p.get("displayName", pid), "group": p["group"],
             "agents": p.get("agents", []), "admin": bool(p.get("admin")), "exists": groups[pid] is not None}
            for pid, p in profiles.items()]


def _user_row(username: str, full_name: Optional[str], groups: Dict[str, Optional[Dict]]) -> Dict:
    return {"username": username, "fullName": full_name,
            "profiles": [pid for pid, g in groups.items() if g and username in (g.get("users") or [])]}


async def list_users() -> Dict:
    """Profiles, and every user: the OpenShift users (logged in at least once) and the members of
    the profile groups (a user may be given a profile before the first login)."""
    profiles = load_profiles()
    groups = await _groups(profiles)
    users = {u["metadata"]["name"]: u.get("fullName") for u in ((await _get(USERS_API)) or {}).get("items", [])}
    members = {name for g in groups.values() if g for name in (g.get("users") or [])}
    return {"profiles": _profile_list(profiles, groups),
            "users": [_user_row(name, users.get(name), groups) for name in sorted(set(users) | members)]}


async def _update_group(name: str, username: str, member: bool) -> bool:
    """Add or remove a member; retried once on a concurrent change (409). True if changed."""
    for attempt in (1, 2):
        group = await _get(f"{GROUPS_API}/{name}")
        if group is None:
            raise ProfileError(f"OpenShift group {name} does not exist")
        users: List[str] = list(group.get("users") or [])
        if (username in users) == member:
            return False
        group["users"] = users + [username] if member else [u for u in users if u != username]
        resp = await kubernetes.http().put(f"{GROUPS_API}/{name}", json=group)
        if resp.status_code == 409 and attempt == 1:
            continue
        resp.raise_for_status()
        return True
    return False


async def set_profiles(username: str, wanted: Set[str], actor: User) -> Dict:
    """Give the user exactly these profiles."""
    profiles = load_profiles()
    if not USERNAME.match(username):
        raise ProfileError(f"Invalid user name: {username}")
    unknown = wanted - set(profiles)
    if unknown:
        raise ProfileError(f"Unknown profiles: {', '.join(sorted(unknown))}")
    if username == actor.username and not any(profiles[p].get("admin") for p in wanted):
        raise ProfileError("You cannot remove your own administrator profile")

    changed = [pid for pid, p in profiles.items() if await _update_group(p["group"], username, pid in wanted)]
    forget_user(username)
    if changed:
        logger.info("Profiles of %s set to %s by %s (changed: %s)", username, sorted(wanted), actor.username, changed)
    groups = await _groups(profiles)
    users = await _get(f"{USERS_API}/{username}")
    return _user_row(username, (users or {}).get("fullName"), groups)


def api_error(e: httpx.HTTPStatusError) -> str:
    """Readable message of an OpenShift API error."""
    try:
        return e.response.json().get("message") or str(e)
    except ValueError:
        return str(e)
