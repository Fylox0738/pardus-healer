"""Kural (korelasyon) motoru — projenin "akıllı" çekirdeği.

Tekil kontrol sonuçlarına ayrı ayrı bakmak yerine, aralarındaki neden-sonuç
ilişkilerini kurar. Örneğin disk doluysa APT'nin başarısız olması bir
"sonuç"tur; asıl çözülmesi gereken "neden" disktir. Motor bunları tespit
edip önceliklendirilmiş içgörüler (Insight) üretir.

Her kural saf bir fonksiyondur: sonuç sözlüğünü alır, uyarsa bir Insight
döndürür, uymazsa None. Böylece yeni kural eklemek tek fonksiyon yazmaktır.
"""

from __future__ import annotations

from typing import Callable, Optional

from .models import CheckResult, Fix, Insight, Status

# result sözlüğü: check_id -> CheckResult
ResultMap = dict[str, CheckResult]
Rule = Callable[[ResultMap], Optional[Insight]]

_RULES: list[Rule] = []


def rule(func: Rule) -> Rule:
    """Bir fonksiyonu kural olarak kaydeden dekoratör."""
    _RULES.append(func)
    return func


def _is(res: ResultMap, cid: str, *statuses: Status) -> bool:
    r = res.get(cid)
    return r is not None and r.status in statuses


# ─────────────────────────────────────────────────────────
#  KURALLAR
# ─────────────────────────────────────────────────────────

@rule
def disk_full_breaks_apt(res: ResultMap) -> Optional[Insight]:
    """Disk dolu + APT/güncelleme sorunlu → asıl neden disktir."""
    if _is(res, "disk", Status.FAIL) and (
        _is(res, "apt_health", Status.FAIL)
        or _is(res, "broken_packages", Status.FAIL)
        or _is(res, "updates", Status.FAIL, Status.WARN)
    ):
        return Insight(
            title="Kök neden: Disk dolu",
            message="Disk kritik seviyede dolu olduğu için paket işlemleri "
            "(APT/güncelleme) başarısız oluyor. Önce disk temizlenmeli; "
            "diğer paket sorunları büyük ihtimalle bunun sonucudur.",
            severity=Status.FAIL,
            priority=95,
            related=["disk", "apt_health", "broken_packages", "updates"],
            suggested_fix=Fix(
                "Diski Temizle",
                "pkexec sh -c 'apt-get clean && apt-get autoremove -y'",
                needs_root=True,
                description="Paket işlemleri için yer açar.",
            ),
        )
    return None


@rule
def no_internet_blocks_updates(res: ResultMap) -> Optional[Insight]:
    """İnternet yok → güncelleme/depo kontrolleri güvenilmezdir."""
    if _is(res, "internet", Status.FAIL):
        affected = [
            cid for cid in ("apt_health", "updates", "security_updates", "dns")
            if _is(res, cid, Status.FAIL, Status.WARN, Status.UNKNOWN)
        ]
        if affected:
            return Insight(
                title="Kök neden: İnternet yok",
                message="İnternet bağlantısı olmadığı için depo ve güncelleme "
                "kontrolleri güvenilir sonuç veremez. Önce bağlantıyı düzeltin, "
                "sonra bu kontrolleri tekrar çalıştırın.",
                severity=Status.FAIL,
                priority=90,
                related=["internet"] + affected,
                suggested_fix=res["internet"].fix,
            )
    return None


@rule
def broken_before_upgrade(res: ResultMap) -> Optional[Insight]:
    """Bozuk paket varken güncelleme yapmak riskli."""
    if _is(res, "broken_packages", Status.FAIL) and _is(
        res, "updates", Status.WARN, Status.FAIL
    ):
        return Insight(
            title="Sıralama önemli: Önce bozuk paketleri düzelt",
            message="Bozuk paketler varken güncelleme yapmak durumu "
            "kötüleştirebilir. Önce bozuk paketleri onarın, ardından "
            "güncellemeleri kurun.",
            severity=Status.WARN,
            priority=70,
            related=["broken_packages", "updates"],
            suggested_fix=res["broken_packages"].fix,
        )
    return None


