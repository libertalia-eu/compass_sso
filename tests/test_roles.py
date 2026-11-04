"""Unit tests for the admin role that follows Keycloak (COMPASS REQ-023). No Frappe needed: python -m unittest."""
import unittest

from compass_sso.roles import ADMIN_ROLES, GRANT, REVOKE, admin_role_change


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


if __name__ == "__main__":
	unittest.main()
