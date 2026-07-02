"""Yeniden kullanılabilir özel widget'lar."""

from __future__ import annotations

import math

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402


_GRADE_RGB = {
    "A": (0.13, 0.77, 0.37),
    "B": (0.52, 0.80, 0.09),
    "C": (0.92, 0.70, 0.03),
    "D": (0.98, 0.45, 0.09),
    "F": (0.94, 0.27, 0.27),
}


class HealthGauge(Gtk.DrawingArea):
    """Sağlık skorunu (0-100) gösteren dairesel gösterge.

    cairo ile çizilir; herhangi bir görsel varlığa ihtiyaç duymaz.
    """

    def __init__(self, size: int = 170):
        super().__init__()
        self._score = 0          # anlık gösterilen (animasyon için)
        self._target = 0         # hedef skor
        self._grade = "F"
        self._dark = False
        self._anim_id = None
        self.set_size_request(size, size)
        self.connect("draw", self._on_draw)

    def set_value(self, score: int, grade: str, dark: bool = False) -> None:
        self._target = max(0, min(100, int(score)))
        self._grade = grade
        self._dark = dark
        # skoru hedefe doğru yumuşakça akıt
        if self._anim_id is None:
            self._anim_id = GLib.timeout_add(16, self._animate)
        self.queue_draw()

    def _animate(self) -> bool:
        diff = self._target - self._score
        if abs(diff) <= 1:
            self._score = self._target
            self.queue_draw()
            self._anim_id = None
            return False
        # her adımda farkın bir kısmını kapat (ease-out)
        self._score += diff * 0.18
        self.queue_draw()
        return True

    def _on_draw(self, _widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 14
        line_w = max(10, radius * 0.16)

        # arka plan halkası
        track = (0.20, 0.25, 0.33) if self._dark else (0.88, 0.91, 0.94)
        cr.set_line_width(line_w)
        cr.set_line_cap(1)  # ROUND
        cr.set_source_rgb(*track)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # skor yayı (tepeden saat yönünde)
        r, g, b = _GRADE_RGB.get(self._grade, (0.23, 0.51, 0.96))
        start = -math.pi / 2
        end = start + 2 * math.pi * (self._score / 100.0)
        cr.set_source_rgb(r, g, b)
        cr.arc(cx, cy, radius, start, end)
        cr.stroke()

        # ortadaki sayı
        cr.set_source_rgb(r, g, b)
        cr.select_font_face("Sans", 0, 1)  # normal, bold
        cr.set_font_size(radius * 0.62)
        text = str(int(round(self._score)))
        ext = cr.text_extents(text)
        cr.move_to(cx - ext.width / 2 - ext.x_bearing,
                   cy - ext.height / 2 - ext.y_bearing - radius * 0.06)
        cr.show_text(text)

        # "/100" alt yazısı
        muted = (0.58, 0.64, 0.72)
        cr.set_source_rgb(*muted)
        cr.set_font_size(radius * 0.20)
        sub = "/ 100"
        ext2 = cr.text_extents(sub)
        cr.move_to(cx - ext2.width / 2 - ext2.x_bearing, cy + radius * 0.42)
        cr.show_text(sub)
        return False


class TrendChart(Gtk.DrawingArea):
    """Sağlık skorunun zaman içindeki değişimini gösteren mini çizgi grafik."""

    def __init__(self, width: int = 260, height: int = 90):
        super().__init__()
        self._values: list[int] = []
        self._dark = False
        self.set_size_request(width, height)
        self.connect("draw", self._on_draw)

    def set_values(self, values: list[int], dark: bool = False) -> None:
        self._values = list(values)
        self._dark = dark
        self.queue_draw()

    def _on_draw(self, _widget, cr):
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height
        pad = 8
        grid = (0.20, 0.25, 0.33) if self._dark else (0.88, 0.91, 0.94)

        # 0-100 ekseninde referans çizgileri
        cr.set_line_width(1)
        cr.set_source_rgb(*grid)
        for frac in (0.0, 0.5, 1.0):
            y = pad + (h - 2 * pad) * frac
            cr.move_to(pad, y)
            cr.line_to(w - pad, y)
            cr.stroke()

        vals = self._values
        if len(vals) < 2:
            cr.set_source_rgb(0.58, 0.64, 0.72)
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(12)
            cr.move_to(pad + 4, h / 2)
            cr.show_text("Trend için en az 2 tarama gerekir")
            return False

        n = len(vals)
        step = (w - 2 * pad) / (n - 1)

        def pt(i, v):
            x = pad + step * i
            y = pad + (h - 2 * pad) * (1 - v / 100.0)
            return x, y

        # dolgu
        cr.set_source_rgba(0.0, 0.655, 0.616, 0.15)
        cr.move_to(pad, h - pad)
        for i, v in enumerate(vals):
            cr.line_to(*pt(i, v))
        cr.line_to(w - pad, h - pad)
        cr.close_path()
        cr.fill()

        # çizgi
        cr.set_source_rgb(0.0, 0.655, 0.616)
        cr.set_line_width(2)
        for i, v in enumerate(vals):
            x, y = pt(i, v)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()

        # son nokta
        x, y = pt(n - 1, vals[-1])
        cr.arc(x, y, 3, 0, 2 * 3.14159)
        cr.fill()
        return False


class LiveMeter(Gtk.Box):
    """Canlı yüzde göstergesi: başlık + değer + renkli ince çubuk.

    Değer, seviyeye göre renklenir (düşük=yeşil, orta=sarı, yüksek=kırmızı).
    None verilirse (ör. veri yok) çubuk gri ve '—' gösterilir.
    """

    def __init__(self, title: str, icon: str = ""):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self._percent = None
        self._dark = False

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        name = Gtk.Label(label=f"{icon} {title}".strip())
        name.set_halign(Gtk.Align.START)
        name.get_style_context().add_class("meter-title")
        head.pack_start(name, False, False, 0)
        self._value_lbl = Gtk.Label(label="—")
        self._value_lbl.set_halign(Gtk.Align.END)
        self._value_lbl.get_style_context().add_class("meter-value")
        head.pack_end(self._value_lbl, False, False, 0)
        self.pack_start(head, False, False, 0)

        self._bar = Gtk.DrawingArea()
        self._bar.set_size_request(-1, 10)
        self._bar.connect("draw", self._on_draw)
        self.pack_start(self._bar, False, False, 0)

    def set_percent(self, percent, dark: bool = False) -> None:
        self._percent = percent
        self._dark = dark
        if percent is None:
            self._value_lbl.set_text("—")
        else:
            self._value_lbl.set_text(f"%{int(round(percent))}")
        self._bar.queue_draw()

    def _on_draw(self, _widget, cr):
        alloc = self._bar.get_allocation()
        w, h = alloc.width, alloc.height
        radius = h / 2

        def rounded(x0, width, color):
            cr.set_source_rgb(*color)
            cr.arc(x0 + radius, radius, radius, math.pi / 2, 3 * math.pi / 2)
            cr.arc(x0 + width - radius, radius, radius,
                   3 * math.pi / 2, math.pi / 2)
            cr.close_path()
            cr.fill()

        track = (0.20, 0.25, 0.33) if self._dark else (0.88, 0.91, 0.94)
        rounded(0, w, track)

        if self._percent is None:
            return False
        pct = max(0.0, min(100.0, float(self._percent)))
        fill_w = max(h, w * pct / 100.0)
        if pct >= 85:
            color = (0.94, 0.27, 0.27)
        elif pct >= 65:
            color = (0.92, 0.70, 0.03)
        else:
            color = (0.13, 0.77, 0.37)
        rounded(0, fill_w, color)
        return False
