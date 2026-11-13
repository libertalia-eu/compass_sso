app_name = "compass_sso"
app_title = "Compass SSO"
app_publisher = "COMPASS"
app_description = "Keycloak logout and session follow-up"
app_license = "AGPL-3.0-or-later"

import os

from compass_sso.apps_screen import desk_entry, nextcloud_entry

# Documented hooks only: the one logout endpoint all UIs call, and two checks per request.
override_whitelisted_methods = {"logout": "compass_sso.api.logout"}
before_request = [
	"compass_sso.login_redirect.redirect_apps_to_overview",
	"compass_sso.login_redirect.redirect_guest_to_keycloak",
	"compass_sso.session.check_keycloak_session",
]

# Desk and Nextcloud enter the apps menus of Helpdesk and CRM through this app: Frappe 16 skips its own entry, and Nextcloud is no Frappe app.
add_to_apps_screen = desk_entry() + nextcloud_entry(os.environ.get("COMPASS_NEXTCLOUD_URL"))

# A Nextcloud Reference is readable only for a user whom Nextcloud itself lets open the object (REQ-047).
has_permission = {"Nextcloud Reference": "compass_sso.nextcloud.reference_has_permission"}
raven_document_link_override = "compass_sso.nextcloud.document_link"
