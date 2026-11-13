# compass_sso

Frappe app for COMPASS: signing out of a Frappe app ends the Keycloak session, and ends of the Keycloak session end the Frappe session.

- `callback.keycloak_login`: sign-in callback of the Social Login Key `keycloak`; keeps the refresh token per Frappe session in the Redis cache (never the database).
- `api.logout`: replaces `logout` (`override_whitelisted_methods`): ends the Keycloak session, then Frappe's.
- `session.check_keycloak_session`: `before_request`, at most every 30 s per session a refresh-token call; refused, or Keycloak unreachable, means the Frappe session ends.
- `login_redirect.redirect_guest_to_keycloak`: `before_request`, a guest who opens `/login`, the site root, the app switcher `/apps` or the route of an app on the site (the `add_to_apps_screen` hooks; GET) is sent straight to Keycloak; the page asked for is kept as the OAuth state. Does nothing without an enabled Social Login Key `keycloak`.
- `roles.sync_roles`: on every sign-in the Frappe roles follow the Keycloak client roles in the id token, for every app of the site in one sign-in. The table `ROLES` is the only mapping: `CRM Nutzer` gives `Sales User`, `CRM Admin` gives `Sales Manager`; `Helpdesk Nutzer` gives `Agent`, `Helpdesk Admin` gives `Agent Manager`; `Raven Nutzer` gives `Raven User`, `Raven Admin` gives `Raven Admin`; `Nextcloud Nutzer` gives the Frappe role `Nextcloud Nutzer` (no Frappe app: the Nextcloud entry of the apps menu asks for it, `apps_screen.has_nextcloud_access`); `Company Admin` (client `compass-admin`) gives the Frappe role `Company Admin`, the only role the table creates with Desk access. Without the Keycloak role the Frappe role is taken away; roles that are not in the table stay. The table never names `System Manager` or `Script Manager`. One Keycloak client for the site needs a mapper ("User Client Role" without a client id, claim `resource_access.${client_id}.roles`) that puts the client roles of all apps into the id token. The older shape still works: a client per site with the claim `roles`.
- `api.backchannel_logout`: POST endpoint for OIDC Back-Channel Logout 1.0. `logout_token.py` checks signature (RS256 via the realm's JWKS), issuer, audience, event, `sid`, no `nonce`, and each `jti` once.

Needs a Social Login Key named `keycloak` (see COMPASS `dev/frappe/setup-sites.sh`) and the Keycloak client with `backchannel.logout.url` = `https://<site>/api/method/compass_sso.api.backchannel_logout` and `backchannel.logout.session.required`.
Relies on `frappe.utils.oauth.login_oauth_user` and `get_redirect_uri` (not publicly documented): re-test after Frappe updates.

Tests: `./run-tests.sh` (or `IMAGE=<frappe image> ./run-tests.sh`). Licence: AGPL-3.0-or-later (see `LICENSE`).
