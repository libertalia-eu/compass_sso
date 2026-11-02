"""Calls to Keycloak (token endpoint, logout endpoint, signing keys) for the Social Login Key `keycloak`."""
import frappe
import requests

PROVIDER = "keycloak"
TIMEOUT_SECONDS = 5


class KeycloakSessionEnded(Exception):
	"""Keycloak refused the refresh token: the Keycloak session no longer exists."""


def _key():
	return frappe.get_doc("Social Login Key", PROVIDER)


def realm_url(key=None) -> str:
	key = key or _key()
	# base_url + the part of the authorize URL before /protocol: https://auth.../realms/libertalia
	return key.base_url.rstrip("/") + key.authorize_url.split("/protocol/")[0]


def _client_credentials(key) -> dict:
	return {"client_id": key.client_id, "client_secret": key.get_password("client_secret")}


def exchange_code(code: str, redirect_uri: str) -> dict:
	key = _key()
	response = requests.post(
		realm_url(key) + "/protocol/openid-connect/token",
		data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
		| _client_credentials(key),
		timeout=TIMEOUT_SECONDS,
	)
	response.raise_for_status()
	return response.json()


def refresh(refresh_token: str) -> dict:
	key = _key()
	response = requests.post(
		realm_url(key) + "/protocol/openid-connect/token",
		data={"grant_type": "refresh_token", "refresh_token": refresh_token} | _client_credentials(key),
		timeout=TIMEOUT_SECONDS,
	)
	if response.status_code == 400 and response.json().get("error") == "invalid_grant":
		raise KeycloakSessionEnded
	response.raise_for_status()
	return response.json()


def end_session(refresh_token: str) -> None:
	key = _key()
	requests.post(
		realm_url(key) + "/protocol/openid-connect/logout",
		data={"refresh_token": refresh_token} | _client_credentials(key),
		timeout=TIMEOUT_SECONDS,
	).raise_for_status()


SIGNING_KEYS_TTL_SECONDS = 600


def signing_keys() -> dict:
	"""Keycloak's public keys (JWKS), cached so that forged calls do not each cost a request to Keycloak."""
	key = _key()
	cache_key = "compass_sso:signing_keys"
	keys = frappe.cache.get_value(cache_key)
	if keys is None:
		response = requests.get(realm_url(key) + "/protocol/openid-connect/certs", timeout=TIMEOUT_SECONDS)
		response.raise_for_status()
		keys = response.json()
		frappe.cache.set_value(cache_key, keys, expires_in_sec=SIGNING_KEYS_TTL_SECONDS)
	return keys
