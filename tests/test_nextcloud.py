"""Unit tests for the pure parts of the Nextcloud references (COMPASS REQ-047). No Frappe site needed: python -m unittest."""
import unittest

from compass_sso.nextcloud import is_nextcloud_url, is_resolved, parse_entries, title_of, visible_providers

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
	def test_an_accessible_object_is_resolved_with_or_without_a_name(self):
		self.assertTrue(is_resolved({BASE + "/f/1": {"accessible": True, "richObject": {"name": "Readme.md"}}}, BASE + "/f/1"))
		self.assertTrue(is_resolved({BASE + "/p": {"accessible": True, "richObject": {"page": {"title": "Page"}}}}, BASE + "/p"))

	def test_an_inaccessible_object_is_not_even_with_a_name(self):
		self.assertFalse(is_resolved({BASE + "/f/1": {"accessible": False, "richObject": {"name": BASE + "/f/1"}}}, BASE + "/f/1"))
		self.assertFalse(is_resolved({BASE + "/p": {"accessible": False, "richObject": {"link": BASE + "/p"}}}, BASE + "/p"))

	def test_a_link_nextcloud_cannot_judge_is_not_even_when_accessible(self):
		bare = {"accessible": True, "richObjectType": "open-graph", "richObject": {"name": BASE + "/c/1"}}
		self.assertFalse(is_resolved({BASE + "/c/1": bare}, BASE + "/c/1"))

	def test_no_reference_is_not(self):
		self.assertFalse(is_resolved({BASE + "/f/1": None}, BASE + "/f/1"))
		self.assertFalse(is_resolved({}, BASE + "/f/1"))


class TitleOfTest(unittest.TestCase):
	def test_name_then_page_title_then_the_link(self):
		self.assertEqual(title_of({"u": {"richObject": {"name": "Readme.md"}}}, "u"), "Readme.md")
		self.assertEqual(title_of({"u": {"richObject": {"page": {"title": "Page"}}}}, "u"), "Page")
		self.assertEqual(title_of({"u": {"richObject": {}}}, "u"), "u")


class AccessTokenTest(unittest.TestCase):
	"""The text the picker shows depends on which error type the token step raises."""

	def call_with(self, recall=None, refresh_error=None):
		from unittest.mock import MagicMock, patch

		from compass_sso import nextcloud

		with patch.object(nextcloud, "frappe", MagicMock()), patch.object(nextcloud.store, "recall", return_value=recall), patch.object(
			nextcloud.keycloak, "refresh", side_effect=refresh_error, return_value={"access_token": "t", "refresh_token": "r"}
		), patch.object(nextcloud.store, "remember"):
			return nextcloud._access_token()

	def test_a_session_without_a_stored_token_is_an_ended_session(self):
		from compass_sso.nextcloud import NextcloudSessionEnded

		with self.assertRaises(NextcloudSessionEnded):
			self.call_with(recall=None)

	def test_a_refused_refresh_token_is_an_ended_session(self):
		from compass_sso import keycloak
		from compass_sso.nextcloud import NextcloudSessionEnded

		with self.assertRaises(NextcloudSessionEnded):
			self.call_with(recall={"refresh_token": "x", "keycloak_sid": "k", "checked_at": 0}, refresh_error=keycloak.KeycloakSessionEnded)

	def test_keycloak_down_is_not_an_ended_session(self):
		import requests

		from compass_sso.nextcloud import NextcloudSessionEnded, NextcloudUnavailable

		with self.assertRaises(NextcloudUnavailable) as caught:
			self.call_with(recall={"refresh_token": "x", "keycloak_sid": "k", "checked_at": 0}, refresh_error=requests.ConnectionError)
		self.assertNotIsInstance(caught.exception, NextcloudSessionEnded)

	def test_a_good_token_is_returned(self):
		self.assertEqual(self.call_with(recall={"refresh_token": "x", "keycloak_sid": "k", "checked_at": 0}), "t")


class SearchWithoutTermTest(unittest.TestCase):
	"""Nextcloud refuses a search without a term, so the search must not reach it."""

	def search(self, term):
		from unittest.mock import MagicMock, patch

		from compass_sso import nextcloud

		with patch.object(nextcloud, "_get", MagicMock()) as get, patch.object(nextcloud, "providers", MagicMock(return_value=[{"id": "files"}])):
			return getattr(nextcloud.search, "__wrapped__", nextcloud.search)("files", term), get

	def test_an_empty_or_blank_term_gives_no_entries_and_asks_nobody(self):
		for term in ("", "   "):
			result, get = self.search(term)
			self.assertEqual(result, {"entries": [], "cursor": None})
			get.assert_not_called()

	def test_a_term_still_asks_nextcloud(self):
		result, get = self.search("Readme")
		get.assert_called_once()
