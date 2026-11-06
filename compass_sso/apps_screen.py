"""The entry for Nextcloud in the app overview and the apps menus of the Frappe apps (COMPASS REQ-039)."""


def nextcloud_entry(url: str | None) -> list[dict]:
	"""One hook entry for the Nextcloud at `url`, none when the URL is empty (a site without Nextcloud)."""
	url = (url or "").strip().rstrip("/")
	if not url:
		return []
	# The name differs from the app name `compass_sso` only in the menu title; the logo is the app icon of Nextcloud (a tile in the colour of its theme), because its white logo would vanish on the white page.
	return [{"name": "nextcloud", "logo": f"{url}/apps/theming/icon", "title": "Nextcloud", "route": url}]
