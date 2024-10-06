import os
import zipfile
import tempfile
import shutil
import subprocess
from io import BytesIO
import urllib.request
import json
import serial.tools.list_ports
import sys

GITHUB_API_URL = "https://api.github.com/repos/espressif/esptool/releases/latest"
FOLDER_IN_ZIP = "esptool-win64"
FILE_TO_EXTRACT = "esp_rfc2217_server.exe"


def get_latest_release():
    """Fetch the latest release data from GitHub API using urllib"""
    print("Fetching latest release information...")
    with urllib.request.urlopen(GITHUB_API_URL) as response:
        if response.status == 200:
            return json.load(response)
        else:
            raise Exception(f"Failed to fetch release information: {response.status}")


def download_asset(download_url):
    """Download the asset from the release using urllib"""
    print(f"Downloading asset from {download_url}...")

    request = urllib.request.Request(
        download_url, headers={"Accept": "application/octet-stream"}
    )

    with urllib.request.urlopen(request) as response:
        if response.status == 200:
            print("Download complete")
            return BytesIO(response.read())
        else:
            raise Exception(f"Failed to download asset: {response.status}")


def extract_file_from_zip(zip_data, folder_in_zip, file_to_extract, temp_dir):
    """Extract a specific file from the ZIP archive into a temporary folder"""
    with zipfile.ZipFile(zip_data, "r") as zip_ref:
        file_in_zip_path = f"{folder_in_zip}/{file_to_extract}"

        if file_in_zip_path in zip_ref.namelist():
            print(
                f"Extracting {file_to_extract} from {folder_in_zip} into {temp_dir}..."
            )
            extracted_path = os.path.join(temp_dir, file_to_extract)
            with open(extracted_path, "wb") as output_file:
                output_file.write(zip_ref.read(file_in_zip_path))
            print(f"File saved to {extracted_path}.")
            return extracted_path
        else:
            raise FileNotFoundError(f"{file_to_extract} not found in the zip archive")


def find_esp_device():
    """Find the COM port of the connected ESP device based on VID and PID"""
    esp32_vid_pid = [
        ("0403", "6015"),
        ("10C4", "EA60"),
        ("1A86", "7523"),
    ]

    ports = serial.tools.list_ports.comports()
    for port in ports:
        vid = f"{port.vid:04X}" if port.vid else None
        pid = f"{port.pid:04X}" if port.pid else None
        if (vid, pid) in esp32_vid_pid:
            return port.device
    raise Exception("No ESP32 device found")


def run_in_new_terminal_windows(executable_path, args):
    """Run the command in a new terminal window (Windows)"""
    command = f'start cmd /k "{executable_path} {" ".join(args)}"'
    print(f"Running in new terminal: {command}")
    subprocess.Popen(command, shell=True)


if __name__ == "__main__":
    try:
        com_port = find_esp_device()

        tmp_dir = os.path.join(os.getcwd(), "tmp")
        new_file_path = os.path.join(tmp_dir, FILE_TO_EXTRACT)

        if not os.path.exists(new_file_path):
            print(f"{FILE_TO_EXTRACT} does not exist, downloading and extracting it...")

            os.makedirs(tmp_dir, exist_ok=True)

            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"Created temporary directory: {temp_dir}")

                release_data = get_latest_release()

                release_version = release_data["tag_name"]
                print(f"Latest release version: {release_version}")

                asset_name = f"esptool-{release_version}-win64.zip"
                print(f"Expected asset name: {asset_name}")

                asset = None
                for a in release_data["assets"]:
                    if asset_name in a["name"]:
                        asset = a
                        break

                if not asset:
                    raise Exception(
                        f"Asset {asset_name} not found in the latest release"
                    )

                asset_url = asset["browser_download_url"]

                zip_data = download_asset(asset_url)

                extracted_file_path = extract_file_from_zip(
                    zip_data, FOLDER_IN_ZIP, FILE_TO_EXTRACT, temp_dir
                )

                shutil.move(extracted_file_path, new_file_path)
                print(f"Moved {FILE_TO_EXTRACT} to {new_file_path}")

        args = ["-v", "-p", "4000", com_port]
        run_in_new_terminal_windows(new_file_path, args)

    except Exception as e:
        print(f"Error: {e}")
