#!/bin/bash
echo "Pardus Suite Kuruluyor (Healer & Doctor)..."

# Bağımlılıkları Kur
sudo apt-get update
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 policykit-1 pkexec curl

# Dizinleri oluştur
sudo mkdir -p /usr/share/pardus-suite/assets
sudo mkdir -p /opt/pardus-suite
sudo mkdir -p /etc/xdg/autostart
sudo mkdir -p /usr/share/polkit-1/actions

# Dosyaları Kopyala
sudo cp -r pardus_healer pardus_doctor main.py run.py main_doctor.py healer_rescue.py /opt/pardus-suite/
sudo cp assets/*.svg /usr/share/pardus-suite/assets/

# TTY Kurtarma Modunu Sisteme Ekle (healer-rescue)
echo "Siyah Ekran Kurtarma CLI'si sisteme ekleniyor..."
sudo cp /opt/pardus-suite/healer_rescue.py /usr/local/bin/healer-rescue
sudo chmod +x /usr/local/bin/healer-rescue

# Başlatıcıları Menüye (Applications) ve Autostart'a Ekle
sudo cp pardus-healer.desktop /usr/share/applications/
sudo cp pardus-doctor.desktop /usr/share/applications/
sudo cp pardus-healer-tray.desktop /etc/xdg/autostart/
sudo chmod +x /usr/share/applications/pardus-healer.desktop
sudo chmod +x /usr/share/applications/pardus-doctor.desktop

# PolKit Kuralını Ekle
sudo cp org.pardus.healer.policy /usr/share/polkit-1/actions/

# Executable izinler
sudo chmod +x /opt/pardus-suite/main.py
sudo chmod +x /opt/pardus-suite/run.py
sudo chmod +x /opt/pardus-suite/main_doctor.py

# Systemd servislerini (Otonom Kalkan & Swarm) kur ve etkinleştir
echo "Otonom Koruma Kalkanı ve Filo Servisleri kuruluyor..."
sudo cp pardus-healer-daemon.service /etc/systemd/system/
sudo cp pardus-healer-swarm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pardus-healer-daemon.service
sudo systemctl enable pardus-healer-swarm.service
sudo systemctl start pardus-healer-daemon.service
sudo systemctl start pardus-healer-swarm.service

echo "-----------------------------------------------"
echo "✅ Pardus Suite başarıyla sisteme kuruldu!"
echo "Uygulamayı başlatıcı (Başlat) menüsünden bulabilirsiniz."
echo "Otonom Koruma Kalkanı ve Filo (Swarm) servisleri arka planda çalışıyor."
echo "-----------------------------------------------"
