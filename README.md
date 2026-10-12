# 👑 Mega Automation Hub — Multi-Bot 3-in-1 Control Center

Yagona portda (**Port 7777**) barcha 3 ta Telegram avtomatlashtirish botlarini birlashtiruvchi zamonaviy boshqaruv markazi:

1. ♟️ **UzChess Akademiya** (Auto-Bot v3.2)
2. 🤖 **IF-Online Bot** (@ifonlineBot)
3. 🎓 **Ibrat Academy** (MFY Onboarding & 100,000+ Checker Hub)

## Imkoniyatlar:
- **Tri-View (3 tasi bir ekranda)**: Barcha 3 tizimni yonma-yon bitta ekranda real vaqtda kuzatish va boshqarish.
- **Fokus rejimi**: Har bir tizimni to'liq ekranga yoyish (UzChess, IF-Online, Ibrat).
- **Yagona Telemetriya**: Barcha 3 botning holati, sessiyalari va statistikasi real vaqt rejimida avtomatik sinxronlanadi.
- **Favqulodda to'xtatish**: 1 ta tugma bilan barcha 3 tizim jarayonlarini to'xtatish.
- **Stream & API Reverse-Proxy**: Barcha SSE loglar, fayl yuklashlar (ZIP/Session) va eksportlar (PDF/Excel) bitta port orqali uzluksiz ishlaydi.

## Ishga tushirish:
```bash
./run.sh
```
yoki systemd xizmati orqali:
```bash
systemctl --user status multi-bot-hub.service
```
