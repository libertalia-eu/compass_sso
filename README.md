# compass_sso

Frappe app for COMPASS: signing out of a Frappe app ends the Keycloak session, and ends of the Keycloak session end the Frappe session.

- `callback.keycloak_login`: sign-in callback of the Social Login Key `keycloak`; keeps the refresh token per Frappe session in the Redis cache (never the database).
- `api.logout`: replaces `logout` (`override_whitelisted_methods`): ends the Keycloak session, then Frappe's.
- `session.check_keycloak_session`: `before_request`, at most every 30 s per session a refresh-token call; refused, or Keycloak unreachable, means the Frappe session ends.
- `login_redirect.redirect_guest_to_keycloak`: `before_request`, a guest who opens `/login` or the app route (the home page of the site; GET) is sent straight to Keycloak; the page asked for is kept as the OAuth state. Does nothing without an enabled Social Login Key `keycloak`.
- `api.backchannel_logout`: POST endpoint for OIDC Back-Channel Logout 1.0. `logout_token.py` checks signature (RS256 via the realm's JWKS), issuer, audience, event, `sid`, no `nonce`, and each `jti` once.

Needs a Social Login Key named `keycloak` (see COMPASS `dev/frappe/setup-sites.sh`) and the Keycloak client with `backchannel.logout.url` = `https://<site>/api/method/compass_sso.api.backchannel_logout` and `backchannel.logout.session.required`.
Relies on `frappe.utils.oauth.login_oauth_user` and `get_redirect_uri` (not publicly documented): re-test after Frappe updates.

Tests: `./run-tests.sh` (or `IMAGE=<frappe image> ./run-tests.sh`). Licence: MIT.
