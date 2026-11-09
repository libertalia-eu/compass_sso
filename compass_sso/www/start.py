"""The overview of the apps a user may open (COMPASS REQ-039): Frappe 16 removed `/apps`."""
import frappe
import frappe.apps

from compass_sso.apps_screen import window_name

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(frappe._("Sign in to see your apps"), frappe.PermissionError)
	context.title = frappe._("Select an app to continue")
	context.apps = [{**app, "window": window_name(app)} for app in frappe.apps.get_apps()]
