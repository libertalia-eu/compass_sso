"""The Keycloak groups of a user set their Frappe role profiles at sign-in (COMPASS REQ-102)."""


def profile_names(claims: dict, existing: set[str]) -> list[str]:
	"""The role profiles the sign-in asks for: the groups of the claims that name a Role Profile. Other groups are ignored."""
	groups = claims.get("groups")
	if not isinstance(groups, list):
		return []
	return [group for group in groups if group in existing]


def on_social_login(user: str, provider: str, claims: dict) -> None:
	"""Hook `on_social_login`: set the role profiles of `user` to the ones the groups name.

	Frappe derives the roles from the profiles on every save and drops the roles no profile gives. With no profile left it
	keeps the old roles, so they are cleared here."""
	import frappe

	from compass_sso import keycloak

	# a token without the claim `groups` (an old client) changes nothing
	if provider != keycloak.PROVIDER or not isinstance(claims.get("groups"), list):
		return
	names = profile_names(claims, set(frappe.get_all("Role Profile", pluck="name")))
	account = frappe.get_doc("User", user)
	account.flags.ignore_permissions = True
	account.set("role_profiles", [{"role_profile": name} for name in names])
	if not names:
		account.set("roles", [])
	account.save()
	# the callback is a GET request, for which Frappe does not commit by itself
	frappe.db.commit()
