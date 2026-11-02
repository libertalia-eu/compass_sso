"""Unit tests for the back-channel logout token check (REQ-005). No Frappe needed: python -m unittest."""
import json
import time
import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from compass_sso.logout_token import LogoutTokenRefused, verify_logout_token

ISSUER = "https://auth.libertalia.localhost/realms/libertalia"
AUDIENCE = "crm"
EVENT = "http://schemas.openid.net/event/backchannel-logout"


def new_key(key_id: str):
	return rsa.generate_private_key(public_exponent=65537, key_size=2048), key_id


def jwks_of(*keys) -> dict:
	entries = []
	for private_key, key_id in keys:
		entry = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
		entries.append(entry | {"kid": key_id, "use": "sig", "alg": "RS256"})
	return {"keys": entries}


def claims(**changes) -> dict:
	base = {
		"iss": ISSUER, "aud": AUDIENCE, "iat": int(time.time()), "jti": "jti-1",
		"sid": "keycloak-session-1", "events": {EVENT: {}},
	}
	base.update(changes)
	return {name: value for name, value in base.items() if value is not None}


class LogoutTokenTest(unittest.TestCase):
	def setUp(self):
		self.key = new_key("kid-1")
		self.jwks = jwks_of(self.key)
		self.seen = set()

	def sign(self, payload: dict, key=None) -> str:
		private_key, key_id = key or self.key
		return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": key_id})

	def verify(self, token: str) -> dict:
		def first_use(jti: str) -> bool:
			new = jti not in self.seen
			self.seen.add(jti)
			return new
		return verify_logout_token(token, self.jwks, ISSUER, AUDIENCE, first_use)

	def test_accepts_a_valid_token(self):
		self.assertEqual(self.verify(self.sign(claims()))["sid"], "keycloak-session-1")

	def test_refuses_a_reused_jti(self):  # REQ-005
		token = self.sign(claims())
		self.verify(token)
		with self.assertRaisesRegex(LogoutTokenRefused, "jti"):
			self.verify(token)

	def test_refuses_what_is_no_token(self):
		for garbage in ("", "garbage", "a.b.c"):
			with self.assertRaises(LogoutTokenRefused, msg=garbage):
				self.verify(garbage)

	def test_refuses_a_foreign_signing_key_with_a_known_kid(self):
		with self.assertRaises(LogoutTokenRefused):
			self.verify(self.sign(claims(), key=new_key("kid-1")))

	def test_refuses_an_unknown_kid(self):
		with self.assertRaisesRegex(LogoutTokenRefused, "signing key"):
			self.verify(self.sign(claims(), key=new_key("other")))

	def test_refuses_alg_none(self):
		token = jwt.encode(claims(), None, algorithm="none", headers={"kid": "kid-1"})
		with self.assertRaises(LogoutTokenRefused):
			self.verify(token)

	def test_refuses_hs256(self):
		token = jwt.encode(claims(), "x" * 32, algorithm="HS256", headers={"kid": "kid-1"})
		with self.assertRaises(LogoutTokenRefused):
			self.verify(token)

	def test_refuses_wrong_issuer_and_audience(self):
		for changes in ({"iss": "https://evil.example/realms/libertalia"}, {"aud": "helpdesk"}):
			with self.assertRaises(LogoutTokenRefused, msg=str(changes)):
				self.verify(self.sign(claims(**changes)))

	def test_refuses_missing_required_claims(self):
		for name in ("iss", "aud", "iat", "jti", "events", "sid"):
			with self.assertRaises(LogoutTokenRefused, msg=name):
				self.verify(self.sign(claims(**{name: None})))

	def test_refuses_another_event(self):
		with self.assertRaisesRegex(LogoutTokenRefused, "event"):
			self.verify(self.sign(claims(events={"http://example/other": {}})))

	def test_refuses_a_nonce(self):
		with self.assertRaisesRegex(LogoutTokenRefused, "nonce"):
			self.verify(self.sign(claims(nonce="n")))

	def test_a_refused_token_does_not_use_up_its_jti(self):
		with self.assertRaises(LogoutTokenRefused):
			self.verify(self.sign(claims(jti="jti-2", nonce="n")))
		self.assertEqual(self.verify(self.sign(claims(jti="jti-2")))["jti"], "jti-2")


if __name__ == "__main__":
	unittest.main()
