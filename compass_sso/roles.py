"""The admin role of a Frappe app and the access to Nextcloud follow a role in Keycloak (COMPASS REQ-023, REQ-045)."""

# One entry per app, keyed by the Keycloak client id: the Keycloak client role and the Frappe role it stands for. This table
# is the only way a Keycloak role becomes a Frappe role: it never names System Manager or Script Manager.
ADMIN_ROLES = {
	"crm": ("CRM Admin", "Sales Manager"),
	"helpdesk": ("Helpdesk Admin", "Agent Manager"),
	"raven": ("Raven Admin", "Raven Admin"),
	# Nextcloud is no Frappe app: the role only tells the apps menu that the user may open it (`apps_screen.has_nextcloud_access`).
	"nextcloud": ("Nextcloud Nutzer", "Nextcloud Nutzer"),
}

GRANT = "grant"
REVOKE = "revoke"


def admin_role_change(client_id: str, keycloak_roles: list[str], frappe_roles: list[str]) -> tuple[str, str] | None:
	"""Which change of the Frappe role the sign-in asks for: (GRANT or REVOKE, the Frappe role), or None.

	`keycloak_roles` is the claim `roles` of the id token (the client roles of the user, composites included).
	An app that is not in the table, or a token without the claim, changes nothing."""
	if client_id not in ADMIN_ROLES or not isinstance(keycloak_roles, list):
		return None
	keycloak_role, frappe_role = ADMIN_ROLES[client_id]
	wanted = keycloak_role in keycloak_roles
	has = frappe_role in frappe_roles
	if wanted and not has:
		return GRANT, frappe_role
	if has and not wanted:
		return REVOKE, frappe_role
	return None


def keycloak_roles_by_app(claims: dict) -> dict:
	"""The Keycloak client roles of each app from the claims of the sign-in: {client id: roles}.

	A site with several apps signs in through one client, and the roles of every app are in `resource_access`
	(Keycloak's own shape). An app without an entry there has none of its roles. Without `resource_access`, the
	older shape applies: the client of the sign-in (`azp`) and its roles in the claim `roles`."""
	resource_access = claims.get("resource_access")
	if isinstance(resource_access, dict):
		return {app: (resource_access.get(app) or {}).get("roles", []) for app in ADMIN_ROLES}
	return {claims.get("azp"): claims.get("roles")}


def ensure_role(name: str) -> None:
	"""Create the Frappe role when it is missing (the roles of the apps exist, the one for Nextcloud does not). It gives no access to Desk."""
	import frappe

	if not frappe.db.exists("Role", name):
		frappe.get_doc(doctype="Role", role_name=name, desk_access=0).insert(ignore_permissions=True)


def sync_admin_role(user: str, claims: dict) -> None:
	"""Give or take away the admin roles of the apps for `user`, as the claims of the sign-in say. Other roles stay as they are."""
	import frappe

	frappe_roles = frappe.get_roles(user)
	changes = [admin_role_change(app, roles, frappe_roles) for app, roles in keycloak_roles_by_app(claims).items()]
	changes = [change for change in changes if change]
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
