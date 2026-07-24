import subprocess

class LogReader:
    @staticmethod
    def get_critical_logs(lines=100):
        """journalctl üzerinden son N satır kritik (0-3 arası) hatayı okur."""
        try:
            r = subprocess.run(["journalctl", "-p", "0..3", "-n", str(lines), "--no-pager", "--output=short-iso"], capture_output=True, text=True)
            return r.stdout.splitlines() if r.returncode == 0 else []
        except Exception:
            return []

    @staticmethod
    def get_dmesg_errors():
        """Kernel ring buffer (dmesg) üzerinden çekirdek/donanım hatalarını yakalar."""
        try:
            r = subprocess.run(["dmesg", "-l", "err,crit,alert,emerg"], capture_output=True, text=True)
            return r.stdout.splitlines() if r.returncode == 0 else []
        except Exception:
            return []
            
    @staticmethod
    def get_service_failures():
        """systemctl üzerinden çöken servisleri listeler."""
        try:
            r = subprocess.run(["systemctl", "--failed", "--no-pager"], capture_output=True, text=True)
            return r.stdout.splitlines() if r.returncode == 0 else []
        except Exception:
            return []
