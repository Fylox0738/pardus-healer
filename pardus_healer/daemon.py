"""Otonom Koruma Kalkanı (Daemon Modu).

Arka planda (root yetkisiyle) düzenli olarak sistemi tarar.
Kritik bir hata bulursa kullanıcı müdahalesine gerek kalmadan
otomatik olarak düzeltir (Self-Healing) ve masaüstüne bildirim gönderir.
"""

from __future__ import annotations

import time
import subprocess
import logging
from pardus_healer.core.engine import DiagnosisEngine
from pardus_healer.core.models import Status
from pardus_healer.core import notify

# Sadece root altında çalışması planlanır.
# `journalctl -u pardus-healer-daemon` ile loglar izlenebilir.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - HEALER_DAEMON - %(message)s")

def run_daemon(interval_seconds: int = 600):
    logging.info("Otonom Koruma Kalkanı (Pardus Healer Daemon) başlatıldı.")
    engine = DiagnosisEngine()

    while True:
        try:
            logging.info("Sistem sağlık taraması başlatılıyor...")
            report = engine.run_all(concurrent=True)
            
            # Aksiyon alınabilir (is_actionable) FAIL veya WARN durumlarını bul
            issues_to_fix = [r for r in report.results if r.is_actionable and r.status == Status.FAIL]
            
            if issues_to_fix:
                logging.warning(f"{len(issues_to_fix)} adet kritik arıza tespit edildi. Otonom onarım başlatılıyor.")
                
                fixed_count = 0
                for issue in issues_to_fix:
                    if issue.fix:
                        # Daemon root olarak çalıştığı için 'pkexec' kullanmamalıyız.
                        # Komutun başındaki olası pkexec'i kaldıralım
                        cmd = issue.fix.resolved_command()
                        if cmd.startswith("pkexec "):
                            cmd = cmd.replace("pkexec ", "", 1)
                        elif " pkexec " in cmd:
                            cmd = cmd.replace(" pkexec ", " ", 1)
                            
                        logging.info(f"Onarılıyor: {issue.title} -> {cmd}")
                        
                        # Komutu çalıştır
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        if result.returncode == 0:
                            fixed_count += 1
                            logging.info(f"Başarılı: {issue.title}")
                        else:
                            logging.error(f"Onarım başarısız: {issue.title} (Hata: {result.stderr.strip()})")
                
                if fixed_count > 0:
                    # Kullanıcıya masaüstü bildirimi gönder
                    # Root olduğumuz için doğrudan DBus üzerinden veya os.system ile kullanıcıya bildirim atmalıyız.
                    # Pardus Healer'ın mevcut notify modülü kullanılıyor.
                    msg = f"Sistem çökmek üzereyken otonom olarak müdahale edildi ve {fixed_count} sorun çözüldü."
                    notify.notify_report(0, 0, 100) # İkonları göstermek için mevcut API (geçici)
                    
                    # Mevcut notify API'si yerine doğrudan bash komutu da çalıştırabiliriz (tüm kullanıcılara)
                    subprocess.run(
                        ['su', '-', 'pardus', '-c', f'notify-send "🛡️ Pardus Healer Kalkanı" "{msg}" -u critical'],
                        capture_output=True
                    )
            else:
                logging.info(f"Sistem sağlıklı. Skor: {report.health_score} ({report.grade})")
                
        except Exception as e:
            logging.error(f"Daemon hatası: {e}")
            
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_daemon()
