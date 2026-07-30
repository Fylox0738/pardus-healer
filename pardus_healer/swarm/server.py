"""Swarm Server Modülü.

UDP Broadcast ile keşfedilmeyi sağlar ve basit bir HTTP API sunar.
"""

from __future__ import annotations

import socket
import threading
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os

from pardus_healer.core.engine import DiagnosisEngine
from pardus_healer.core.models import Status

# Sadece kök seviyede bir logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - SWARM_SERVER - %(message)s")

UDP_PORT = 4242
HTTP_PORT = 4243

class SwarmHTTPHandler(BaseHTTPRequestHandler):
    """Pardus Healer ağ API'si."""
    
    def do_GET(self):
        if self.path == '/health':
            from pardus_healer.config import Config
            from pardus_healer.swarm.auth import verify_auth_headers
            expected_token = Config().swarm_token
            
            # Doğrulama: Headers dict-like object
            if not verify_auth_headers(self.headers, expected_token, method="GET", path=self.path):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Yetkisiz Erisim veya Gecersiz Imza.")
                return

            try:
                engine = DiagnosisEngine()
                # Hızlı (parallel) modda koş
                report = engine.run_all(concurrent=True)
                
                response_data = {
                    "hostname": socket.gethostname(),
                    "health_score": report.health_score,
                    "grade": report.grade,
                    "fail_count": report.fail_count,
                    "warn_count": report.warn_count,
                    "ok_count": report.ok_count
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/heal_all' or self.path.startswith('/heal_node'):
            from pardus_healer.config import Config
            from pardus_healer.swarm.auth import verify_auth_headers
            expected_token = Config().swarm_token
            
            if not verify_auth_headers(self.headers, expected_token, method="POST", path=self.path):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Yetkisiz Erisim veya Gecersiz Imza.")
                return

            try:
                engine = DiagnosisEngine()
                report = engine.run_all(concurrent=True)
                issues_to_fix = [r for r in report.results if r.is_actionable and r.status == Status.FAIL]
                
                from pardus_healer.core.shell import run_fix_as_root

                fixed_count = 0
                for issue in issues_to_fix:
                    if issue.fix:
                        result = run_fix_as_root(issue.fix.resolved_command())
                        if result.ok:
                            fixed_count += 1
                        
                response_data = {
                    "status": "success",
                    "message": f"{fixed_count} sorun onarıldı."
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        # Varsayılan stdout loglarını kapat
        pass

def run_udp_discovery_responder():
    """Ağdaki diğer Healer düğümlerinin bu bilgisayarı bulabilmesi için UDP Broadcast dinleyicisi."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Broadcastleri dinle
    try:
        sock.bind(('', UDP_PORT))
    except Exception as e:
        logging.error(f"UDP Bind hatası (Port {UDP_PORT} kullanılıyor olabilir): {e}")
        return

    logging.info(f"UDP Keşif Servisi dinleniyor (Port {UDP_PORT})...")
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = data.decode('utf-8').strip()
            
            if msg == "DISCOVER_HEALER_NODES":
                hostname = socket.gethostname()
                reply = f"HEALER_NODE:{hostname}:{HTTP_PORT}"
                sock.sendto(reply.encode('utf-8'), addr)
                logging.info(f"Keşif isteği alındı: {addr[0]}. Yanıt gönderildi.")
        except Exception as e:
            logging.error(f"UDP Dinleme hatası: {e}")

def run_http_server():
    """HTTP API'sini başlatır."""
    server_address = ('0.0.0.0', HTTP_PORT)
    try:
        httpd = HTTPServer(server_address, SwarmHTTPHandler)
        logging.info(f"HTTP API Servisi başlatıldı (Port {HTTP_PORT})...")
        httpd.serve_forever()
    except Exception as e:
        logging.error(f"HTTP Servisi hatası: {e}")

def start_server():
    """Swarm Server (Filo Düğümü) modunu başlatır."""
    logging.info("Pardus Healer Swarm Düğümü başlatılıyor...")
    
    # UDP responder thread
    udp_thread = threading.Thread(target=run_udp_discovery_responder, daemon=True)
    udp_thread.start()
    
    # HTTP server thread (blocking)
    run_http_server()
