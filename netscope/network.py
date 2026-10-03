"""Local Windows system and network information helpers."""

from __future__ import annotations

import json
import os
import platform
import re
import socket
import subprocess
import time
import urllib.request
from typing import Any


NOT_AVAILABLE = "Not available"


def _run_powershell(script: str) -> str:
    """Run a read-only PowerShell query and return stdout, or an empty string."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def get_system_information() -> dict[str, str]:
    """Return computer name, Windows version, and current account name."""
    version = platform.platform()
    if os.name == "nt":
        value = _run_powershell("(Get-CimInstance Win32_OperatingSystem).Caption")
        if value:
            version = value
    return {
        "computer_name": socket.gethostname() or NOT_AVAILABLE,
        "windows_version": version or NOT_AVAILABLE,
        "username": os.environ.get("USERNAME") or os.environ.get("USER") or NOT_AVAILABLE,
    }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)] if value != "" else []


def parse_adapter_data(data: Any) -> dict[str, str]:
    """Choose the best active adapter from Get-NetIPConfiguration JSON."""
    adapters = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
    candidates = []
    for item in adapters:
        if not isinstance(item, dict):
            continue
        ipv4 = _as_list(item.get("IPv4"))
        ipv6 = _as_list(item.get("IPv6"))
        gateways = _as_list(item.get("Gateway"))
        # Configuration output contains active interfaces; prefer routed ones,
        # then interfaces with a usable address. Loopback/link-local are lower priority.
        score = (100 if gateways else 0) + (20 if ipv4 else 0) + (5 if ipv6 else 0)
        if ipv4 and ipv4[0].startswith("169.254."):
            score -= 15
        candidates.append((score, item, ipv4, ipv6, gateways))
    if not candidates:
        return {key: NOT_AVAILABLE for key in ("adapter", "ipv4", "ipv6", "mac", "gateway", "dns", "dhcp")}
    _, item, ipv4, ipv6, gateways = max(candidates, key=lambda entry: entry[0])
    dns = _as_list(item.get("DNS"))
    dhcp = item.get("DHCP")
    if isinstance(dhcp, bool):
        dhcp_value = "Enabled" if dhcp else "Disabled"
    elif dhcp is None or str(dhcp).strip() == "":
        dhcp_value = NOT_AVAILABLE
    else:
        dhcp_value = str(dhcp)
    return {
        "adapter": str(item.get("Name") or NOT_AVAILABLE),
        "ipv4": ", ".join(ipv4) or NOT_AVAILABLE,
        "ipv6": ", ".join(ipv6) or NOT_AVAILABLE,
        "mac": str(item.get("MAC") or NOT_AVAILABLE),
        "gateway": ", ".join(gateways) or NOT_AVAILABLE,
        "dns": ", ".join(dns) or NOT_AVAILABLE,
        "dhcp": dhcp_value,
    }


def parse_ipconfig_output(output: str) -> dict[str, str]:
    """Extract the active adapter from `ipconfig /all` output."""
    sections: list[tuple[str, dict[str, list[str]]]] = []
    current_name: str | None = None
    current: dict[str, list[str]] = {}
    previous_key = ""
    for line in output.splitlines():
        header = re.match(r"^\s*(?:.+? adapter|Unknown adapter)\s+(.+):\s*$", line, re.IGNORECASE)
        if header:
            if current_name is not None:
                sections.append((current_name, current))
            current_name, current, previous_key = header.group(1).strip(), {}, ""
            continue
        if current_name is None:
            continue
        prop = re.match(r"^\s*(.*?)\s*\.\s*:\s*(.*?)\s*$", line)
        if prop:
            label = re.sub(r"[.\s]", "", prop.group(1)).casefold()
            value = prop.group(2).strip()
            if "description" in label:
                key = "description"
            elif "physicaladdress" in label:
                key = "mac"
            elif "dhcpenabled" in label:
                key = "dhcp"
            elif "ipv4address" in label or label == "ipaddress":
                key = "ipv4"
            elif "ipv6address" in label:
                key = "ipv6"
            elif "defaultgateway" in label:
                key = "gateway"
            elif "dnsservers" in label:
                key = "dns"
            elif "mediastate" in label:
                key = "media"
            else:
                key = "other"
            if key != "other" and value:
                current.setdefault(key, []).append(value)
            previous_key = key
        elif previous_key == "dns" and line.strip():
            current.setdefault("dns", []).append(line.strip())
    if current_name is not None:
        sections.append((current_name, current))

    candidates = []
    for name, values in sections:
        ipv4 = values.get("ipv4", [])
        ipv6 = values.get("ipv6", [])
        gateways = values.get("gateway", [])
        dns = values.get("dns", [])
        # Ignore Windows' disconnected adapters and favor the routed interface.
        if values.get("media") or not (ipv4 or ipv6 or gateways):
            continue
        score = (100 if any(g.strip() for g in gateways) else 0) + (20 if ipv4 else 0) + (5 if ipv6 else 0)
        if ipv4 and ipv4[0].startswith("169.254."):
            score -= 15
        candidates.append((score, name, values, ipv4, ipv6, gateways, dns))
    if not candidates:
        return {key: NOT_AVAILABLE for key in ("adapter", "ipv4", "ipv6", "mac", "gateway", "dns", "dhcp")}
    _, name, values, ipv4, ipv6, gateways, dns = max(candidates, key=lambda item: item[0])

    def clean(items: list[str]) -> list[str]:
        return [re.sub(r"\s*\([^)]*\)\s*$", "", item).strip() for item in items if item.strip()]

    return {
        "adapter": name or values.get("description", [NOT_AVAILABLE])[0],
        "ipv4": ", ".join(clean(ipv4)) or NOT_AVAILABLE,
        "ipv6": ", ".join(clean(ipv6)) or NOT_AVAILABLE,
        "mac": values.get("mac", [NOT_AVAILABLE])[0] or NOT_AVAILABLE,
        "gateway": ", ".join(clean(gateways)) or NOT_AVAILABLE,
        "dns": ", ".join(clean(dns)) or NOT_AVAILABLE,
        "dhcp": ("Enabled" if values.get("dhcp", [""])[0].casefold() == "yes" else "Disabled") if values.get("dhcp") else NOT_AVAILABLE,
    }


def get_network_information() -> dict[str, str]:
    """Read active adapter configuration using Windows' built-in networking cmdlets."""
    empty = {key: NOT_AVAILABLE for key in ("adapter", "ipv4", "ipv6", "mac", "gateway", "dns", "dhcp")}
    if os.name != "nt":
        return empty
    script = (
        "$ErrorActionPreference='Stop'; "
        "Get-NetIPConfiguration | ForEach-Object { $c=$_; "
        "$v4=Get-NetIPInterface -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue; "
        "$v6=Get-NetIPInterface -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv6 -ErrorAction SilentlyContinue; "
        "[pscustomobject]@{Name=$c.InterfaceAlias; MAC=$c.NetAdapter.MacAddress; "
        "IPv4=@($c.IPv4Address | ForEach-Object {$_.IPAddress}); "
        "IPv6=@($c.IPv6Address | ForEach-Object {$_.IPAddress}); "
        "Gateway=@($c.IPv4DefaultGateway | ForEach-Object {$_.NextHop}); "
        "DNS=@($c.DnsServer.ServerAddresses); DHCP=if($v4.Dhcp -eq 'Enabled'){'Enabled'}elseif($v4.Dhcp -eq 'Disabled'){'Disabled'}else{$null}} "
        "} | ConvertTo-Json -Depth 4 -Compress"
    )
    output = _run_powershell(script)
    if output:
        try:
            parsed = parse_adapter_data(json.loads(output))
            if parsed["adapter"] != NOT_AVAILABLE:
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    try:
        result = subprocess.run(
            ["ipconfig.exe", "/all"], capture_output=True, text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False,
        )
        if result.returncode == 0:
            return parse_ipconfig_output(result.stdout)
    except (OSError, subprocess.SubprocessError):
        pass
    return empty


