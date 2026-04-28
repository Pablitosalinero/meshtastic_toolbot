# Meshtastic Toolbot

This is an interactive Meshtastic bot developed in Python, managed via `uv` (Ultraviolet). It automatically connects to a Meshtastic device connected via serial/USB port, listens to messages, and responds with detailed network telemetry if it receives specific commands.

## Portable Executable Guide (Windows)

The easiest way to run the bot on Windows is by using the standalone portable executable (if available in the repository's Releases section). You don't need to install Python or any dependencies.

1. **Download:** Go to the [Releases](../../releases) section of this repository and download the `mtb-windows.zip` file.
2. **Extract:** Unzip the downloaded file to extract `mtb.exe`.
3. **Connect Device:** Plug your Meshtastic device into a USB port on your PC.
4. **Run via Command Line:** Open a Terminal or Command Prompt in the folder where you extracted the `.exe` and run it passing your configuration as arguments.

### Example Usage:

```cmd
mtb.exe --location "My City, Country" --channel "Test" --cooldown 20
```

### Available Command-Line Arguments:
- `--location`: (Optional) Text indicating the bot's location. This will be included in the telemetry response. Default: `"Unknown Location"`.
- `--channel`: (Optional) The channel name where the bot will listen for the `/ping` command. Default: `"Test"`.
- `--cooldown`: (Optional) Time in seconds that a user must wait before using a command again. Default: `20`.
- `--port`: (Optional) Manually specify the Serial COM port (e.g., `COM3`). If not provided, the bot will auto-detect the connected device.

---

## Node Configuration Requirements
Before running the bot, your local Meshtastic node must be configured with a specific channel so the bot can listen and respond. By default, ensure you have set up:
- **Channel Name:** `Test` (This is the default and highly recommended channel for running bots, to avoid spamming the main public channels).
- **PSK (Pre-Shared Key):** `Ag==` (Base64)

*Note: The channel name can be overridden using the `--channel` CLI argument, but the key depends entirely on your Meshtastic app configuration.*

## Requirements (For Development)
- [uv](https://github.com/astral-sh/uv) installed.
- A Meshtastic device connected locally via USB cable to the PC.

## Installation (For Development)

1. Clone or ensure you are in the directory of this repository.
2. Initialize the entire environment and download dependencies automatically using `uv` (our package manager). There is no need to manually install packages with pip, as `pyproject.toml` manages everything.
   
## Usage (Source Code)

To run the bot from the source code, simply execute the following command in this directory:

```bash
uv run main.py --location "My City"
```

The bot will attempt to connect via auto-discovery to the USB-connected device. Upon starting, it will announce its start on the target channel, indicating its original node name.

### Supported Commands

| Command / Event | Default Channel | Response                                   | Description                                                                                 |
|-----------------|-----------------|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `/ping`         | `Test`          | Complete telemetry and routing report      | Verifies that the bot is active and returns a technical analysis of the connection quality  |

### Metrics Dictionary for /ping

The bot disassembles the incoming Meshtastic protobuf packet to extract the following statistics:

- **Node**: Displays the text defined by the `--location` parameter.
- **RSSI**: Extracted from the temporary attribute `packet["rxRssi"]`. The base radio associates this data with the packet at the exact moment the antenna catches the signal, indicating the raw received power in dBm.
- **SNR**: Extracted from `packet["rxSnr"]`. Injected by the smart radio chip when measuring the electrical cleanliness threshold against the general background noise level of the band (dB).
- **Hops**: Calculated by subtracting routing metadata from the hardware packet. Meshtastic includes `hopStart` (maximum hops it left the sender with) and `hopLimit` (remaining). The bot uses `hopStart - hopLimit` to visually paint how many of these hops were consumed.
- **Relay**: The intermediate node that catapulted the packet to us. Meshtastic (to save bandwidth over LoRa) truncates the license plate of the relay antenna to a very small size of **1 single byte** (0-255) and stamps it in `packet["relayNode"]`. The bot, to get a clear name, reverse engineers this by crossing that byte against an iterative scan (`node_id & 0xFF`) of the internal contacts file (`interface.nodes`) until it finds a "match". If this fails or if the consumed hops were 0 (direct connection with no one repeating), the app removes the mask and maps it directly extracting the original 32-bit ID from the packet: `packet["from"]`.

## Code Structure

- **`main.py`**: The bot engine. Subscribes to device events with `pub.subscribe`, intercepts `TEXT_MESSAGE_APP` packets from the `Test` index, and responds to `id` using `replyId` in thread form. Contains visual mapping logic and CLI parsing.
- **`pyproject.toml`**: Python environment file managed natively by `uv`.

## Building the Executable

If you want to build the `mtb` portable executable yourself, simply run:

```bash
uv run pyinstaller --onefile --name mtb main.py
```

The `.exe` file will be generated inside the `dist/` folder.