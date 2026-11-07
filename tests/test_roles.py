"""Unit tests for the Frappe roles that follow Keycloak (COMPASS REQ-023, REQ-045, REQ-046). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.roles import DESK_ROLES, GRANT, REVOKE, ROLES, keycloak_roles_by_app, role_changes


class RoleChangesTest(unittest.TestCase):
	def test_admin_in_keycloak_is_granted_the_manager_role_and_the_user_role(self):
		self.assertEqual(
			role_changes("crm", ["CRM Admin", "CRM Nutzer"], []), [(GRANT, "Sales User"), (GRANT, "Sales Manager")]
		)
		self.assertEqual(role_changes("helpdesk", ["Helpdesk Admin", "Helpdesk Nutzer"], []), [(GRANT, "Agent"), (GRANT, "Agent Manager")])
		self.assertEqual(role_changes("raven", ["Raven Admin", "Raven Nutzer"], []), [(GRANT, "Raven User"), (GRANT, "Raven Admin")])

	def test_a_plain_user_gets_only_the_user_role(self):
		self.assertEqual(role_changes("crm", ["CRM Nutzer"], []), [(GRANT, "Sales User")])
		self.assertEqual(role_changes("helpdesk", ["Helpdesk Nutzer"], []), [(GRANT, "Agent")])
		self.assertEqual(role_changes("raven", ["Raven Nutzer"], []), [(GRANT, "Raven User")])

	def test_a_taken_away_admin_role_is_revoked_and_the_user_role_stays(self):
		self.assertEqual(role_changes("crm", ["CRM Nutzer"], ["Sales User", "Sales Manager"]), [(REVOKE, "Sales Manager")])

	def test_a_taken_away_access_revokes_both_roles(self):
		self.assertEqual(role_changes("crm", [], ["Sales User", "Sales Manager"]), [(REVOKE, "Sales User"), (REVOKE, "Sales Manager")])

	def test_nothing_changes_when_both_sides_agree(self):
		self.assertEqual(role_changes("crm", ["CRM Admin", "CRM Nutzer"], ["Sales User", "Sales Manager"]), [])
		self.assertEqual(role_changes("crm", [], []), [])

	def test_a_token_without_the_claim_changes_nothing(self):
		self.assertEqual(role_changes("crm", None, ["Sales Manager"]), [])

	def test_an_unknown_app_changes_nothing(self):
		self.assertEqual(role_changes("other", ["CRM Admin"], ["Sales Manager"]), [])
		self.assertEqual(role_changes(None, ["CRM Admin"], []), [])

	def test_nextcloud_role_follows_the_keycloak_role(self):
		self.assertEqual(role_changes("nextcloud", ["Nextcloud Nutzer", "admin"], ["Sales Manager"]), [(GRANT, "Nextcloud Nutzer")])
		self.assertEqual(role_changes("nextcloud", [], ["Nextcloud Nutzer"]), [(REVOKE, "Nextcloud Nutzer")])
		self.assertEqual(role_changes("nextcloud", ["Nextcloud Nutzer"], ["Nextcloud Nutzer"]), [])

	def test_company_admin_gets_the_role_that_opens_desk(self):
		self.assertEqual(role_changes("compass-admin", ["Company Admin"], []), [(GRANT, "Company Admin")])
		self.assertEqual(role_changes("compass-admin", [], ["Company Admin"]), [(REVOKE, "Company Admin")])
		self.assertEqual(DESK_ROLES, {"Company Admin"})

	def test_the_table_never_names_a_system_role(self):
		for pairs in ROLES.values():
			for _keycloak_role, frappe_role in pairs:
				self.assertNotIn(frappe_role, ("System Manager", "Script Manager", "Administrator"))

	def test_only_company_admin_opens_desk(self):
		frappe_roles = {role for pairs in ROLES.values() for _kc, role in pairs}
		self.assertEqual(DESK_ROLES & frappe_roles, DESK_ROLES)
		self.assertEqual(len(DESK_ROLES), 1)


class KeycloakRolesByAppTest(unittest.TestCase):
	def test_one_client_carries_the_roles_of_every_app(self):
		claims = {"azp": "frappe", "resource_access": {"crm": {"roles": ["CRM Admin"]}, "raven": {"roles": ["Raven Nutzer"]}, "other": {"roles": ["x"]}}}
		self.assertEqual(
			keycloak_roles_by_app(claims),
			{"crm": ["CRM Admin"], "helpdesk": [], "raven": ["Raven Nutzer"], "nextcloud": [], "compass-admin": []},
		)

	def test_the_older_shape_names_the_client_of_the_sign_in(self):
		self.assertEqual(keycloak_roles_by_app({"azp": "crm", "roles": ["CRM Admin"]}), {"crm": ["CRM Admin"]})

	def test_a_token_without_any_roles_changes_nothing(self):
		(app, roles), = keycloak_roles_by_app({"azp": "frappe"}).items()
		self.assertEqual(role_changes(app, roles, ["Sales Manager"]), [])

	def test_a_missing_app_entry_revokes_its_roles(self):
		roles = keycloak_roles_by_app({"resource_access": {"crm": {"roles": ["CRM Nutzer"]}}})
		self.assertEqual(role_changes("helpdesk", roles["helpdesk"], ["Agent", "Agent Manager"]), [(REVOKE, "Agent"), (REVOKE, "Agent Manager")])


if __name__ == "__main__":
	unittest.main()
