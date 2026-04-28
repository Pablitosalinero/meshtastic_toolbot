import sys
import serial.tools.list_ports
import meshtastic.serial_interface
import time

def find_meshtastic_port():
    """
    Intelligently discover a Meshtastic serial port across Windows, macOS, and Linux.
    Looks for known VIDs, PIDs, or typical device names.
    """
    ports = serial.tools.list_ports.comports()
    
    # Known manufacturer hints, or simple 'COM', 'ttyUSB', 'ttyACM', 'cu.' prefixes
    valid_prefixes = ('COM', 'ttyUSB', 'ttyACM', 'cu.SLAB', 'cu.usbserial', 'cu.wchusbserial')
    
    # Try to find a CH340 or CP2102 based device (common for ESP32/ESP8266)
    for p in ports:
        if p.vid is not None:
            # Common VIDs: 10C4 (Silicon Labs), 1A86 (QinHeng / CH340), 303A (Espressif)
            if p.vid in (0x10C4, 0x1A86, 0x303A):
                return p.device
                
        # Fallback to checking device name string
        if any(prefix in p.device for prefix in valid_prefixes):
            return p.device
            
    return None

def connect(target_port=None):
    device_port = target_port
    if not device_port:
        print("Searching for Meshtastic Serial ports...")
        device_port = find_meshtastic_port()
        
    if not device_port:
        print("No serial port found. Check USB connection.")
        sys.exit(1)
        
    print(f"Port detected: {device_port}. Connecting...")
    
    interface = None
    while True:
        try:
            # Ensure the previous port is released if the previous loop failed
            if interface and hasattr(interface, 'close'):
                try:
                    interface.close()
                except:
                    pass
                time.sleep(1)

            # Manual connection to control pins
            interface = meshtastic.serial_interface.SerialInterface(devPath=device_port, connectNow=False)
            
            # Release reset pins (very useful for ESP32 chips)
            if hasattr(interface, 'stream'):
                interface.stream.setDTR(False)
                interface.stream.setRTS(False)
            
            # Wait for board to stabilize
            print("Starting connection (waiting 4 seconds in case the board restarted)...")
            time.sleep(4)
            
            print("Launching handshake protocol with the device...")
            interface.connect()
            
            print("=== CONNECTED ===")
            print(f"The bot is connected on port {device_port}.")
            return interface
            
        except PermissionError:
            print(f"Port {device_port} is blocked. Close other apps and retry.")
            time.sleep(5)
        except Exception as e:
            print(f"Communication failure: {e} | Retrying in 6s...")
            time.sleep(6)
