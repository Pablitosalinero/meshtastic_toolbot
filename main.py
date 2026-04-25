import sys
import time
from pubsub import pub
import meshtastic
import meshtastic.serial_interface
import serial.tools.list_ports

# --- CONFIGURACIÓN DEL NODO ---
# Se enviará como texto en el mensaje de bienvenida
BOT_LOCATION = "Totana (Murcia)"

def on_receive(packet, interface):
    try:
        # Verificar si hay datos decodificados en el paquete
        if 'decoded' not in packet:
            return
            
        decoded = packet['decoded']
        portnum = decoded.get('portnum')
        
        # Filtrar solo mensajes de texto (portnum 1 o 'TEXT_MESSAGE_APP')
        if portnum == 'TEXT_MESSAGE_APP' or portnum == 1:
            text = decoded.get('text', '')
            channel_index = packet.get('channel', 0)
            
            # Ignorar nuestros propios mensajes para no hacer bucles
            my_node_num = interface.myInfo.my_node_num if hasattr(interface, 'myInfo') else None
            if packet.get('from') == my_node_num:
                return 
            
            # Obtener el nombre del canal a partir de su índice
            channel_name = ""
            if hasattr(interface, 'localNode') and hasattr(interface.localNode, 'channels'):
                if 0 <= channel_index < len(interface.localNode.channels):
                    channel_obj = interface.localNode.channels[channel_index]
                    if hasattr(channel_obj, 'settings') and hasattr(channel_obj.settings, 'name'):
                        channel_name = channel_obj.settings.name

            print(f"[*] Mensaje recibido -> Canal: '{channel_name}' | Índice: {channel_index} | Texto: '{text}'")

            # Procesar el comando solo si el canal es "test"
            if channel_name.lower() == "test" and text.strip().lower() == "/ping":
                print(f">>> ¡Comando /ping detectado en el canal '{channel_name}'! Recopilando métricas...")
                
                rssi = packet.get('rxRssi', 'N/A')
                snr = packet.get('rxSnr', 'N/A')
                hop_start = packet.get('hopStart', 'N/A')
                hop_limit = packet.get('hopLimit', 'N/A')
                
                # Calcular número de saltos en ruta visualmente
                saltos_visual = "N/A"
                if isinstance(hop_start, int) and isinstance(hop_limit, int):
                    saltos_dados = max(0, hop_start - hop_limit)
                    saltos_visual = ("🟢" * saltos_dados) + ("⚪" * hop_limit) + f" ({saltos_dados}/{hop_start})"
                
                # Iconos de calidad de señal (RSSI) y Ruido (SNR)
                icon_rssi = "❔"
                if isinstance(rssi, (int, float)):
                    if rssi >= -70: icon_rssi = "🟢"
                    elif rssi >= -95: icon_rssi = "🟡"
                    else: icon_rssi = "🔴"
                    
                icon_snr = "❔"
                if isinstance(snr, (int, float)):
                    if snr >= 0: icon_snr = "🟢"
                    elif snr >= -10: icon_snr = "🟡"
                    else: icon_snr = "🔴"
                
                # Identificar la antena que retransmitió físicamente el paquete a nuestro receptor
                relay_byte = packet.get('relayNode')
                real_relay_id = None
                
                # Si los saltos dados son 0, entró directo y el Relay inmediato es el remitente original (from)
                if isinstance(hop_start, int) and isinstance(hop_limit, int) and hop_start == hop_limit:
                    real_relay_id = packet.get('from')
                elif relay_byte is not None and hasattr(interface, 'nodes'):
                    # Si hizo route, Meshtastic recorta el ID del Relay a 1 byte (0-255). Hay que buscar coincidencias en la DB
                    for _, n in interface.nodes.items():
                        node_num = n.get('num')
                        if node_num and (node_num & 0xFF) == relay_byte:
                            real_relay_id = node_num
                            break
                            
                if not real_relay_id:
                    real_relay_id = packet.get('from')

                nombre_relay = "Desconocido"
                if real_relay_id and hasattr(interface, 'nodes'):
                    # Buscar en la libreta de contactos local usando el ID completo expandido
                    for _, n in interface.nodes.items():
                        if n.get('num') == real_relay_id:
                            user_data = n.get('user', {})
                            nombre_relay = user_data.get('longName') or user_data.get('shortName') or f"!{real_relay_id:08x}"
                            break
                            
                if nombre_relay == "Desconocido" and real_relay_id:
                    nombre_relay = f"!{real_relay_id:08x}" # Hexadecimal formateado en 32 bits íntegro

                str_ultimo_nodo = f"\nRelay: {nombre_relay}"

                # Armamos el mensaje final compacto y visual
                reply = f"Node: {BOT_LOCATION}\n"
                reply += f"RSSI: {rssi} dBm {icon_rssi}\n"
                reply += f"SNR: {snr} dB {icon_snr}\n"
                reply += f"Hops: {saltos_visual}{str_ultimo_nodo}"

                # Enviar respuesta con las estadísticas vinculada al mensaje original
                reply_to_id = packet.get('id')
                interface.sendText(reply, channelIndex=channel_index, replyId=reply_to_id)
                
    except Exception as e:
        print(f"[!] Error procesando paquete: {e}")

