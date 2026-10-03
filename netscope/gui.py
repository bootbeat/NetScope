"""NetScope PySide6 user interface."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from .network import NOT_AVAILABLE
from .workers import RefreshWorker


class InfoCard(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 17, 20, 18)
        self.layout.setSpacing(12)
        heading = QLabel(title.upper())
        heading.setObjectName("cardHeading")
        self.layout.addWidget(heading)

    def add_row(self, name: str, value: str = "Checking...") -> QLabel:
        row = QHBoxLayout()
        key = QLabel(name)
        key.setObjectName("fieldName")
        val = QLabel(value)
        val.setObjectName("fieldValue")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val.setWordWrap(True)
        val.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(key, 1)
        row.addWidget(val, 2)
        self.layout.addLayout(row)
        return val


class NetScopeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetScope")
        self.resize(900, 760)
        self.setMinimumSize(680, 600)
        self.worker: RefreshWorker | None = None
        self._build_ui()
        self._set_theme()
        self.refresh_data()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("NetScope")
        title.setObjectName("appTitle")
        subtitle = QLabel("Windows Network Information & Diagnostics")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        outer.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        self.system_card = InfoCard("System Information")
        self.system_values = {
            "Computer Name": self.system_card.add_row("Computer Name"),
            "Windows Version": self.system_card.add_row("Windows Version"),
            "Username": self.system_card.add_row("Username"),
        }
        self.network_card = InfoCard("Network Information")
        self.network_values = {
            label: self.network_card.add_row(label)
            for label in ("Adapter", "IPv4 Address", "IPv6 Address", "MAC Address", "Default Gateway", "DNS Servers", "DHCP")
        }
        self.connectivity_card = InfoCard("Connectivity")
        self.connectivity_values = {
            label: self.connectivity_card.add_row(label, "🟡 Checking")
            for label in ("Internet", "Gateway", "DNS")
        }
        self.public_card = InfoCard("Public IP")
        self.public_ip_value = self.public_card.add_row("Address", "Checking...")

        grid.addWidget(self.system_card, 0, 0)
        grid.addWidget(self.network_card, 0, 1, 2, 1)
        grid.addWidget(self.connectivity_card, 1, 0)
        grid.addWidget(self.public_card, 2, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        controls = QHBoxLayout()
        self.update_label = QLabel("Ready")
        self.update_label.setObjectName("updateLabel")
        controls.addWidget(self.update_label)
        controls.addStretch()
        self.copy_button = QPushButton("📋  Copy All")
        self.copy_button.setObjectName("secondaryButton")
        self.copy_button.clicked.connect(self.copy_all)
        self.refresh_button = QPushButton("🔄  Refresh")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(self.refresh_data)
        controls.addWidget(self.copy_button)
        controls.addWidget(self.refresh_button)
        outer.addLayout(controls)
        self.setCentralWidget(root)

    def _set_theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #11151c; color: #e7edf6; font-family: 'Segoe UI'; font-size: 10pt; }
            QScrollArea, QScrollArea QWidget { background: transparent; }
            #appTitle { font-size: 25pt; font-weight: 700; color: #f5f8ff; }
            #subtitle { color: #98a6b8; font-size: 10pt; }
            #card { background: #191f29; border: 1px solid #2b3544; border-radius: 13px; }
            #cardHeading { color: #85b8ff; font-size: 9pt; font-weight: 700; letter-spacing: 1px; }
            #fieldName { color: #9eabbb; }
            #fieldValue { color: #edf2fa; font-weight: 500; }
            #updateLabel { color: #9eabbb; }
            QPushButton { border-radius: 9px; padding: 10px 16px; font-weight: 600; }
            #primaryButton { background: #3478d4; color: white; border: 1px solid #4a8ce7; }
            #primaryButton:hover { background: #4388e4; }
            #secondaryButton { background: #202936; color: #e7edf6; border: 1px solid #354255; }
            #secondaryButton:hover { background: #293647; }
            QPushButton:disabled { color: #8e9aaa; background: #252c36; }
        """)

    def refresh_data(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        self.update_label.setText("Updating...")
        self.refresh_button.setEnabled(False)
        for value in self.connectivity_values.values():
            value.setText("🟡 Checking")
        self.worker = RefreshWorker(self)
        self.worker.finished_data.connect(self._apply_snapshot)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _apply_snapshot(self, data: dict) -> None:
        if data.get("error"):
            self.update_label.setText("Update incomplete")
            return
        for label, key in (("Computer Name", "computer_name"), ("Windows Version", "windows_version"), ("Username", "username")):
            self.system_values[label].setText(data["system"].get(key) or NOT_AVAILABLE)
        network_labels = {
            "Adapter": "adapter", "IPv4 Address": "ipv4", "IPv6 Address": "ipv6",
            "MAC Address": "mac", "Default Gateway": "gateway", "DNS Servers": "dns", "DHCP": "dhcp",
        }
        for label, key in network_labels.items():
            self.network_values[label].setText(data["network"].get(key) or NOT_AVAILABLE)
        self.connectivity_values["Internet"].setText(self._status(data["internet_status"], data["internet_latency"]))
        self.connectivity_values["Gateway"].setText(self._status(data["gateway_status"], data["gateway_latency"], "Reachable", "Unreachable"))
        self.connectivity_values["DNS"].setText(self._status(data["dns_status"], data["dns_latency"], "Working", "Unavailable"))
        self.public_ip_value.setText(data.get("public_ip") or "Unavailable")
        self.update_label.setText("Updated just now")

    @staticmethod
    def _status(state: str, latency: str, positive: str = "Connected", negative: str = "Disconnected") -> str:
        return f"{'🟢' if state == 'Connected' else '🔴'} {positive if state == 'Connected' else negative} — {latency}"

    def _worker_finished(self) -> None:
        self.refresh_button.setEnabled(True)
        self.worker = None

    def copy_all(self) -> None:
        lines = ["NetScope Network Report", "=======================", "", "System"]
        for label in ("Computer Name", "Windows Version", "Username"):
            lines.append(f"{label}: {self.system_values[label].text()}")
        lines.extend(["", "Network"])
        for label in ("Adapter", "IPv4 Address", "IPv6 Address", "MAC Address", "Default Gateway", "DNS Servers", "DHCP"):
            lines.append(f"{label}: {self.network_values[label].text()}")
        lines.extend(["", "Connectivity"])
        for label in ("Internet", "Gateway", "DNS"):
            lines.append(f"{label}: {self.connectivity_values[label].text()}")
        lines.extend(["", "Public IP", self.public_ip_value.text()])
        QApplication.clipboard().setText("\n".join(lines))
