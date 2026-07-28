"""Swarm İstemci (Filo Yöneticisi) Modülü.

Ağdaki düğümleri bulur ve onlara komut gönderir.
"""

from __future__ import annotations

import socket
import json
import urllib.request
from typing import Dict, Any

UDP_PORT = 4242

def discover_nodes(timeout: float = 2.0) -> list[dict[str, str]]:
    """Ağdaki Pardus Healer sunucularını keşfeder."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    
    nodes = []
    seen_ips = set()
    
    # Broadcast mesajı gönder
    msg = "DISCOVER_HEALER_NODES"
    try:
        sock.sendto(msg.encode('utf-8'), ('<broadcast>', UDP_PORT))
    except Exception:
        # Eğer <broadcast> çalışmazsa 255.255.255.255 deneyelim
        try:
            sock.sendto(msg.encode('utf-8'), ('255.255.255.255', UDP_PORT))
        except Exception:
            pass
            
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            reply = data.decode('utf-8').strip()
            ip = addr[0]
            
            if reply.startswith("HEALER_NODE:") and ip not in seen_ips:
                parts = reply.split(":")
                if len(parts) >= 3:
                    hostname = parts[1]
                    http_port = parts[2]
                    nodes.append({
                        "ip": ip,
                        "hostname": hostname,
                        "port": http_port
                    })
                    seen_ips.add(ip)
        except socket.timeout:
            break
        except Exception:
            break
            
    return nodes

def get_node_health(ip: str, port: str = "4243") -> Dict[str, Any] | None:
    """Bir düğümden (Node) sağlık durumunu çeker."""
    url = f"http://{ip}:{port}/health"
    try:
        from pardus_healer.config import Config
        from pardus_healer.swarm.auth import generate_auth_headers
        token = Config().swarm_token
        req = urllib.request.Request(url, method="GET")
        
        auth_headers = generate_auth_headers(token)
        for k, v in auth_headers.items():
            req.add_header(k, v)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                return json.loads(data)
    except Exception:
        return None
    return None

def heal_node(ip: str, port: str = "4243") -> bool:
    """Bir düğüme (Node) onarım sinyali gönderir."""
    url = f"http://{ip}:{port}/heal_all"
    try:
        from pardus_healer.config import Config
        from pardus_healer.swarm.auth import generate_auth_headers
        token = Config().swarm_token
        req = urllib.request.Request(url, method="POST")
        
        auth_headers = generate_auth_headers(token)
        for k, v in auth_headers.items():
            req.add_header(k, v)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return True
    except Exception:
        return False
    return False
