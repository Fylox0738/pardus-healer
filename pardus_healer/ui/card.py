"""Tek bir tanı kontrolünü gösteren kart bileşeni.

Kart tıklanabilir: başlığa tıklandığında kök neden ve öneri gibi ayrıntılar
yumuşak bir animasyonla açılıp kapanır (Gtk.Revealer).
"""

from __future__ import annotations

import subprocess
import threading
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from ..core.models import CheckResult, Fix

_BORDER_CLASSES = ("card-ok", "card-warn", "card-fail", "card-wait", "card-info-b")


class DiagnosticCard(Gtk.Box):
    """Bir kontrolün ikonunu, başlığını, durumunu ve onarım butonunu gösterir."""

    def __init__(
        self,
        check_id: str,
        icon: str,
        title: str,
        category: str,
        log_callback: Callable[[str], None],
        recheck_callback: Callable[[str], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("card")
        self.get_style_context().add_class("card-wait")

        self.check_id = check_id
        self.title_text = title
        self.log_callback = log_callback
        self.recheck_callback = recheck_callback
        self.current_fix: Optional[Fix] = None
        self.last_result: Optional[CheckResult] = None

        # ── Başlık satırı (tıklanabilir) ──
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        self.expander = Gtk.Label(label=" ")
        self.expander.get_style_context().add_class("card-expander")
        self.expander.set_size_request(14, -1)
        header.pack_start(self.expander, False, False, 0)

        self.icon_label = Gtk.Label(label=icon)
        self.icon_label.get_style_context().add_class("status-icon")
        self.icon_label.set_size_request(34, -1)
        header.pack_start(self.icon_label, False, False, 0)

        mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        head_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.get_style_context().add_class("card-title")
        head_row.pack_start(self.title_label, False, False, 0)
        self.cat_label = Gtk.Label(label=category)
        self.cat_label.get_style_context().add_class("card-cat")
        head_row.pack_start(self.cat_label, False, False, 0)
        mid.pack_start(head_row, False, False, 0)

        self.info_label = Gtk.Label(label="Bekleniyor...")
        self.info_label.set_halign(Gtk.Align.START)
        self.info_label.set_line_wrap(True)
        self.info_label.set_xalign(0.0)
        self.info_label.get_style_context().add_class("card-info")
        mid.pack_start(self.info_label, False, False, 0)
        header.pack_start(mid, True, True, 0)

        self.spinner = Gtk.Spinner()
        header.pack_start(self.spinner, False, False, 0)

        self.status_label = Gtk.Label(label="⏳")
        self.status_label.get_style_context().add_class("status-icon")
        header.pack_start(self.status_label, False, False, 0)

        self.fix_btn = Gtk.Button(label="Düzelt")
        self.fix_btn.get_style_context().add_class("fix-button")
        self.fix_btn.set_no_show_all(True)
        self.fix_btn.set_visible(False)
        self.fix_btn.connect("clicked", self._on_fix_clicked)
        header.pack_start(self.fix_btn, False, False, 0)

        # başlığı tıklanabilir yap (ayrıntıları aç/kapa)
        self._header_event = Gtk.EventBox()
        self._header_event.set_visible_window(False)
        self._header_event.add(header)
        self._header_event.connect("button-press-event", self._on_header_click)
        self.pack_start(self._header_event, False, False, 0)

        # ── Ayrıntı bölmesi (açılır) ──
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(
            Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(180)
        self.detail_label = Gtk.Label(label="")
        self.detail_label.set_halign(Gtk.Align.START)
        self.detail_label.set_xalign(0.0)
        self.detail_label.set_line_wrap(True)
        self.detail_label.set_margin_top(8)
        self.detail_label.set_margin_start(62)
        self.detail_label.get_style_context().add_class("card-detail")
        self.revealer.add(self.detail_label)
        self.pack_start(self.revealer, False, False, 0)
        self._has_detail = False

    # ---- tıklama / açılır ----
    def _on_header_click(self, _widget, _event):
        if self._has_detail:
            self.revealer.set_reveal_child(not self.revealer.get_reveal_child())
            self.expander.set_label(
                "▾" if self.revealer.get_reveal_child() else "▸")
        return False

    # ---- durum ----
    def set_checking(self) -> None:
        self.status_label.set_label("⏳")
        self.info_label.set_label("Kontrol ediliyor...")
        self._set_border("card-wait")
        self.fix_btn.set_visible(False)
        self.spinner.start()

    def update(self, result: CheckResult) -> None:
        self.spinner.stop()
        self.last_result = result
        self.current_fix = result.fix
        self.status_label.set_label(result.status.icon)
        self.info_label.set_label(result.summary)
        self._set_border(result.status.css_class)

        if result.is_actionable and result.fix is not None:
            self.fix_btn.set_label(result.fix.label)
            self.fix_btn.set_sensitive(True)
            self.fix_btn.set_visible(True)
        else:
            self.fix_btn.set_visible(False)

        # ayrıntı metnini kur
        parts = []
        if result.detail:
            parts.append(result.detail)
        if result.root_cause:
            parts.append(f"🔎 Olası neden: {result.root_cause}")
        if result.recommendation:
            parts.append(f"💡 Öneri: {result.recommendation}")
        detail_text = "\n".join(parts)
        self._has_detail = bool(detail_text)
        self.detail_label.set_label(detail_text)
        if not self._has_detail:
            self.revealer.set_reveal_child(False)
            self.expander.set_label(" ")
        else:
            self.expander.set_label(
                "▾" if self.revealer.get_reveal_child() else "▸")

    def _set_border(self, css_class: str) -> None:
        ctx = self.get_style_context()
        for c in _BORDER_CLASSES:
            ctx.remove_class(c)
        ctx.add_class(css_class)

    # ---- onarım ----
    def _on_fix_clicked(self, _widget) -> None:
        fix = self.current_fix
        if fix is None:
            return
        self.fix_btn.set_sensitive(False)
        self.log_callback(f"──▶ Çalıştırılıyor: {fix.command}")
        threading.Thread(target=self._run_fix, args=(fix,), daemon=True).start()

    def _run_fix(self, fix: Fix) -> None:
        try:
            proc = subprocess.Popen(
                fix.resolved_command(),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                if line:
                    GLib.idle_add(self.log_callback, line.rstrip())
            proc.stdout.close()
            proc.wait()
            GLib.idle_add(
                self.log_callback,
                f"İşlem tamamlandı (çıkış kodu: {proc.returncode})\n",
            )
        except Exception as exc:
            GLib.idle_add(self.log_callback, f"Hata: {exc}\n")
        finally:
            GLib.idle_add(self.recheck_callback, self.check_id)
