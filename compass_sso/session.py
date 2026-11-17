import time

import frappe
import requests

from compass_sso import keycloak, store
from compass_sso.login_redirect import redirect_guest_to_keycloak

CHECK_INTERVAL_SECONDS = 30


def next_step(remembered: dict | None, now: float) -> str:
	"""end: no token remembered (the cache was lost); skip: checked a moment ago; check: renew the refresh token."""
	if not remembered:
		return "end"
	return "skip" if now - remembered["checked_at"] < CHECK_INTERVAL_SECONDS else "check"


def _end_session():
	store.forget(frappe.session.sid)
	frappe.local.login_manager.logout()
	frappe.db.commit()
	# A page goes to the sign-in like a guest; an API call keeps the 401 (the user is Guest only from the next request on, so pass it).
	redirect_guest_to_keycloak("Guest")
	raise frappe.SessionExpired


def check_keycloak_session():
	"""before_request: while the Keycloak session lives, its refresh token can be renewed; once it ended, cannot be confirmed or its token is gone, so does Frappe's."""
	if frappe.session.user == "Guest":
		return
	remembered = store.recall(frappe.session.sid)
	step = next_step(remembered, time.time())
	if step == "end":
		_end_session()
	if step == "skip":
		return
	try:
		tokens = keycloak.refresh(remembered["refresh_token"])
	except (keycloak.KeycloakSessionEnded, requests.RequestException):
		# Keycloak unreachable counts as ended (fails closed): the Keycloak session cannot be confirmed, so Frappe's ends too.
		_end_session()
	store.remember(frappe.session.sid, remembered["keycloak_sid"], tokens["refresh_token"], time.time())
