"""Sign-in callback of the Keycloak client: same result as Frappe's own, plus keeping the refresh token."""
import time

import frappe
import jwt
from frappe.utils.oauth import get_oauth2_providers, login_oauth_user

from compass_sso import keycloak, roles, store


@frappe.whitelist(allow_guest=True)
def keycloak_login(code: str, state: str):
	redirect_uri = frappe.utils.oauth.get_redirect_uri(keycloak.PROVIDER)
	tokens = keycloak.exchange_code(code, redirect_uri)
	# shortcut: unsigned decode, the token comes straight from the token endpoint over TLS (OIDC Core 3.1.3.7)
	claims = jwt.decode(tokens["id_token"], options={"verify_signature": False})
	login_oauth_user(claims, provider=keycloak.PROVIDER, state=state)
	if frappe.session.user != "Guest":
		roles.sync_admin_role(frappe.session.user, claims)
		store.remember(frappe.session.sid, claims["sid"], tokens["refresh_token"], time.time())
