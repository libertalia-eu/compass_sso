LOGIN_PATH = "/login"


def is_guest_login_page_request(method: str, path: str, user: str) -> bool:
	return method == "GET" and path == LOGIN_PATH and user == "Guest"


def redirect_login_page_to_keycloak():
	"""before_request: a guest who opens the login page goes straight to Keycloak; `redirect-to` survives as the OAuth state."""
	import frappe
	from frappe.utils.oauth import get_oauth2_authorize_url
	from frappe.www.login import sanitize_redirect
	from werkzeug.exceptions import HTTPException
	from werkzeug.utils import redirect

	from compass_sso import keycloak

	request = frappe.local.request
	if not is_guest_login_page_request(request.method, request.path, frappe.session.user):
		return
	if not frappe.db.exists("Social Login Key", {"name": keycloak.PROVIDER, "enable_social_login": 1}):
		return
	url = get_oauth2_authorize_url(keycloak.PROVIDER, sanitize_redirect(request.args.get("redirect-to")))
	raise HTTPException(response=redirect(url))
