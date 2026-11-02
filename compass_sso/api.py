import frappe
import requests
from frappe.handler import logout as frappe_logout

from compass_sso import keycloak, store
from compass_sso.logout_token import LogoutTokenRefused, verify_logout_token


@frappe.whitelist(allow_guest=True)
def logout():
	"""Replaces `logout`: end the Keycloak session first, then the Frappe session as before."""
	remembered = store.recall(frappe.session.sid)
	if remembered:
		try:
			keycloak.end_session(remembered["refresh_token"])
		except Exception:
			frappe.log_error(title="Keycloak logout failed")
		store.forget(frappe.session.sid)
	return frappe_logout()


@frappe.whitelist(allow_guest=True, methods=["POST"])
def backchannel_logout(logout_token: str):
	"""Keycloak calls this when the Keycloak session ends (OIDC Back-Channel Logout 1.0)."""
	try:
		claims = verify_logout_token(
			logout_token,
			keycloak.signing_keys(),
			keycloak.realm_url(),
			frappe.get_doc("Social Login Key", keycloak.PROVIDER).client_id,
			store.claim_jti,
		)
	except (LogoutTokenRefused, requests.RequestException) as error:
		frappe.log_error(title="Back-channel logout token refused", message=repr(error))
		frappe.local.response["http_status_code"] = 400
		return {"error": "invalid_request"}
	for frappe_sid in store.frappe_sessions_of(claims["sid"]):
		frappe.sessions.delete_session(frappe_sid, reason="Keycloak back-channel logout")
		store.forget(frappe_sid)
	return {}
