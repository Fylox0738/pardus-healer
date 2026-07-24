#!/usr/bin/env python3
import os
import re
import subprocess
import sys

# Pardus/Debian paket adlarıyla eşleşen katı bir kalıp — bunun dışındaki
# hiçbir token argv'ye eklenmez (apt geçmişindeki serbest metinden gelen
# tokenlerin komut satırına kaçak bayrak/enjeksiyon olarak sızmasını önler).
_PACKAGE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+.\-:]*$")

def print_banner():
    print("=" * 65)
    print(" 🏥 PARDUS HEALER - KURTARMA MODU (RESCUE CLI)")
    print("=" * 65)
    print("Grafik arayüzün (GUI) çöktüğü siyah ekran (TTY) durumlarında,")
    print("sistemi komut satırından onarmanızı sağlar. (Linux Ctrl+Z)\n")

def parse_history():
    history_file = "/var/log/apt/history.log"
    if not os.path.exists(history_file):
        print("ℹ️ APT History dosyası bulunamadı.")
        return []
        
    records = []
    current_record = {}
    try:
        with open(history_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    if "Start-Date" in current_record and "Commandline" in current_record:
                        records.append(current_record)
                    current_record = {}
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    current_record[key.strip()] = val.strip()
                    
        if current_record and "Start-Date" in current_record:
            records.append(current_record)
            
        records.reverse()
        
        actions = []
        for rec in records:
            date = rec.get("Start-Date", "")
            cmd = rec.get("Commandline", "")
            if "apt " in cmd or "apt-get " in cmd:
                revert_action = ""
                packages = []
                action_name = ""
                if "install" in cmd:
                    raw = [w for w in cmd.split() if w not in ["apt", "apt-get", "install", "-y", "sudo", "pkexec"]]
                    packages = [w for w in raw if _PACKAGE_NAME_RE.match(w)]
                    if packages:
                        revert_action = "remove"
                        action_name = f"Kurulum: {' '.join(packages)}"
                elif ("remove" in cmd or "purge" in cmd) and "autoremove" not in cmd:
                    raw = [w for w in cmd.split() if w not in ["apt", "apt-get", "remove", "purge", "-y", "sudo", "pkexec"]]
                    packages = [w for w in raw if _PACKAGE_NAME_RE.match(w)]
                    if packages:
                        revert_action = "install"
                        action_name = f"Silme: {' '.join(packages)}"

                if revert_action and packages:
                    actions.append({
                        "date": date, "name": action_name,
                        "revert_action": revert_action, "packages": packages,
                    })
                    
        return actions
    except Exception as e:
        print(f"Hata: {e}")
        return []

def main():
    if os.geteuid() != 0:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(" UYARI: Bu araç sistem paketlerini değiştireceği için")
        print(" root haklarına (sudo) ihtiyaç duyar.")
        print(" Lütfen aracı şu şekilde başlatın:  sudo healer-rescue")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        # Biz yine de listeyi gösterelim, çalıştırırken sudo ekleriz.

    print_banner()
    actions = parse_history()
    
    if not actions:
        print("Geri alınabilecek sistem işlemi bulunamadı.")
        sys.exit(0)
        
    print("Son Yapılan 10 APT İşlemi:\n")
    for i in range(min(10, len(actions))):
        a = actions[i]
        print(f"  [{i+1}] {a['date']} | {a['name']}")
        
    print("\n  [0] Çıkış (Hiçbir şey yapma)")
    
    choice = input("\nHangi hatalı işlemi iptal edip geri almak istiyorsunuz? (1-10): ").strip()
    
    if choice == '0' or not choice:
        print("Çıkış yapılıyor...")
        sys.exit(0)
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(actions) and idx < 10:
            target_action = actions[idx]
            argv = ["apt-get", target_action["revert_action"], "-y", "--"] + target_action["packages"]
            if os.geteuid() != 0:
                argv = ["sudo"] + argv
            print(f"\n⚡ Seçilen İşlem TERSİNE Çevriliyor: {' '.join(argv)}")
            confirm = input("Sistemi kurtarmaya emin misiniz? (E/H): ").strip().lower()
            if confirm == 'e':
                print("\n================== KURTARMA BAŞLIYOR ==================")
                # shell=True KULLANILMIYOR: apt geçmişinden gelen paket adları
                # katı bir regex ile doğrulanıp argv listesi olarak çalıştırılıyor,
                # böylece komut enjeksiyonu (injection) mümkün olmuyor.
                subprocess.run(argv, shell=False)

                print("=======================================================")
                print("✅ Kurtarma (Rollback) işlemi tamamlandı.")
                print("Lütfen siyah ekrandan çıkmak için sistemi yeniden başlatın: 'sudo reboot'")
            else:
                print("İptal edildi.")
        else:
            print("Geçersiz seçim.")
    except ValueError:
        print("Hatalı giriş, listedeki sayılardan birini girmelisiniz.")

if __name__ == "__main__":
    main()