def main():
    print("Iniciando Bot de Meshtastic (UV Environment)...")
    pub.subscribe(on_receive, "meshtastic.receive")
    
    device_port = None
    print("Buscando puertos Serie...")
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if 'COM' in p.device:
            device_port = p.device
            break
            
    if not device_port:
        print("No se ha encontrado ningún puerto. Revisa la conexión USB.")
        sys.exit(1)
        
    print(f"Puerto detectado: {device_port}. Conectando...")
    interface = None
    while True:
        try:
            # Asegurarse de liberar el puerto anterior si el anterior loop falló
            if interface and hasattr(interface, 'close'):
                try:
                    interface.close()
                except:
                    pass
                time.sleep(1)

            # Conexión manual para controlar los pines en Windows
            interface = meshtastic.serial_interface.SerialInterface(devPath=device_port, connectNow=False)
            
            # Liberar pines de reset (muy útil para chips ESP32 en Windows)
            if hasattr(interface, 'stream'):
                interface.stream.setDTR(False)
                interface.stream.setRTS(False)
            
            # Esperar a que la placa estabilice
            print("Iniciando conexión (esperando 4 seg por si la placa se reinició)...")
            time.sleep(4)
            
            print("Lanzando protocolo handshake con el dispositivo...")
            interface.connect()
            
            print("=== CONECTADO ===")
            print(f"El bot está a la escucha en el puerto {device_port}.")
            
            # --- DEBUG: Mostrar canales configurados ---
            print("\n--- TUS CANALES LOCALES ---")
            test_channel_idx = None
            if hasattr(interface, 'localNode') and hasattr(interface.localNode, 'channels'):
                for idx, ch in enumerate(interface.localNode.channels):
                    if hasattr(ch, 'settings'):
                        c_name = ch.settings.name
                        c_role = ch.role
                        # Ignorar canales deshabilitados (role 0 = DISABLED)
                        if c_role != 0:
                            print(f"> Índice: {idx} | Rol: {c_role} | Nombre guardado: '{c_name}'")
                            if c_name.lower() == "test":
                                test_channel_idx = idx
            print("---------------------------\n")

            if test_channel_idx is not None:
                print(f"Enviando mensaje de arranque al canal 'Test' (Índice {test_channel_idx})...")
                mi_nombre = interface.getLongName() or "Desconocido"
                startup_msg = f"Test node {mi_nombre} started."
                interface.sendText(startup_msg, channelIndex=test_channel_idx)

            print("Esperando comandos '/ping' en el canal 'Test'")
            
            while True:
                time.sleep(1)
                
        except PermissionError:
            print(f"Puerto {device_port} bloqueado. Cierra otras apps y reintenta.")
            time.sleep(5)
        except Exception as e:
            print(f"Fallo en comunicación: {e} | Reintentando en 6s...")
            time.sleep(6)

if __name__ == "__main__":
    main()
