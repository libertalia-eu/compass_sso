LOGIN_PATH = "/login"


def goes_to_keycloak(method: str, path: str, user: str, app_routes) -> bool:
	"""A guest who opens the login page, the site root or one of the apps. The app's own page would only show an error (CRM) or redirect with JavaScript."""
	if method != "GET" or user != "Guest":
		return False
	return path in (LOGIN_PATH, "/") or any(path == f"/{route}" or path.startswith(f"/{route}/") for route in app_routes)


def app_routes_of(apps_screen: list, home_page: str | None) -> set:
	"""The routes of the apps on this site, without the slash: the entries of `add_to_apps_screen`, the app switcher `apps` and the home page."""
	routes = {entry["route"].strip("/") for entry in apps_screen if entry.get("route")}
	return {route for route in routes | {"apps", home_page or ""} if route}


def redirect_guest_to_keycloak():
	"""before_request: send the guest straight to Keycloak; the page asked for survives as the OAuth state."""
	import frappe
	from frappe.utils.oauth import get_oauth2_authorize_url
	from frappe.www.login import sanitize_redirect
	from werkzeug.exceptions import HTTPException
	from werkzeug.utils import redirect

	from compass_sso import keycloak

	request = frappe.local.request
	app_routes = app_routes_of(frappe.get_hooks("add_to_apps_screen"), frappe.db.get_single_value("Website Settings", "home_page"))
	if not goes_to_keycloak(request.method, request.path, frappe.session.user, app_routes):
		return
	if not frappe.db.exists("Social Login Key", {"name": keycloak.PROVIDER, "enable_social_login": 1}):
		return
	asked_for = request.args.get("redirect-to") if request.path == LOGIN_PATH else request.full_path.rstrip("?")
	url = get_oauth2_authorize_url(keycloak.PROVIDER, sanitize_redirect(asked_for))
	raise HTTPException(response=redirect(url))
