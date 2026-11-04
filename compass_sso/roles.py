"""The admin role of a Frappe app follows a role in Keycloak (COMPASS REQ-023)."""

# One entry per app, keyed by the Keycloak client id: the Keycloak client role and the Frappe role it stands for. This table
# is the only way a Keycloak role becomes a Frappe role: it never names System Manager or Script Manager.
ADMIN_ROLES = {
	"crm": ("CRM Admin", "Sales Manager"),
	"helpdesk": ("Helpdesk Admin", "Agent Manager"),
	"raven": ("Raven Admin", "Raven Admin"),
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


def sync_admin_role(user: str, claims: dict) -> None:
	"""Give or take away the admin role of the app for `user`, as the claims of the sign-in say. Other roles stay as they are."""
	import frappe

	change = admin_role_change(claims.get("azp"), claims.get("roles"), frappe.get_roles(user))
	if change is None:
		return
	action, role = change
	account = frappe.get_doc("User", user)
	account.flags.ignore_permissions = True
	if action == GRANT:
		account.add_roles(role)
	else:
		account.remove_roles(role)
	# the callback is a GET request, for which Frappe does not commit by itself (login_oauth_user commits before this runs)
	frappe.db.commit()
