"""The entry for Nextcloud in the app overview and the apps menus of the Frappe apps (COMPASS REQ-039)."""


def nextcloud_entry(url: str | None) -> list[dict]:
	"""One hook entry for the Nextcloud at `url`, none when the URL is empty (a site without Nextcloud)."""
	url = (url or "").strip().rstrip("/")
	if not url:
		return []
	# The name differs from the app name `compass_sso` only in the menu title; the logo comes from Nextcloud, so it follows its theme.
	return [{"name": "nextcloud", "logo": f"{url}/core/img/logo/logo.svg", "title": "Nextcloud", "route": url}]
