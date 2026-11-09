"""The entry for Nextcloud in the app overview and the apps menus of the Frappe apps (COMPASS REQ-039, REQ-045)."""

NEXTCLOUD_ROLE = "Nextcloud Nutzer"


def has_nextcloud_access() -> bool:
	"""Hook `has_permission` of the entry: only a user with the Frappe role that follows the Keycloak role sees Nextcloud."""
	import frappe

	return NEXTCLOUD_ROLE in frappe.get_roles()


def nextcloud_entry(url: str | None) -> list[dict]:
	"""One hook entry for the Nextcloud at `url`, none when the URL is empty (a site without Nextcloud)."""
	url = (url or "").strip().rstrip("/")
	if not url:
		return []
	# The name differs from the app name `compass_sso` only in the menu title; the logo is the app icon of Nextcloud (a tile in the colour of its theme), because its white logo would vanish on the white page.
	return [{"name": "nextcloud", "logo": f"{url}/apps/theming/icon", "title": "Nextcloud", "route": url, "has_permission": "compass_sso.apps_screen.has_nextcloud_access"}]


def has_desk_access() -> bool:
	"""Hook `has_permission` of the Desk entry: only a System User, who may open Desk, sees it (COMPASS REQ-045)."""
	import frappe

	return frappe.permissions.is_system_user()


def desk_entry() -> list[dict]:
	"""Desk itself as an entry of the apps menus, so CRM and Helpdesk need no fixed one that every user would see (Frappe 16 skips its own entry in `get_apps`)."""
	return [{"name": "desk", "logo": "/assets/frappe/images/framework.png", "title": "Desk", "route": "/desk", "has_permission": "compass_sso.apps_screen.has_desk_access"}]


OVERVIEW_PATH = "/start"


def landing_path(location: str) -> str:
	"""The address a user opens after signing in. Frappe 16 sends a user with several apps to `/apps`, which it redirects to Desk (a 403 for a user who may not open Desk); the overview `/start` takes its place."""
	from urllib.parse import urlsplit, urlunsplit

	parts = urlsplit(location)
	if parts.path.rstrip("/") != "/apps":
		return location
	return urlunsplit(parts._replace(path=OVERVIEW_PATH))


def window_name(app: dict) -> str:
	"""The name of the browser window an app opens in, the same as in the apps menus: a second click reuses the window. The entries of this app (Desk, Nextcloud) share the app name, so they are told apart by their title."""
	import re

	key = app["title"] if app["name"] == "compass_sso" else app["name"]
	return "compass-" + re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
