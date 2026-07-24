#!/usr/bin/env python3
import gi
import signal
import sys
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Ekosistemdeki ikinci uygulamayı Doctor üzerinden yükle
from pardus_doctor.ui.app import DoctorApp

def main():
    # Ctrl+C komutlarını terminalde temiz kapatmak için
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = DoctorApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    
    Gtk.main()

if __name__ == "__main__":
    sys.exit(main())
