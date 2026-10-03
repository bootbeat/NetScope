"""Offline tests for selecting and parsing local adapter information."""

import unittest

from netscope.network import NOT_AVAILABLE, parse_adapter_data, parse_ipconfig_output


class AdapterParsingTests(unittest.TestCase):
    def test_prefers_interface_with_default_gateway(self):
        result = parse_adapter_data([
            {"Name": "Virtual", "IPv4": ["192.168.56.1"], "Gateway": [], "DNS": []},
            {"Name": "Wi-Fi", "IPv4": ["192.0.2.12"], "Gateway": ["192.0.2.1"], "DNS": ["1.1.1.1"]},
        ])
        self.assertEqual(result["adapter"], "Wi-Fi")
        self.assertEqual(result["gateway"], "192.0.2.1")

    def test_handles_missing_adapter_data(self):
        result = parse_adapter_data([])
        self.assertEqual(result["ipv4"], NOT_AVAILABLE)
        self.assertEqual(result["dns"], NOT_AVAILABLE)

    def test_parses_ipconfig_multiline_dns_and_ignores_disconnected_adapter(self):
        output = """Ethernet adapter Disconnected:
   Media State . . . . . . . . . . : Media disconnected

Wireless LAN adapter Office Wi-Fi:
   Physical Address. . . . . . . . : AA-BB-CC-DD-EE-FF
   DHCP Enabled. . . . . . . . . . : Yes
   IPv4 Address. . . . . . . . . . : 192.0.2.8(Preferred)
   Default Gateway . . . . . . . . : 192.0.2.1
   DNS Servers . . . . . . . . . . : 1.1.1.1
                                       8.8.8.8
"""
        result = parse_ipconfig_output(output)
        self.assertEqual(result["adapter"], "Office Wi-Fi")
        self.assertEqual(result["ipv4"], "192.0.2.8")
        self.assertEqual(result["dns"], "1.1.1.1, 8.8.8.8")
        self.assertEqual(result["dhcp"], "Enabled")


if __name__ == "__main__":
    unittest.main()
