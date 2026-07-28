prefix = /usr/local

all:
	@echo "Build step completed. Run 'make install' as root."

install:
	# Dizinleri oluştur
	install -d $(DESTDIR)/opt/pardus-suite
	install -d $(DESTDIR)/usr/share/pardus-suite/assets
	install -d $(DESTDIR)/usr/share/applications
	install -d $(DESTDIR)/usr/local/bin
	install -d $(DESTDIR)/etc/systemd/system
	install -d $(DESTDIR)/usr/share/polkit-1/actions
	install -d $(DESTDIR)/etc/xdg/autostart

	# Python dosyalarını ve modülleri kopyala
	cp -r pardus_healer pardus_doctor main.py run.py main_doctor.py healer_rescue.py $(DESTDIR)/opt/pardus-suite/
	cp assets/*.svg $(DESTDIR)/usr/share/pardus-suite/assets/

	# Çalıştırılabilir izinler
	chmod +x $(DESTDIR)/opt/pardus-suite/main.py
	chmod +x $(DESTDIR)/opt/pardus-suite/run.py
	chmod +x $(DESTDIR)/opt/pardus-suite/main_doctor.py

	# Masaüstü başlatıcıları
	install -m 644 pardus-healer.desktop $(DESTDIR)/usr/share/applications/
	install -m 644 pardus-doctor.desktop $(DESTDIR)/usr/share/applications/
	
	# Görev Çubuğu (Tray) Otonom Başlatıcı
	install -m 644 pardus-healer-tray.desktop $(DESTDIR)/etc/xdg/autostart/

	# CLI Kurtarma Aracı
	install -m 755 healer_rescue.py $(DESTDIR)/usr/local/bin/healer-rescue

	# Systemd Servisleri
	install -m 644 pardus-healer-daemon.service $(DESTDIR)/etc/systemd/system/
	install -m 644 pardus-healer-swarm.service $(DESTDIR)/etc/systemd/system/

	# PolKit Kuralı
	install -m 644 org.pardus.healer.policy $(DESTDIR)/usr/share/polkit-1/actions/

clean:
	rm -rf __pycache__
	rm -rf pardus_healer/__pycache__
	rm -rf pardus_doctor/__pycache__
