# compass_sso

A [Frappe](https://frappeframework.com) app that ties Frappe sites to a [Keycloak](https://www.keycloak.org) realm as the only way to sign in. It is part of [COMPASS](https://github.com/libertalia-eu/COMPASS), a self-hosted stack of Keycloak, Nextcloud and Frappe apps (CRM, Helpdesk, Raven), but it has no dependency on the other COMPASS parts except for the optional Nextcloud features.

Frappe's built-in Social Login handles the sign-in. This app adds what it lacks for a single-sign-on setup:

- **Single sign-out in both directions.** Signing out of a Frappe app ends the Keycloak session. Ending the Keycloak session (in any app, or in Keycloak itself) ends the Frappe session.
- **Keycloak first.** A guest is sent straight to Keycloak instead of seeing Frappe's login form.
- **Roles from Keycloak.** Frappe roles follow the Keycloak client roles on every sign-in.
- **One overview of the apps** a user may open, including a Nextcloud entry.
- **Nextcloud objects as link cards** in Raven, shown only to users whom Nextcloud itself lets open them.

## Requirements

- Frappe 16 (the overview page replaces `/apps`, which Frappe 16 removed). Python 3.10 or newer.
- A Keycloak realm with a confidential OpenID Connect client for the site.
- A Social Login Key named `keycloak` on the site (see below).
- Redis (any Frappe bench has it). Refresh tokens are kept in the Redis cache only, never in the database.

## Install

```bash
bench get-app https://github.com/libertalia-eu/compass_sso --branch v0.10.0
bench --site <site> install-app compass_sso
```

Use the latest release tag. The app has no dependencies besides Frappe.

## Configure

#### Social Login Key

Create a Social Login Key whose document name is `keycloak` and enable it:

| Field | Value |
|---|---|
| Social Login Provider | Custom, with "Custom Base URL" on |
| Provider Name | `Keycloak` |
| Base URL | `https://<keycloak host>` |
| Authorize URL | `/realms/<realm>/protocol/openid-connect/auth` |
| Access Token URL | `/realms/<realm>/protocol/openid-connect/token` |
| Redirect URL | `/api/method/compass_sso.callback.keycloak_login` |
| API Endpoint | `/realms/<realm>/protocol/openid-connect/userinfo` |
| Auth URL Data | `{"response_type": "code", "scope": "openid email profile"}` |
| User ID Property | `preferred_username` |
| Client ID / Secret | from the Keycloak client |

The realm URL is derived from Base URL plus the part of Authorize URL before `/protocol/`. Without an enabled key the app does nothing. A working example of the whole setup is `dev/frappe/setup-sites.sh` in the COMPASS repository.

#### Keycloak client

- Valid redirect URI: `https://<site>/api/method/compass_sso.callback.keycloak_login`.
- Back-channel logout URL: `https://<site>/api/method/compass_sso.api.backchannel_logout`, with "Back-channel logout session required" on.
- A protocol mapper "User Client Role" without a client id, claim `resource_access.${client_id}.roles`, added to the id token. It carries the client roles of all apps on the site into one sign-in. A client per site with a flat `roles` claim still works.

#### Environment

| Variable | Effect |
|---|---|
| `COMPASS_NEXTCLOUD_URL` | Base URL of Nextcloud. Enables the Nextcloud entry in the apps menus and the Nextcloud link cards. Unset: no Nextcloud features. |

## How it works

| Module | What it does |
|---|---|
| `callback.keycloak_login` | Sign-in callback of the Social Login Key. Stores the refresh token per Frappe session in the Redis cache and calls Frappe's `login_oauth_user`. |
| `api.logout` | Replaces Frappe's `logout`: ends the Keycloak session, then the Frappe session. |
| `session.check_keycloak_session` | `before_request` hook. At most every 30 seconds per session it uses the refresh token. If Keycloak refuses it, or cannot be reached, the Frappe session ends. |
| `api.backchannel_logout` | POST endpoint for OIDC Back-Channel Logout 1.0. `logout_token.py` checks signature (RS256 via the realm's JWKS), issuer, audience, event, `sid`, that there is no `nonce`, and that each `jti` is used once. |
| `login_redirect` | A guest who opens `/login`, the site root, the app overview or the route of an app on the site is sent to Keycloak. The requested page is kept as the OAuth state. |
| `roles.sync_roles` | Maps Keycloak client roles to Frappe roles on every sign-in and removes a Frappe role when the Keycloak role is gone. Roles outside the table stay. The table never names `System Manager` or `Script Manager`. |
| `apps_screen`, `www/start` | A Desk entry (only for system users), a Nextcloud entry (only with the role `Nextcloud Nutzer`) and the overview page `/start`. |
| `nextcloud` | Searches Nextcloud with the user's own Keycloak access token and stores the picked object as a `Nextcloud Reference` for Raven. Providers that return settings or objects without a permission check are hidden. |

#### Role mapping

The table `ROLES` in `compass_sso/roles.py` is the only mapping. The Keycloak role names are German, as in COMPASS.

| Keycloak client | Keycloak role | Frappe role |
|---|---|---|
| `crm` | `CRM Nutzer` / `CRM Admin` | `Sales User` / `Sales Manager` |
| `helpdesk` | `Helpdesk Nutzer` / `Helpdesk Admin` | `Agent` / `Agent Manager` |
| `raven` | `Raven Nutzer` / `Raven Admin` | `Raven User` / `Raven Admin` |
| `nextcloud` | `Nextcloud Nutzer` | `Nextcloud Nutzer` |
| `compass-admin` | `Company Admin` | `Company Admin` (the only role the table creates with Desk access) |

To use other roles, edit the table.

## Limits

- The app relies on `frappe.utils.oauth.login_oauth_user` and `get_redirect_uri`, which Frappe does not document as public API. Re-test after every Frappe update.
- It assumes one Keycloak realm per site and a Social Login Key named `keycloak`.
- Role names and some UI texts are German, tied to COMPASS.

## Development

```bash
./run-tests.sh                                  # needs PyJWT and cryptography
IMAGE=<frappe image> ./run-tests.sh             # or inside a Frappe image
```

The unit tests need no bench. The version lives in `compass_sso/__init__.py`; raise it with each release and tag `v<version>`.

## Contributing and security

Contributions are welcome under the DCO, see [CONTRIBUTING.md](CONTRIBUTING.md). Report security issues privately through the repository's "Report a vulnerability" page (GitHub Security tab), not as a public issue.

## Licence

AGPL-3.0-or-later, see [LICENSE](LICENSE). If you change the app and let others use it over a network, you must offer them the source of your version.
