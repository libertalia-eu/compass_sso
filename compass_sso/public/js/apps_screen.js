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
		frappe.call({
			method: "frappe.apps.get_incomplete_setup_route",
			args: { current_app: localStorage.current_app, app_route: localStorage.current_route },
			callback: (r) => {
				target.location.href = r.message;
			},
			error: () => target.close(), // shortcut: also closes a reused window, when the call fails
		});
	},
	true
);
