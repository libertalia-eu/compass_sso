"""Unit tests for the admin role that follows Keycloak (COMPASS REQ-023). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.roles import ADMIN_ROLES, GRANT, REVOKE, admin_role_change, keycloak_roles_by_app


class AdminRoleChangeTest(unittest.TestCase):
	def test_admin_in_keycloak_is_granted_the_manager_role(self):
		self.assertEqual(admin_role_change("crm", ["CRM Admin", "CRM Nutzer"], ["Sales User"]), (GRANT, "Sales Manager"))
		self.assertEqual(admin_role_change("helpdesk", ["Helpdesk Admin"], []), (GRANT, "Agent Manager"))
		self.assertEqual(admin_role_change("raven", ["Raven Admin"], []), (GRANT, "Raven Admin"))

	def test_user_without_the_admin_role_does_not_get_it(self):
		self.assertIsNone(admin_role_change("crm", ["CRM Nutzer"], ["Sales User"]))

	def test_a_taken_away_admin_role_is_revoked(self):
		self.assertEqual(admin_role_change("crm", ["CRM Nutzer"], ["Sales Manager", "Sales User"]), (REVOKE, "Sales Manager"))

	def test_nothing_changes_when_both_sides_agree(self):
		self.assertIsNone(admin_role_change("crm", ["CRM Admin"], ["Sales Manager"]))
		self.assertIsNone(admin_role_change("crm", [], []))

	def test_a_token_without_the_claim_changes_nothing(self):
		self.assertIsNone(admin_role_change("crm", None, ["Sales Manager"]))

	def test_an_unknown_app_changes_nothing(self):
		self.assertIsNone(admin_role_change("other", ["CRM Admin"], ["Sales Manager"]))
		self.assertIsNone(admin_role_change(None, ["CRM Admin"], []))

	def test_the_table_never_names_a_system_role(self):
		for _client, (_keycloak_role, frappe_role) in ADMIN_ROLES.items():
			self.assertNotIn(frappe_role, ("System Manager", "Script Manager", "Administrator"))


class KeycloakRolesByAppTest(unittest.TestCase):
	def test_one_client_carries_the_roles_of_every_app(self):
		claims = {"azp": "frappe", "resource_access": {"crm": {"roles": ["CRM Admin"]}, "raven": {"roles": ["Raven Nutzer"]}, "other": {"roles": ["x"]}}}
		self.assertEqual(keycloak_roles_by_app(claims), {"crm": ["CRM Admin"], "helpdesk": [], "raven": ["Raven Nutzer"]})

	def test_the_older_shape_names_the_client_of_the_sign_in(self):
		self.assertEqual(keycloak_roles_by_app({"azp": "crm", "roles": ["CRM Admin"]}), {"crm": ["CRM Admin"]})

	def test_a_token_without_any_roles_changes_nothing(self):
		(app, roles), = keycloak_roles_by_app({"azp": "frappe"}).items()
		self.assertIsNone(admin_role_change(app, roles, ["Sales Manager"]))

	def test_a_missing_app_entry_revokes_its_admin_role(self):
		roles = keycloak_roles_by_app({"resource_access": {"crm": {"roles": ["CRM Nutzer"]}}})
		self.assertEqual(admin_role_change("helpdesk", roles["helpdesk"], ["Agent Manager"]), (REVOKE, "Agent Manager"))


if __name__ == "__main__":
	unittest.main()