@rule
def security_updates_priority(res: ResultMap) -> Optional[Insight]:
    """Bekleyen güvenlik güncellemesi her zaman yüksek öncelikli."""
    if _is(res, "security_updates", Status.FAIL):
        return Insight(
            title="Güvenlik önceliği: Yamalar bekliyor",
            message="Sisteminizde bekleyen güvenlik güncellemeleri var. Bunlar "
            "bilinen açıkları kapatır ve diğer güncellemelerden önce kurulmalıdır.",
            severity=Status.FAIL,
            priority=85,
            related=["security_updates"],
            suggested_fix=res["security_updates"].fix,
        )
    return None


@rule
def high_load_high_temp(res: ResultMap) -> Optional[Insight]:
    """Yüksek CPU yükü + yüksek sıcaklık birlikte → termal risk."""
    if _is(res, "cpu_load", Status.FAIL, Status.WARN) and _is(
        res, "cpu_temp", Status.FAIL, Status.WARN
    ):
        return Insight(
            title="Termal risk: Yük ve sıcaklık birlikte yüksek",
            message="CPU hem yüksek yük altında hem de ısınmış durumda. Yükü "
            "azaltmak sıcaklığı da düşürecektir; sık yaşanıyorsa soğutmayı "
            "kontrol edin.",
            severity=Status.WARN,
            priority=65,
            related=["cpu_load", "cpu_temp"],
        )
    return None


@rule
def ram_full_uses_swap(res: ResultMap) -> Optional[Insight]:
    """RAM dolu + swap yüksek → bellek darboğazı."""
    if _is(res, "ram", Status.WARN, Status.FAIL) and _is(
        res, "swap", Status.WARN, Status.FAIL
    ):
        return Insight(
            title="Bellek darboğazı",
            message="RAM dolduğu için sistem takas alanını yoğun kullanıyor; "
            "bu belirgin yavaşlamaya yol açar. Bellek tüketen uygulamaları "
            "kapatmak en hızlı çözümdür.",
            severity=Status.WARN,
            priority=60,
            related=["ram", "swap"],
        )
    return None


@rule
def exposed_ports_no_firewall(res: ResultMap) -> Optional[Insight]:
    """Riskli portlar dışa açık + güvenlik duvarı etkin değil → yüksek risk."""
    fw = res.get("firewall")
    fw_off = fw is not None and fw.status in (Status.WARN, Status.INFO)
    if _is(res, "open_ports", Status.WARN) and fw_off:
        return Insight(
            title="Güvenlik riski: Açık portlar korumasız",
            message="Riskli servisler dış dünyaya açıkken güvenlik duvarı "
            "etkin değil. Bu, saldırı yüzeyini ciddi biçimde büyütür. Önce "
            "güvenlik duvarını açın, ardından gereksiz servisleri kapatın.",
            severity=Status.FAIL,
            priority=88,
            related=["open_ports", "firewall"],
            suggested_fix=fw.fix if fw is not None else None,
        )
    return None


@rule
def no_auto_updates_with_pending(res: ResultMap) -> Optional[Insight]:
    """Otomatik güncelleme kapalı + bekleyen güvenlik yaması → öneri."""
    if _is(res, "auto_updates", Status.WARN) and _is(
        res, "security_updates", Status.FAIL
    ):
        return Insight(
            title="Güncel kalmıyorsunuz",
            message="Bekleyen güvenlik güncellemeleri var ve otomatik "
            "güncelleme kapalı. Otomatik güvenlik güncellemelerini açmak, "
            "sistemin ileride de güncel kalmasını sağlar.",
            severity=Status.WARN,
            priority=68,
            related=["auto_updates", "security_updates"],
            suggested_fix=res["auto_updates"].fix,
        )
    return None


# ─────────────────────────────────────────────────────────

def evaluate(results: list[CheckResult]) -> list[Insight]:
    """Tüm kuralları çalıştırıp içgörüleri öncelik sırasına göre döndürür."""
    res_map: ResultMap = {r.check_id: r for r in results}
    insights: list[Insight] = []
    for r in _RULES:
        try:
            ins = r(res_map)
        except Exception:
            ins = None
        if ins is not None:
            insights.append(ins)
    insights.sort(key=lambda i: i.priority, reverse=True)
    return insights
