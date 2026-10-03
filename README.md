# NetScope

NetScope is a Windows desktop network information and diagnostics utility built with Python and PySide6. It presents selected system and network details in a simple dashboard and runs lightweight connectivity checks when the application starts or when you refresh it.

## V1 features

- **System information:** computer name, Windows version, and current username.
- **Network adapter information:** selects an active adapter, preferring one with a default gateway. Displays the adapter name, IPv4 and IPv6 addresses when available, MAC address, default gateway, configured DNS servers, and DHCP status.
- **Connectivity:** separately reports Internet, gateway, and DNS results. Gateway reachability is checked with one ping. DNS connectivity is checked by resolving `example.com` through the system resolver. Internet connectivity is checked with the HTTPS public-IP lookup. Latency is shown where a check completes successfully.
- **Public IP:** displays the response from `https://api.ipify.org` when available.
- **Refresh:** re-reads system and network details and repeats the checks in a background thread, keeping the window responsive.
- **Copy All:** copies the currently displayed report as plain text to the clipboard.
- **Dark, resizable interface:** information is grouped into clearly labeled cards.

Checks run on startup and on demand; NetScope does not continuously ping or poll the network.

## Privacy and security

NetScope reads local system and adapter information using Python and Windows' built-in networking tools. Adapter details are not sent to the public-IP service. The public-IP lookup makes an HTTPS request to ipify and displays its response. The DNS check asks the configured system resolver to resolve `example.com`. Gateway checking sends one ICMP echo request to the configured default gateway. These checks do not scan the LAN, enumerate other devices, scan ports, capture packets, change Windows settings, or require administrator privileges for normal use. Network details are only copied externally if you choose to copy or share the report yourself.

## Requirements

- Windows 10 or later
- Python 3.10 or later
- PySide6, pinned in `requirements.txt`

## Installation

From the project directory, create and activate a virtual environment, then install the runtime dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

With the virtual environment active:

```powershell
python app.py
```

Public IP lookup requires Internet access. If the public-IP endpoint is unreachable, NetScope displays `Unavailable`; local system and adapter information can still be shown. A firewall may block the gateway's ICMP response even when the network is otherwise working.

## Project structure

```text
NetScope/
├── app.py                 # Application entry point
├── netscope/
│   ├── __init__.py
│   ├── gui.py              # PySide6 dashboard and controls
│   ├── network.py          # Windows information and connectivity helpers
│   └── workers.py          # Background refresh thread
├── tests/
│   └── test_network.py     # Offline parsing and adapter-selection tests
├── requirements.txt
├── .gitignore
└── README.md
```

## Current limitations

- Adapter detection uses `Get-NetIPConfiguration` when available and falls back to parsing `ipconfig /all`. The fallback recognizes the standard English Windows labels, so localized Windows output may result in some values being unavailable.
- The dashboard displays the selected adapter, rather than a full inventory of every interface.
- Internet status depends on reaching the ipify HTTPS endpoint. A failure can mean that endpoint is blocked or unavailable, even if another Internet service works.
- Gateway reachability depends on an ICMP reply, which some networks or firewalls block.
- No executable installer is included.

## Roadmap

Potential future additions, outside the current V1 scope:

- On-demand Ping tool
- DNS Lookup tool
- Traceroute tool

These tools are not part of the current release.

## Screenshot

_Screenshot to be added._

## NetScope Web

NetScope also includes a separate static browser application in [`web/`](web/). The web version runs in a browser with HTML, CSS, and JavaScript and does not replace or require the Windows desktop application. See [web/README.md](web/README.md) for features, privacy details, local preview, and GitHub Pages deployment. The hosted site will be available at <https://bootbeat.github.io/NetScope/> after deployment.

## License

License: TBD.
