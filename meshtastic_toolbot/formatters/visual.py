def get_hops_visual(hop_start, hop_limit):
    """
    Returns visual string of hops taken.
    """
    if isinstance(hop_start, int) and isinstance(hop_limit, int):
        hops_taken = max(0, hop_start - hop_limit)
        return ("🟢" * hops_taken) + ("⚪" * hop_limit) + f" ({hops_taken}/{hop_start})"
    return "N/A"

def get_signal_icons(rssi, snr):
    """
    Returns (rssi_icon, snr_icon)
    """
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
        
    return icon_rssi, icon_snr
