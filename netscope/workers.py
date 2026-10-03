"""Background refresh worker for network and public-IP checks."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .network import (
    check_dns,
    check_gateway,
    get_network_information,
    get_public_ip,
    get_system_information,
)


class RefreshWorker(QThread):
    """Collect one dashboard snapshot without blocking the GUI thread."""

    finished_data = Signal(dict)

    def run(self) -> None:
        try:
            network = get_network_information()
            gateway_status, gateway_latency = check_gateway(network.get("gateway", ""))
            dns_status, dns_latency = check_dns()
            public_ip, internet_latency = get_public_ip()
            self.finished_data.emit({
                "system": get_system_information(),
                "network": network,
                "gateway_status": gateway_status,
                "gateway_latency": gateway_latency,
                "dns_status": dns_status,
                "dns_latency": dns_latency,
                "internet_status": "Connected" if public_ip != "Unavailable" else "Disconnected",
                "internet_latency": internet_latency or "Unavailable",
                "public_ip": public_ip,
            })
        except Exception as exc:  # A failed data source should never take down the window.
            self.finished_data.emit({"error": str(exc)})
