app_name = "compass_sso"
app_title = "Compass SSO"
app_publisher = "COMPASS"
app_description = "Keycloak logout and session follow-up"
app_license = "MIT"

import os

from compass_sso.apps_screen import nextcloud_entry

# Documented hooks only: the one logout endpoint all UIs call, and two checks per request.
override_whitelisted_methods = {"logout": "compass_sso.api.logout"}
before_request = [
	"compass_sso.login_redirect.redirect_guest_to_keycloak",
	"compass_sso.session.check_keycloak_session",
]

# Nextcloud is no Frappe app, so it enters the app overview and the apps menus of Helpdesk and CRM through this app.
add_to_apps_screen = nextcloud_entry(os.environ.get("COMPASS_NEXTCLOUD_URL"))

# The app overview opens the apps in a new window (REQ-039).
web_include_js = "/assets/compass_sso/js/apps_screen.js"
