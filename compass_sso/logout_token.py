"""Check of a back-channel logout token (OIDC Back-Channel Logout 1.0, section 2.6). Pure logic, no Frappe."""
from collections.abc import Callable

import jwt

BACKCHANNEL_LOGOUT_EVENT = "http://schemas.openid.net/event/backchannel-logout"
REQUIRED_CLAIMS = ["iss", "aud", "iat", "jti", "events"]


class LogoutTokenRefused(Exception):
	"""The token is not a valid logout token from our Keycloak realm."""


def verify_logout_token(
	logout_token: str,
	jwks: dict,
	issuer: str,
	audience: str,
	is_first_use_of: Callable[[str], bool],
) -> dict:
	"""Return the claims of a valid logout token, else raise LogoutTokenRefused.

	jwks: the realm's public keys (JSON Web Key Set). Only RS256 is accepted.
	is_first_use_of: called with the `jti` of an otherwise valid token; must return False if the
	`jti` was seen before (replay) and remember it otherwise.
	"""
	try:
		claims = _decode(logout_token, jwks, issuer, audience)
	except jwt.InvalidTokenError as error:
		raise LogoutTokenRefused(str(error)) from error
	if BACKCHANNEL_LOGOUT_EVENT not in claims["events"]:
		raise LogoutTokenRefused("not a back-channel logout event")
	if "nonce" in claims:
		raise LogoutTokenRefused("nonce must not be present")
	if not claims.get("sid"):
		raise LogoutTokenRefused("sid missing")
	if not is_first_use_of(claims["jti"]):
		raise LogoutTokenRefused("jti used before")
	return claims


def _decode(logout_token: str, jwks: dict, issuer: str, audience: str) -> dict:
	key_id = jwt.get_unverified_header(logout_token).get("kid")
	signing_key = next((k for k in jwt.PyJWKSet.from_dict(jwks).keys if k.key_id == key_id), None)
	if signing_key is None:
		raise jwt.InvalidTokenError("unknown signing key")
	return jwt.decode(
		logout_token, signing_key.key, algorithms=["RS256"], audience=audience, issuer=issuer,
		options={"require": REQUIRED_CLAIMS},
	)
