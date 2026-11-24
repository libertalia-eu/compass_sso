import json
import unittest
from pathlib import Path

from compass_sso.profiles import profile_names

EXISTING = {"CRM Nutzer", "CRM Admin"}
FIXTURES = Path(__file__).parent.parent / "compass_sso" / "fixtures"


class TestProfiles(unittest.TestCase):
	def test_group_names_the_profile(self):
		self.assertEqual(profile_names({"groups": ["CRM Nutzer"]}, EXISTING), ["CRM Nutzer"])

	def test_unknown_group_is_ignored(self):
		self.assertEqual(profile_names({"groups": ["Sales", "CRM Admin"]}, EXISTING), ["CRM Admin"])

	def test_no_groups(self):
		self.assertEqual(profile_names({"groups": []}, EXISTING), [])
		self.assertEqual(profile_names({}, EXISTING), [])
		self.assertEqual(profile_names({"groups": "CRM Admin"}, EXISTING), [])

	def test_no_profile_gives_a_system_role(self):
		for profile in json.loads((FIXTURES / "role_profile.json").read_text()):
			roles = {row["role"] for row in profile["roles"]}
			self.assertFalse(roles & {"System Manager", "Script Manager"}, profile["name"])
