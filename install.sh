#!/bin/bash
echo "Pardus Suite Kuruluyor (Healer & Doctor)..."

# Bağımlılıkları Kur
sudo apt-get update
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 pkexec curl

# Dizinleri oluştur
sudo mkdir -p /usr/share/pardus-suite/assets
sudo mkdir -p /opt/pardus-suite

# Dosyaları Kopyala
sudo cp -r pardus_healer pardus_doctor main.py run.py main_doctor.py healer_rescue.py /opt/pardus-suite/
sudo cp assets/*.svg /usr/share/pardus-suite/assets/

# TTY Kurtarma Modunu Sisteme Ekle (healer-rescue)
echo "Siyah Ekran Kurtarma CLI'si sisteme ekleniyor..."
sudo cp /opt/pardus-suite/healer_rescue.py /usr/local/bin/healer-rescue
sudo chmod +x /usr/local/bin/healer-rescue

# Başlatıcıları Menüye (Applications) Ekle
sudo cp pardus-healer.desktop /usr/share/applications/
sudo cp pardus-doctor.desktop /usr/share/applications/
sudo chmod +x /usr/share/applications/pardus-healer.desktop
sudo chmod +x /usr/share/applications/pardus-doctor.desktop

# Executable izinler
sudo chmod +x /opt/pardus-suite/main.py
sudo chmod +x /opt/pardus-suite/run.py
sudo chmod +x /opt/pardus-suite/main_doctor.py

echo "-----------------------------------------------"
echo "✅ Pardus Suite başarıyla sisteme kuruldu!"
echo "Uygulamayı başlatıcı (Başlat) menüsünden bulabilirsiniz."
echo "-----------------------------------------------"
