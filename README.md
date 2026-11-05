# compass_sso

Frappe app for COMPASS: signing out of a Frappe app ends the Keycloak session, and ends of the Keycloak session end the Frappe session.

- `callback.keycloak_login`: sign-in callback of the Social Login Key `keycloak`; keeps the refresh token per Frappe session in the Redis cache (never the database).
- `api.logout`: replaces `logout` (`override_whitelisted_methods`): ends the Keycloak session, then Frappe's.
- `session.check_keycloak_session`: `before_request`, at most every 30 s per session a refresh-token call; refused, or Keycloak unreachable, means the Frappe session ends.
- `login_redirect.redirect_guest_to_keycloak`: `before_request`, a guest who opens `/login`, the site root, the app switcher `/apps` or the route of an app on the site (the `add_to_apps_screen` hooks; GET) is sent straight to Keycloak; the page asked for is kept as the OAuth state. Does nothing without an enabled Social Login Key `keycloak`.
- `roles.sync_admin_role`: on every sign-in the admin role of the app follows the Keycloak client roles in the id token, for every app of the site in one sign-in: `CRM Admin` gives `Sales Manager`, `Helpdesk Admin` gives `Agent Manager`, `Raven Admin` gives `Raven Admin`; without the Keycloak role the Frappe role is taken away. The table `ADMIN_ROLES` is the only mapping and never names `System Manager` or `Script Manager`. One Keycloak client for the site needs a mapper ("User Client Role" without a client id, claim `resource_access.${client_id}.roles`) that puts the client roles of all apps into the id token. The older shape still works: a client per site with the claim `roles`.
- `api.backchannel_logout`: POST endpoint for OIDC Back-Channel Logout 1.0. `logout_token.py` checks signature (RS256 via the realm's JWKS), issuer, audience, event, `sid`, no `nonce`, and each `jti` once.

Needs a Social Login Key named `keycloak` (see COMPASS `dev/frappe/setup-sites.sh`) and the Keycloak client with `backchannel.logout.url` = `https://<site>/api/method/compass_sso.api.backchannel_logout` and `backchannel.logout.session.required`.
Relies on `frappe.utils.oauth.login_oauth_user` and `get_redirect_uri` (not publicly documented): re-test after Frappe updates.

Tests: `./run-tests.sh` (or `IMAGE=<frappe image> ./run-tests.sh`). Licence: MIT.
