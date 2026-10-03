# NetScope Web

NetScope Web is a no-build, browser-based companion to the Windows desktop application. It uses plain HTML, CSS, and JavaScript and can be hosted as a static website. It has no Python backend, build step, account, or installation requirement for visitors.

## Features

- Reports the browser's online hint and checks HTTPS reachability with the public-IP request.
- Measures approximate HTTP round-trip time for that HTTPS request. This is not ICMP ping latency.
- Shows browser, exposed platform, screen resolution, language, time zone, and connection type only when the browser exposes a recognized type.
- Displays public IP from ipify over HTTPS.
- Looks up A and AAAA records with Google Public DNS JSON DNS-over-HTTPS.
- Copies the information currently displayed as plain text.
- Responsive dark dashboard for desktop and mobile screens.

The IP-information card shows `Not available` for country, region, city, and organization because the selected IP service returns the public address only. NetScope does not send that address to a second geolocation service.

## What the browser can and cannot show

Browsers expose a limited set of browser and display values. The Network Information API is not available in every browser, so connection type may show `Not available in browser`. A web page cannot normally read the visitor's MAC address, default gateway, configured local DNS servers, DHCP settings, or complete adapter details. NetScope does not fabricate or try to bypass those restrictions.

## Privacy

The page runs in the browser and has no application backend, analytics, accounts, or local storage. The public-IP request is sent to ipify; like any network service, ipify receives the request and its source IP. The DNS Lookup feature sends the entered domain and query type to Google Public DNS over HTTPS. NetScope does not make claims about these providers' request retention; review their policies before use. No geolocation permission or precise location is requested, and no LAN scanning is performed.

Browser metadata remains in the page and in a Copy All report only if you choose to copy it. The app does not persist the report.

## Run locally

For local testing, serve this folder from a static HTTP server. For example, with Python installed:

```powershell
cd web
python -m http.server 8000
```

Then open <http://localhost:8000>. Python is only used here as a convenient local static-file server; it is not part of the application and is not needed for deployment. Clipboard access is available on secure contexts such as HTTPS and localhost.

## Deploy to GitHub Pages

The web app lives in `web/`. The workflow at `.github/workflows/pages.yml` uploads only `./web` as the Pages artifact, so the deployed site has `index.html`, `styles.css`, `app.js`, and `assets/` at its root. The Windows desktop application is not included in the Pages artifact.

In the repository's **Settings → Pages**, select **GitHub Actions** as the build and deployment source if it is not already selected. After the workflow is on GitHub, pushes to `main` deploy the site automatically. You can also start a deployment manually from the repository's **Actions** tab by selecting the Pages workflow and choosing **Run workflow**.

The public site URL is <https://bootbeat.github.io/NetScope/>. The site is static and requires no build step or server-side runtime.

## Browser compatibility

The app uses standard HTML, CSS Grid, Fetch, AbortController, URL, and Clipboard APIs with a fallback for clipboard access. Current versions of Chrome, Edge, Firefox, and Safari are expected to support the core dashboard. Connection-type reporting varies by browser. HTTPS hosting is recommended and required by browsers for some APIs.

## Limitations

- External service or CORS failure can prevent public-IP or DNS lookup; the dashboard reports an unavailable result and remains usable.
- `navigator.onLine` is only the browser's connectivity hint. The HTTPS request is used as a reachability check; a blocked service may show the check as unavailable rather than proving the whole Internet is offline.
- The latency number measures the public-IP HTTPS request, including request/response overhead, and is not a general route or ICMP measurement.
- DNS Lookup uses Google Public DNS, not the visitor's configured resolver. It resolves public A and AAAA answers only.
- Country, region, city, and organization are intentionally unavailable because no geolocation provider is contacted.
- The page cannot expose protected local adapter information to JavaScript.

## Future improvements

Possible future work includes optional user-selected DoH providers, more DNS record types, and accessibility refinements based on user feedback. Intrusive scanning features are out of scope.
