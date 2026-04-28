def extract_text_message(packet):
    """
    Returns (portnum, text, channel_index, from_node, reply_to_id) 
    if the packet is a valid text message. Otherwise, returns None.
    """
    if 'decoded' not in packet:
        return None
        
    decoded = packet['decoded']
    portnum = decoded.get('portnum')
    
    if portnum == 'TEXT_MESSAGE_APP' or portnum == 1:
        text = decoded.get('text', '')
        channel_index = packet.get('channel', 0)
        from_node = packet.get('from')
        reply_to_id = packet.get('id')
        return (portnum, text, channel_index, from_node, reply_to_id)
        
    return None

def get_channel_name(interface, channel_index):
    """
    Safely retrieves the channel name given an index.
    """
    if hasattr(interface, 'localNode') and hasattr(interface.localNode, 'channels'):
        if 0 <= channel_index < len(interface.localNode.channels):
            channel_obj = interface.localNode.channels[channel_index]
            if hasattr(channel_obj, 'settings') and hasattr(channel_obj.settings, 'name'):
                return channel_obj.settings.name
    return ""

def get_telemetry_metrics(packet):
    """
    Extracts RSSI, SNR, hop_start, and hop_limit.
    """
    rssi = packet.get('rxRssi', 'N/A')
    snr = packet.get('rxSnr', 'N/A')
    hop_start = packet.get('hopStart', 'N/A')
    hop_limit = packet.get('hopLimit', 'N/A')
    return rssi, snr, hop_start, hop_limit

def get_node_name(interface, node_num):
    """
    Looks up a node name from its 32-bit ID.
    """
    if node_num and hasattr(interface, 'nodes'):
        for _, n in interface.nodes.items():
            if n.get('num') == node_num:
                user_data = n.get('user', {})
                return user_data.get('longName') or user_data.get('shortName') or f"!{node_num:08x}"
    if node_num:
        return f"!{node_num:08x}"
    return "Unknown"

def identify_relay(packet, interface, hop_start, hop_limit):
    """
    Identifies the relay node name based on the 1-byte truncated relayNode packet header.
    """
    relay_byte = packet.get('relayNode')
    real_relay_id = None
    
    # If hops taken is 0, it came direct and the immediate relay is the original sender (from)
    if isinstance(hop_start, int) and isinstance(hop_limit, int) and hop_start == hop_limit:
        real_relay_id = packet.get('from')
    elif relay_byte is not None and hasattr(interface, 'nodes'):
        # If routed, Meshtastic trims Relay ID to 1 byte (0-255). We must find a match in the DB
        for _, n in interface.nodes.items():
            node_num = n.get('num')
            if node_num and (node_num & 0xFF) == relay_byte:
                real_relay_id = node_num
                break
                
    if not real_relay_id:
        real_relay_id = packet.get('from')

    relay_name = get_node_name(interface, real_relay_id)
    return real_relay_id, relay_name
