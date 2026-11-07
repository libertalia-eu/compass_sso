"""Unit tests for the pure parts of the Nextcloud references (COMPASS REQ-047). No Frappe site needed: python -m unittest."""
import unittest

from compass_sso.nextcloud import is_nextcloud_url, is_resolved, parse_entries, visible_providers

BASE = "https://cloud.libertalia.localhost"


class VisibleProvidersTest(unittest.TestCase):
	def test_settings_and_comments_are_hidden_and_objects_stay(self):
		providers = [{"id": "files", "name": "Files"}, {"id": "settings"}, {"id": "settings_apps"}, {"id": "comments"}, {"id": "search-deck-comment"}, {"id": "search-deck-card-board", "name": "Deck"}]
		self.assertEqual(
			visible_providers(providers), [{"id": "files", "name": "Files"}, {"id": "search-deck-card-board", "name": "Deck"}]
		)

	def test_a_provider_without_name_shows_its_id(self):
		self.assertEqual(visible_providers([{"id": "notes"}]), [{"id": "notes", "name": "notes"}])


class ParseEntriesTest(unittest.TestCase):
	def test_entries_keep_title_subline_link_and_thumbnail_and_the_cursor_while_paginated(self):
		data = {"isPaginated": True, "cursor": 5, "entries": [{"title": "Readme.md", "resourceUrl": BASE + "/f/1", "thumbnailUrl": "t"}, {"title": "no link"}]}
		self.assertEqual(
			parse_entries(data), {"entries": [{"title": "Readme.md", "subline": "", "url": BASE + "/f/1", "thumbnail": "t"}], "cursor": 5}
		)

	def test_no_cursor_when_the_provider_is_not_paginated(self):
		self.assertIsNone(parse_entries({"isPaginated": False, "cursor": 3, "entries": []})["cursor"])


class IsNextcloudUrlTest(unittest.TestCase):
	def test_only_the_host_of_nextcloud_is_accepted(self):
		self.assertTrue(is_nextcloud_url(BASE + "/f/1", BASE))
		self.assertFalse(is_nextcloud_url("https://example.org/f/1", BASE))
		self.assertFalse(is_nextcloud_url("http://cloud.libertalia.localhost/f/1", BASE))
		self.assertFalse(is_nextcloud_url(BASE + ".evil.test/f/1", BASE))
		self.assertFalse(is_nextcloud_url("//cloud.libertalia.localhost/f/1", BASE))
		self.assertFalse(is_nextcloud_url("not a url", BASE))


class IsResolvedTest(unittest.TestCase):
	def test_a_named_object_is_resolved(self):
		self.assertTrue(is_resolved({BASE + "/f/1": {"richObject": {"name": "Readme.md"}}}, BASE + "/f/1"))

	def test_the_bare_object_for_a_forbidden_link_is_not(self):
		self.assertFalse(is_resolved({BASE + "/f/1": {"richObject": {"name": BASE + "/f/1"}}}, BASE + "/f/1"))

	def test_no_reference_is_not(self):
		self.assertFalse(is_resolved({BASE + "/f/1": None}, BASE + "/f/1"))
		self.assertFalse(is_resolved({}, BASE + "/f/1"))
