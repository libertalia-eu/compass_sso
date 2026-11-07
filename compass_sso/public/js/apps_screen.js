// The app overview (frappe/www/apps.html) opens every app in the same tab; here it opens in a new window.
// The window opens inside the click, before the async call, so popup blockers let it through.
document.addEventListener(
	"click",
	(event) => {
		const logo = event.target.closest(".app-name-cls");
		if (!logo || event.target.closest(".set-default")) return;
		event.stopImmediatePropagation();
		const target = window.open("", "_blank");
		target.opener = null; // Nextcloud and the other hosts get no handle on this tab
		localStorage.current_app = logo.getAttribute("app-name");
		localStorage.current_route = logo.getAttribute("app-route");
		frappe.call({
			method: "frappe.apps.get_incomplete_setup_route",
			args: { current_app: localStorage.current_app, app_route: localStorage.current_route },
			callback: (r) => {
				target.location.href = r.message;
			},
			error: () => target.close(),
		});
	},
	true
);