def check_gateway(gateway: str) -> tuple[str, str]:
    """Ping the configured default gateway once, with a short timeout."""
    if not gateway or gateway == NOT_AVAILABLE:
        return "Disconnected", "No gateway"
    try:
        started = time.perf_counter()
        result = subprocess.run(
            ["ping.exe", "-n", "1", "-w", "1200", gateway],
            capture_output=True,
            text=True,
            timeout=2.5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        elapsed = max(1, round((time.perf_counter() - started) * 1000))
        return ("Connected", f"{elapsed} ms") if result.returncode == 0 else ("Disconnected", "Unreachable")
    except (OSError, subprocess.SubprocessError):
        return "Disconnected", "Check unavailable"


def check_dns() -> tuple[str, str]:
    """Resolve a stable public hostname once using the system resolver."""
    started = time.perf_counter()
    try:
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        return "Connected", f"{max(1, round((time.perf_counter() - started) * 1000))} ms"
    except OSError:
        return "Disconnected", "Resolution failed"


def get_public_ip() -> tuple[str, str]:
    """Fetch the public IP over HTTPS; only the response value is retained."""
    started = time.perf_counter()
    try:
        request = urllib.request.Request(
            "https://api.ipify.org", headers={"User-Agent": "NetScope/1.0"}
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            address = response.read(128).decode("ascii", errors="ignore").strip()
        # Validate and display only an IP address, never response metadata.
        import ipaddress

        parsed = ipaddress.ip_address(address)
        return str(parsed), f"{max(1, round((time.perf_counter() - started) * 1000))} ms"
    except Exception:
        return "Unavailable", ""
