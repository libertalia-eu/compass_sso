"""The Frappe roles of a user follow the Keycloak client roles of the sign-in (COMPASS REQ-023, REQ-045, REQ-046)."""

# One list per Keycloak client id: the Keycloak client role and the Frappe role it stands for. This table is the only way a
# Keycloak role becomes a Frappe role: it never names System Manager or Script Manager. `X Nutzer` gives the role to work in the
# app, `X Admin` the manager role (the admin role includes the user role in Keycloak, so an admin gets both).
# Nextcloud is no Frappe app: its role only tells the apps menu that the user may open it (`apps_screen.has_nextcloud_access`).
# The Company Admin role of the client `compass-admin` is the one that gives access to Desk.
ROLES = {
	"crm": [("CRM Nutzer", "Sales User"), ("CRM Admin", "Sales Manager")],
	"helpdesk": [("Helpdesk Nutzer", "Agent"), ("Helpdesk Admin", "Agent Manager")],
	"raven": [("Raven Nutzer", "Raven User"), ("Raven Admin", "Raven Admin")],
	"nextcloud": [("Nextcloud Nutzer", "Nextcloud Nutzer")],
	"compass-admin": [("Company Admin", "Company Admin")],
}

# The Frappe roles that open Desk (desk_access = 1); every other role the table creates gives no access to Desk (REQ-044).
DESK_ROLES = {"Company Admin"}

GRANT = "grant"
REVOKE = "revoke"


def role_changes(client_id: str, keycloak_roles: list[str], frappe_roles: list[str]) -> list[tuple[str, str]]:
	"""Which changes of the Frappe roles the sign-in asks for: a list of (GRANT or REVOKE, the Frappe role).

	`keycloak_roles` is the claim `roles` of the id token (the client roles of the user, composites included).
	An app that is not in the table, or a token without the claim, changes nothing."""
	if client_id not in ROLES or not isinstance(keycloak_roles, list):
		return []
	changes = []
	for keycloak_role, frappe_role in ROLES[client_id]:
		wanted = keycloak_role in keycloak_roles
		has = frappe_role in frappe_roles
		if wanted and not has:
			changes.append((GRANT, frappe_role))
		elif has and not wanted:
			changes.append((REVOKE, frappe_role))
	return changes


def keycloak_roles_by_app(claims: dict) -> dict:
	"""The Keycloak client roles of each app from the claims of the sign-in: {client id: roles}.

	A site with several apps signs in through one client, and the roles of every app are in `resource_access`
	(Keycloak's own shape). An app without an entry there has none of its roles. Without `resource_access`, the
	older shape applies: the client of the sign-in (`azp`) and its roles in the claim `roles`."""
	resource_access = claims.get("resource_access")
	if isinstance(resource_access, dict):
		return {app: (resource_access.get(app) or {}).get("roles", []) for app in ROLES}
	return {claims.get("azp"): claims.get("roles")}


def ensure_role(name: str) -> None:
	"""Create the Frappe role when it is missing (the roles of the apps exist, the ones for Nextcloud and the Company Admin do not)."""
	import frappe

	if not frappe.db.exists("Role", name):
		frappe.get_doc(doctype="Role", role_name=name, desk_access=int(name in DESK_ROLES)).insert(ignore_permissions=True)


def sync_roles(user: str, claims: dict) -> None:
	"""Give or take away the roles of the table for `user`, as the claims of the sign-in say. Other roles stay as they are."""
	import frappe

	frappe_roles = frappe.get_roles(user)
	changes = [change for app, roles in keycloak_roles_by_app(claims).items() for change in role_changes(app, roles, frappe_roles)]
	if not changes:
		return
	account = frappe.get_doc("User", user)
	account.flags.ignore_permissions = True
	for action, role in changes:
		if action == GRANT:
			ensure_role(role)
			account.add_roles(role)
		else:
			account.remove_roles(role)
	# the callback is a GET request, for which Frappe does not commit by itself (login_oauth_user commits before this runs)
	frappe.db.commit()
