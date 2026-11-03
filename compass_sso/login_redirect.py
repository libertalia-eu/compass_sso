LOGIN_PATH = "/login"


def goes_to_keycloak(method: str, path: str, user: str, app_route: str) -> bool:
	"""A guest who opens the login page, the site root (the home page is the app) or the app itself. The app's own page would only show an error (CRM) or redirect with JavaScript."""
	if method != "GET" or user != "Guest":
		return False
	return path in (LOGIN_PATH, "/", f"/{app_route}") or path.startswith(f"/{app_route}/")


def redirect_guest_to_keycloak():
	"""before_request: send the guest straight to Keycloak; the page asked for survives as the OAuth state."""
	import frappe
	from frappe.utils.oauth import get_oauth2_authorize_url
	from frappe.www.login import sanitize_redirect
	from werkzeug.exceptions import HTTPException
	from werkzeug.utils import redirect

	from compass_sso import keycloak

	request = frappe.local.request
	# shortcut: the app route is the site's home page (COMPASS setup-sites.sh); a site with another layout needs a setting.
	app_route = frappe.db.get_single_value("Website Settings", "home_page") or LOGIN_PATH.strip("/")
	if not goes_to_keycloak(request.method, request.path, frappe.session.user, app_route):
		return
	if not frappe.db.exists("Social Login Key", {"name": keycloak.PROVIDER, "enable_social_login": 1}):
		return
	asked_for = request.args.get("redirect-to") if request.path == LOGIN_PATH else request.full_path.rstrip("?")
	url = get_oauth2_authorize_url(keycloak.PROVIDER, sanitize_redirect(asked_for))
	raise HTTPException(response=redirect(url))
