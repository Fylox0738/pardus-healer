import subprocess
import os
from datetime import datetime

class GitAnalyzer:
    def __init__(self, repo_path):
        self.repo_path = os.path.expanduser(repo_path)

    def is_valid_repo(self):
        return os.path.isdir(os.path.join(self.repo_path, ".git"))

    def get_recent_commits(self, limit=20):
        if not self.is_valid_repo():
            return []
        
        # Git log çıktısını ISO 8601 formatında alıyoruz (örn: 2026-03-26T10:15:30)
        cmd = ["git", "log", f"-n", str(limit), "--pretty=format:%h|%cI|%an|%s"]
        try:
            r = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            commits = []
            if r.returncode == 0 and r.stdout:
                for line in r.stdout.splitlines():
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "date_iso": parts[1], # 2026-03-26T10:15:30+03:00
                            "author": parts[2],
                            "message": parts[3]
                        })
            return commits
        except Exception:
            return []
            
    def match_logs_to_commits(self, logs, commits):
        """
        Gelen sistem logları (ISO date formatlıysa) ile Git commit tarihlerini karşılaştırır.
        Basit bir correlation: Aynı gün içinde commit atıldıysa ve sistem hata verdiyse ilişkilendir!
        """
        matches = []
        for c in commits:
            try:
                # Loglar da "short-iso" formatinda cekildigi icin YYYY-MM-DD ile match edebiliriz.
                commit_day = c['date_iso'][:10] # YYYY-MM-DD
                
                related_logs = []
                for log_line in logs:
                    if commit_day in log_line:
                        related_logs.append(log_line)
                
                if related_logs:
                    matches.append({
                        "commit": c,
                        "logs": related_logs[:5] # Sadece ispat icin ilk 5 log yeterli
                    })
            except:
                pass
        return matches
