prefix = /usr/local

all:
	@echo "Build step completed. Run 'make install' as root."

install:
	# Dizinleri oluştur
	install -d $(DESTDIR)/opt/pardus-suite
	install -d $(DESTDIR)/usr/share/pardus-suite/assets
	install -d $(DESTDIR)/usr/share/applications
	install -d $(DESTDIR)/usr/bin
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
	# NOT: /usr/local/bin DEĞİL — Debian paketleri /usr/local'a dosya
	# koyamaz (dh_usrlocal derlemeyi durdurur); /usr/bin FHS-uyumludur.
	install -m 755 healer_rescue.py $(DESTDIR)/usr/bin/healer-rescue

	# Systemd Servisleri
	install -m 644 pardus-healer-daemon.service $(DESTDIR)/etc/systemd/system/
	install -m 644 pardus-healer-swarm.service $(DESTDIR)/etc/systemd/system/

	# PolKit Kuralı
	install -m 644 org.pardus.healer.policy $(DESTDIR)/usr/share/polkit-1/actions/

test:
	python3 -m compileall -q pardus_healer pardus_doctor tests healer_rescue.py run.py main.py main_doctor.py
	python3 -m unittest discover -s tests

deb:
	dpkg-buildpackage -us -uc -b

clean:
	rm -rf __pycache__
	rm -rf pardus_healer/__pycache__
	rm -rf pardus_doctor/__pycache__

.PHONY: all install test deb clean
