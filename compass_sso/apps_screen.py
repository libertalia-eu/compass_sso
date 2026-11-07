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
