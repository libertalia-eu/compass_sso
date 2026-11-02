app_name = "compass_sso"
app_title = "Compass SSO"
app_publisher = "COMPASS"
app_description = "Keycloak logout and session follow-up"
app_license = "MIT"

# Documented hooks only: the one logout endpoint all UIs call, and a check per request.
override_whitelisted_methods = {"logout": "compass_sso.api.logout"}
before_request = ["compass_sso.session.check_keycloak_session"]
