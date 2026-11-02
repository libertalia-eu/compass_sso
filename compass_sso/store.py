"""Keycloak tokens per Frappe session, kept in the Redis cache (never in the database)."""
import frappe

SESSION_TTL_SECONDS = 12 * 3600  # above the Keycloak maximum of 10 hours


def remember(frappe_sid: str, keycloak_sid: str, refresh_token: str, checked_at: float) -> None:
	frappe.cache.set_value(
		f"compass_sso:session:{frappe_sid}",
		{"keycloak_sid": keycloak_sid, "refresh_token": refresh_token, "checked_at": checked_at},
		expires_in_sec=SESSION_TTL_SECONDS,
	)
	sessions = frappe.cache.get_value(f"compass_sso:keycloak:{keycloak_sid}") or []
	if frappe_sid not in sessions:
		frappe.cache.set_value(
			f"compass_sso:keycloak:{keycloak_sid}", [*sessions, frappe_sid], expires_in_sec=SESSION_TTL_SECONDS
		)


def recall(frappe_sid: str) -> dict | None:
	return frappe.cache.get_value(f"compass_sso:session:{frappe_sid}")


def forget(frappe_sid: str) -> None:
	frappe.cache.delete_value(f"compass_sso:session:{frappe_sid}")


def frappe_sessions_of(keycloak_sid: str) -> list[str]:
	return frappe.cache.get_value(f"compass_sso:keycloak:{keycloak_sid}") or []


def claim_jti(jti: str) -> bool:
	"""True the first time a logout token id is seen, False on every reuse (replay)."""
	return bool(frappe.cache.set(frappe.cache.make_key(f"compass_sso:jti:{jti}"), 1, nx=True, ex=SESSION_TTL_SECONDS))
