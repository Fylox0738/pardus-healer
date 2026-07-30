"""Otonom Koruma Kalkanı (Daemon Modu).

Arka planda (root yetkisiyle) düzenli olarak sistemi tarar.
Kritik bir hata bulursa kullanıcı müdahalesine gerek kalmadan
otomatik olarak düzeltir (Self-Healing) ve masaüstüne bildirim gönderir.
"""

from __future__ import annotations

import os
import time
import subprocess
import logging
import gc
from pardus_healer.core.engine import DiagnosisEngine
from pardus_healer.core.models import Status
from pardus_healer.core import notify
from pardus_healer.core import shell

# Sadece root altında çalışması planlanır.
# `journalctl -u pardus-healer-daemon` ile loglar izlenebilir.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - HEALER_DAEMON - %(message)s")

# Eskiden yalnızca 4 süreç adı kontrol ediliyordu ve bunlardan ikisi
# ("impress", "loimpress") gerçekte hiç eşleşmiyordu — LibreOffice Impress
# çalışırken görünen gerçek süreç adı "soffice.bin"dir, "impress"/
# "loimpress" yalnızca başlatıcı betik adlarıdır.
# Liste ayrıca PDF/sunum görüntüleyiciler ve video konferans araçlarını
# kapsayacak şekilde genişletildi.
_PRESENTATION_PROCESSES = [
    'soffice.bin', 'impress', 'loimpress',
    'okular', 'evince',
    'vlc', 'mpv', 'totem',
    'zoom', 'teams',
]

def is_presentation_mode_active() -> bool:
    """Ekrandaki aktif pencerenin tam ekran bir sunum veya medya oynatıcı olup olmadığını kontrol eder."""
    try:
        # Sunum programlarını iteratif kontrol et
        for prog in _PRESENTATION_PROCESSES:
            try:
                output = subprocess.check_output(['pgrep', '-x', prog], text=True)
                if output.strip():
                    return True
            except subprocess.CalledProcessError:
                continue
    except Exception as e:
        logging.error(f"Ders modu tespiti hatasi: {e}")
    return False

def setup_watchdog():
    """Otonom onarım sırasında yaşanabilecek Kernel Panic veya donmalara karşı geri dönüş sigortası bırakır."""
    try:
        # Örnek mekanizma: Bir sonraki yeniden başlatmada Timeshift snapshot'ına dönmek için
        # bir işaret (flag) dosyası bırakır. Sistem sağlıklı açılırsa Healer bu dosyayı siler.
        # Güvenlik: Dosya izinleri kısıtlı (sadece root okuyabilir/yazabilir)
        subprocess.run(['touch', '/var/run/healer_watchdog_active'], shell=False)
        subprocess.run(['chmod', '600', '/var/run/healer_watchdog_active'], shell=False)
    except Exception as e:
        logging.error(f"Watchdog ayarlanırken hata: {e}")

def clear_watchdog():
    """Watchdog işaretini temizler (Sistem sağlıklı)."""
    subprocess.run(['rm', '-f', '/var/run/healer_watchdog_active'], shell=False)

def check_and_clear_watchdog():
    """Daemon başlarken önceki oturumdan kalan watchdog işaretini denetler.

    Eskiden bu işaret hiç OKUNMADAN, doğrudan silinirdi — yani "watchdog"un
    iddia ettiği "çökmeye karşı geri dönüş sigortası" hiçbir zaman devreye
    girmiyordu. Dosya hâlâ varsa, bir önceki
    otonom onarım turu clear_watchdog()'a ulaşamadan kesilmiş demektir
    (beklenmedik çökme/elektrik kesintisi/kernel panic) — bu durumda
    kullanıcı bilgilendirilir.
    """
    flag = "/var/run/healer_watchdog_active"
    if os.path.exists(flag):
        logging.warning(
            "Watchdog işareti aktif bulundu: önceki otonom onarım turu "
            "yarım kalmış olabilir (beklenmedik çökme/elektrik kesintisi)."
        )
        try:
            active_user = "pardus"
            who_output = subprocess.check_output(['who'], text=True).splitlines()
            if who_output:
                active_user = who_output[0].split()[0]
            subprocess.run(
                ['su', '-', active_user, '-c',
                 'notify-send "⚠️ Pardus Healer Kalkanı" '
                 '"Önceki otonom onarım yarım kalmış olabilir, sisteminizi '
                 'kontrol edin." -u critical'],
                capture_output=True, shell=False,
            )
        except Exception as e:
            logging.error(f"Watchdog kurtarma bildirimi gönderilemedi: {e}")
    clear_watchdog()

def run_daemon(interval_seconds: int = 600):
    logging.info("Otonom Koruma Kalkanı (Pardus Healer Daemon) başlatıldı.")

    check_and_clear_watchdog()

    while True:
        try:
            # Döngü başında engine oluştur
            engine = DiagnosisEngine()
            
            logging.info("Sistem sağlık taraması başlatılıyor...")
            report = engine.run_all(concurrent=True)
            
            # Aksiyon alınabilir (is_actionable) FAIL veya WARN durumlarını bul
            issues_to_fix = [r for r in report.results if r.is_actionable and r.status == Status.FAIL]
            
            if issues_to_fix:
                if is_presentation_mode_active():
                    logging.warning("Ders/Sunum modu aktif. Otonom onarım ertelendi (Kullanıcı rahatsız edilmeyecek).")
                else:
                    logging.warning(f"{len(issues_to_fix)} adet kritik arıza tespit edildi. Otonom onarım başlatılıyor.")
                    
                    fixed_count = 0
                    setup_watchdog() # Riskli işlemlere girmeden sigortayı kur (tüm işlemler için 1 kez)
                    
                    import shutil
                    if shutil.which("timeshift"):
                        logging.info("Güvenlik yedeği alınıyor (Timeshift)...")
                        subprocess.run(["timeshift", "--create", "--comments", "Pardus Healer Otonom Pre-Fix"], shell=False, check=False)
                        
                    for issue in issues_to_fix:
                        if issue.fix:
                            logging.info(f"Onarılıyor: {issue.title}")
                            result = shell.run_fix_as_root(issue.fix.resolved_command())
                            if result.ok:
                                fixed_count += 1
                                logging.info(f"Başarılı: {issue.title}")
                            else:
                                logging.error(f"Onarım başarısız: {issue.title} (Hata: {result.stderr.strip()})")
                                    
                    clear_watchdog() # Tüm onarımlar bitti, sigortayı kaldır
                    
                    if fixed_count > 0:
                        msg = f"Sistem çökmek üzereyken otonom olarak müdahale edildi ve {fixed_count} sorun çözüldü."
                        notify.notify_report(0, 0, 100) # İkonları göstermek için
                        
                        # Aktif X11 kullanıcısını dinamik tespit et
                        active_user = "pardus"
                        try:
                            who_output = subprocess.check_output(['who'], text=True).splitlines()
                            if who_output:
                                active_user = who_output[0].split()[0]
                        except Exception:
                            pass
                            
                        subprocess.run(
                            ['su', '-', active_user, '-c', f'notify-send "🛡️ Pardus Healer Kalkanı" "{msg}" -u critical'],
                            capture_output=True,
                            shell=False
                        )
            else:
                logging.info(f"Sistem sağlıklı. Skor: {report.health_score} ({report.grade})")
                
            # Bellek Sızıntısını (Memory Leak) önlemek için nesneleri zorla sil ve GC çağır
            del report
            del issues_to_fix
            del engine
            gc.collect()
                
        except Exception as e:
            logging.error(f"Daemon hatası: {e}")
            
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_daemon()
