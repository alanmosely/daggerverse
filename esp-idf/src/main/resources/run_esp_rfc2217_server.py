"""Start an RFC2217 server exposing the local ESP device's serial port.

Cross-platform (Windows/Linux/macOS). Requires esptool >= 5.0, which
provides the esp_rfc2217_server command and pyserial:

    pip install "esptool>=5.0"

The server forwards the serial port over TCP so containers can flash the
device, e.g. via the esp-idf Dagger module:

    dagger call flash --project-dir . --serial-host host.docker.internal --serial-port 4000

If SERIAL_PORT is omitted, the connected ESP device is auto-detected by
its USB VID/PID. The server runs in the foreground; stop it with Ctrl+C.
"""

import argparse
import shutil
import subprocess
import sys

# Common USB-serial bridges and native USB interfaces on ESP dev boards
ESP_USB_IDS = [
    ("0403", "6015"),  # FTDI FT231X
    ("10C4", "EA60"),  # Silicon Labs CP210x
    ("1A86", "7523"),  # WCH CH340
    ("1A86", "55D4"),  # WCH CH9102
    ("303A", "1001"),  # Espressif USB Serial/JTAG
]


def find_esp_device() -> str:
    """Find the serial port of the connected ESP device by USB VID/PID"""
    try:
        import serial.tools.list_ports
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required to detect ESP devices; install esptool: "
            'pip install "esptool>=5.0"'
        ) from exc

    for port in serial.tools.list_ports.comports():
        vid = f"{port.vid:04X}" if port.vid else None
        pid = f"{port.pid:04X}" if port.pid else None
        if (vid, pid) in ESP_USB_IDS:
            return port.device
    raise SystemExit(
        "No ESP device found; pass the serial port explicitly, e.g. "
        f"python {sys.argv[0]} COM3"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve the local ESP device's serial port over RFC2217"
    )
    parser.add_argument(
        "serial_port",
        nargs="?",
        help="Serial port to serve (e.g. COM3, /dev/ttyUSB0); auto-detected if omitted",
    )
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=4000,
        help="TCP port to listen on (default: 4000, the flash function's default)",
    )
    args = parser.parse_args()

    server = shutil.which("esp_rfc2217_server") or shutil.which(
        "esp_rfc2217_server.py"
    )
    if not server:
        raise SystemExit(
            'esp_rfc2217_server not found; install esptool: pip install "esptool>=5.0"'
        )

    serial_port = args.serial_port or find_esp_device()
    print(f"Serving {serial_port} on RFC2217 port {args.tcp_port} (Ctrl+C to stop)")
    try:
        return subprocess.call([server, "-v", "-p", str(args.tcp_port), serial_port])
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        raise SystemExit(f"failed to run {server}: {exc}") from exc


if __name__ == "__main__":
    sys.exit(main())
