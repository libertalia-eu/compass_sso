// The app overview (frappe/www/apps.html) opens every app in the same tab; here it opens in a new window named like the one of the apps menus, so a second click reuses it.
// The window opens inside the click, before the async call, so popup blockers let it through.
document.addEventListener(
	"click",
	(event) => {
		const logo = event.target.closest(".app-name-cls");
		if (!logo || event.target.closest(".set-default")) return;
		event.stopImmediatePropagation();
		const target = window.open("", `compass-${logo.getAttribute("app-name")}`);
		try {
			target.opener = null; // Nextcloud and the other hosts get no handle on this tab
		} catch (e) {
			// a window of another host was opened with the opener cut already
		}
		localStorage.current_app = logo.getAttribute("app-name");
		localStorage.current_route = logo.getAttribute("app-route");
		// GET needs no CSRF token: the token of this tab goes stale as soon as another tab of the site signs in or boots.
		const query = new URLSearchParams({ current_app: localStorage.current_app, app_route: localStorage.current_route });
		fetch(`/api/method/frappe.apps.get_incomplete_setup_route?${query}`, { credentials: "same-origin" })
			.then((response) => (response.ok ? response.json() : Promise.reject(response)))
			.then((body) => body.message)
			.catch(() => localStorage.current_route) // shortcut: skips the setup wizard redirect when the call fails, upgrade when an app needs it
			.then((route) => {
				target.location.href = route;
			});
	},
	true
);
