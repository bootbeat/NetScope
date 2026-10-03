"""Start the NetScope Windows network dashboard."""

import sys

from PySide6.QtWidgets import QApplication

from netscope.gui import NetScopeWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NetScope")
    window = NetScopeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
