"""Kontroller sayfası: tanı kartları listesi + terminal çıktısı."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

from ..core.check import BaseCheck
from .card import DiagnosticCard


class ChecksPage(Gtk.Paned):
    """Üstte kart listesi, altta yeniden boyutlandırılabilir terminal."""

    def __init__(
        self,
        checks: list[BaseCheck],
        recheck_callback: Callable[[str], None],
        refresh_all_callback: Callable,
        report_callback: Callable,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # ── Üst: kartlar ──
        upper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        upper.set_margin_start(24)
        upper.set_margin_end(24)
        upper.set_margin_top(18)
        upper.set_margin_bottom(8)

        title = Gtk.Label(label="Sistem Kontrolleri")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        upper.pack_start(title, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        cards_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scroll.add(cards_vbox)
        upper.pack_start(scroll, True, True, 0)

        # kartları oluştur
        self.cards: dict[str, DiagnosticCard] = {}
        for check in checks:
            card = DiagnosticCard(
                check.id, check.icon, check.title, check.category,
                self.log, recheck_callback,
            )
            cards_vbox.pack_start(card, False, False, 0)
            self.cards[check.id] = card

        # buton çubuğu
        btn_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        report_btn = Gtk.Button(label="📄  Rapor Oluştur (HTML)")
        report_btn.get_style_context().add_class("report-button")
        report_btn.connect("clicked", lambda _b: report_callback())
        btn_bar.pack_start(report_btn, False, False, 0)

        refresh_btn = Gtk.Button(label="🔄  Tümünü Yeniden Kontrol Et")
        refresh_btn.get_style_context().add_class("fix-button")
        refresh_btn.connect("clicked", lambda _b: refresh_all_callback())
        btn_bar.pack_end(refresh_btn, False, False, 0)
        upper.pack_start(btn_bar, False, False, 0)

        self.pack1(upper, resize=True, shrink=False)

        # ── Alt: terminal ──
        lower = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        lower.set_margin_start(24)
        lower.set_margin_end(24)
        lower.set_margin_top(6)
        lower.set_margin_bottom(12)

        tlabel = Gtk.Label(label="Terminal Çıktısı")
        tlabel.set_halign(Gtk.Align.START)
        tlabel.get_style_context().add_class("terminal-title")
        lower.pack_start(tlabel, False, False, 0)

        term_scroll = Gtk.ScrolledWindow()
        term_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.terminal_view = Gtk.TextView()
        self.terminal_view.set_editable(False)
        self.terminal_view.set_cursor_visible(False)
        self.terminal_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.terminal_view.get_style_context().add_class("terminal-view")
        self.text_buffer = self.terminal_view.get_buffer()
        term_scroll.add(self.terminal_view)
        self.terminal_scroll = term_scroll
        lower.pack_start(term_scroll, True, True, 0)

        self.pack2(lower, resize=True, shrink=False)
        self.set_position(470)

    # ---- terminal ----
    def log(self, text: str) -> None:
        end = self.text_buffer.get_end_iter()
        self.text_buffer.insert(end, text + "\n")
        adj = self.terminal_scroll.get_vadjustment()
        GLib.idle_add(
            lambda: adj.set_value(adj.get_upper() - adj.get_page_size())
        )

    def get_card(self, check_id: str) -> DiagnosticCard | None:
        return self.cards.get(check_id)

    def set_all_checking(self) -> None:
        for card in self.cards.values():
            card.set_checking()
