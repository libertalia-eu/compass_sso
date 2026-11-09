"""Nextcloud objects as link cards in the Frappe apps (COMPASS REQ-047).

Every call to Nextcloud carries the Keycloak access token of the signed-in user, so Nextcloud decides what the user sees.
"""
import os
from urllib.parse import quote, urlsplit

import frappe
import requests

from compass_sso import keycloak, store

TIMEOUT_SECONDS = 10
REFERENCE_DOCTYPE = "Nextcloud Reference"
# Search providers that return settings or comments, not an object one can link to, and those whose apps have no reference provider
# (Teams, Tags, Contacts): Nextcloud cannot say who may open their objects, so a card would show them to everybody.
HIDDEN_PROVIDERS = {"settings", "settings_apps", "comments", "circles", "systemtags", "contacts"}
ACCESS_CACHE_SECONDS = 60


class NextcloudUnavailable(frappe.ValidationError):
	"""Nextcloud is unreachable, refuses the token, or is not configured for this site."""


class NextcloudSessionEnded(frappe.ValidationError):
	"""The user's Keycloak sign-in is gone (no stored token, or Keycloak refused it): only a new sign-in helps. The picker shows its own text for this type."""


def base_url() -> str:
	url = (os.environ.get("COMPASS_NEXTCLOUD_URL") or "").rstrip("/")
	if not url:
		raise NextcloudUnavailable("Nextcloud is not configured for this site.")
	return url


def is_nextcloud_url(url: str, base: str) -> bool:
	"""Same scheme and host as Nextcloud: Nextcloud itself resolves any URL it is given, so a foreign one must never reach it."""
	given, own = urlsplit(url), urlsplit(base)
	return bool(given.scheme and given.hostname) and (given.scheme, given.hostname, given.port) == (own.scheme, own.hostname, own.port)


def visible_providers(providers: list[dict]) -> list[dict]:
	return [
		{"id": provider["id"], "name": provider.get("name") or provider["id"]}
		for provider in providers
		if provider["id"] not in HIDDEN_PROVIDERS and not provider["id"].endswith("comment")
	]


def parse_entries(data: dict) -> dict:
	return {
		"entries": [
			{
				"title": entry.get("title") or "",
				"subline": entry.get("subline") or "",
				"url": entry["resourceUrl"],
				"thumbnail": entry.get("thumbnailUrl") or "",
			}
			for entry in data.get("entries", [])
			if entry.get("resourceUrl")
		],
		"cursor": data.get("cursor") if data.get("isPaginated") else None,
	}


def is_resolved(references: dict, url: str) -> bool:
	"""Nextcloud flags a link the user may not open with `accessible: false`. A link without a reference provider of its app (Teams, Tags, Contacts) comes back as `open-graph`, `accessible` for everybody: Nextcloud cannot judge it, so it counts as no access."""
	reference = references.get(url) or {}
	return bool(reference.get("accessible")) and reference.get("richObjectType") != "open-graph"


def title_of(references: dict, url: str) -> str:
	"""Most apps put `name` into the rich object; Collectives puts the title of the page into `page`."""
	rich = references[url].get("richObject") or {}
	return rich.get("name") or (rich.get("page") or {}).get("title") or url


def _access_token() -> str:
	remembered = store.recall(frappe.session.sid)
	if not remembered:
		raise NextcloudSessionEnded("The Keycloak session has ended. Sign in again.")
	try:
		tokens = keycloak.refresh(remembered["refresh_token"])
	except keycloak.KeycloakSessionEnded:
		raise NextcloudSessionEnded("The Keycloak session has ended. Sign in again.") from None
	except requests.RequestException:
		raise NextcloudUnavailable("Keycloak is not reachable.") from None
	store.remember(frappe.session.sid, remembered["keycloak_sid"], tokens["refresh_token"], remembered["checked_at"])
	return tokens["access_token"]


def _get(path: str, params: dict | None = None) -> dict:
	try:
		response = requests.get(
			base_url() + path,
			params=params,
			headers={"Authorization": f"Bearer {_access_token()}", "OCS-APIRequest": "true", "Accept": "application/json"},
			timeout=TIMEOUT_SECONDS,
		)
	except requests.RequestException:
		raise NextcloudUnavailable("Nextcloud is not reachable.") from None
	if response.status_code in (401, 403):
		raise NextcloudUnavailable("Nextcloud refused the sign-in.")
	if response.status_code == 404:
		raise frappe.DoesNotExistError("Unknown Nextcloud search provider.")
	if not response.ok:
		raise NextcloudUnavailable("Nextcloud answered with an error.")
	return response.json()["ocs"]["data"]


@frappe.whitelist(methods=["GET"])
def providers() -> list[dict]:
	return visible_providers(_get("/ocs/v2.php/search/providers", {"format": "json"}))


@frappe.whitelist(methods=["GET"])
def search(provider: str, term: str = "", cursor: str | None = None) -> dict:
	# Nextcloud answers a search without a term with 400 ("no valid filters"), so there is nothing to ask for.
	if not term.strip():
		return parse_entries({})
	if provider not in {entry["id"] for entry in providers()}:
		raise frappe.DoesNotExistError("Unknown Nextcloud search provider.")
	params = {"term": term, "format": "json"} | ({"cursor": cursor} if cursor else {})
	return parse_entries(_get(f"/ocs/v2.php/search/providers/{quote(provider, safe='')}/search", params))


def _resolve(url: str) -> dict:
	if not is_nextcloud_url(url, base_url()):
		raise frappe.ValidationError("Only links to Nextcloud can be referenced.")
	return _get("/ocs/v2.php/references/resolve", {"reference": url, "format": "json"})["references"]


@frappe.whitelist(methods=["POST"])
def reference(url: str, title: str = "", subline: str = "", thumbnail: str = "") -> str:
	"""The Nextcloud Reference for `url` (made when it is new), to attach to a Raven message. A pasted link has no title yet: Nextcloud names it."""
	references = _resolve(url)
	if not is_resolved(references, url):
		raise frappe.PermissionError("You have no access to this Nextcloud object.")
	if not title:
		title = title_of(references, url)
	name = frappe.db.get_value(REFERENCE_DOCTYPE, {"url": url})
	if name:
		return name
	doc = frappe.get_doc(
		{"doctype": REFERENCE_DOCTYPE, "url": url, "title": title, "subline": subline, "thumbnail": thumbnail}
	)
	doc.insert()
	return doc.name


def reference_has_permission(doc, ptype=None, user=None, **kwargs) -> bool:
	"""Hook `has_permission` of the Nextcloud Reference: reading asks Nextcloud again, with the token of the user who reads."""
	if ptype not in (None, "read") or (user and user != frappe.session.user):
		return True
	cache_key = f"compass_sso:nextcloud_access:{frappe.session.user}:{doc.url}"
	allowed = frappe.cache.get_value(cache_key)
	if allowed is None:
		try:
			allowed = is_resolved(_resolve(doc.url), doc.url)
		except (NextcloudUnavailable, NextcloudSessionEnded):
			return False
		frappe.cache.set_value(cache_key, allowed, expires_in_sec=ACCESS_CACHE_SECONDS)
	return allowed


def document_link(doctype: str, docname: str) -> str | None:
	"""Hook `raven_document_link_override`: a Nextcloud Reference opens in Nextcloud, not in the desk."""
	if doctype == REFERENCE_DOCTYPE:
		return frappe.db.get_value(REFERENCE_DOCTYPE, docname, "url")
