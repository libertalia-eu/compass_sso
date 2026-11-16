"""The Frappe language of a user follows the Keycloak attribute `locale` of the sign-in (COMPASS REQ-088)."""

SUPPORTED = ("de", "en")
DEFAULT = "en"


def language_of(claims: dict) -> str:
	"""The claim `locale` when COMPASS has that language, else English (a user who never chose one)."""
	locale = claims.get("locale")
	return locale if locale in SUPPORTED else DEFAULT


def sync_language(user: str, claims: dict) -> None:
	import frappe

	language = language_of(claims)
	if frappe.db.get_value("User", user, "language") != language:
		frappe.db.set_value("User", user, "language", language)
		# the callback is a GET request, for which Frappe does not commit by itself
		frappe.db.commit()
