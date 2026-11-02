import time

import frappe

from compass_sso import keycloak, store

CHECK_INTERVAL_SECONDS = 30


def check_keycloak_session():
	"""before_request: while the Keycloak session lives, its refresh token can be renewed; once it ended, so does Frappe's."""
	if frappe.session.user == "Guest":
		return
	remembered = store.recall(frappe.session.sid)
	if not remembered or time.time() - remembered["checked_at"] < CHECK_INTERVAL_SECONDS:
		return
	try:
		tokens = keycloak.refresh(remembered["refresh_token"])
	except keycloak.KeycloakSessionEnded:
		store.forget(frappe.session.sid)
		frappe.local.login_manager.logout()
		frappe.db.commit()
		raise frappe.SessionExpired from None
	store.remember(frappe.session.sid, remembered["keycloak_sid"], tokens["refresh_token"], time.time())
