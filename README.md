# opencode-free-models-watcher

مراقب يبلّغك على تليجرام كل ما يظهر نموذج **مجاني** جديد في [opencode.ai/zen](https://opencode.ai/zen) (أو يختفي واحد موجود). شغّال على GitHub Actions كل 4 ساعات — مفيش سيرفر، مفيش اعتماد على جهازك.

## اللي بيعمله

1. يجيب قائمة النماذج من `https://opencode.ai/zen/v1/models`
2. ياخد اللي اسمه بيخلص/فيه `-free`
3. يقارنه بـ `known_free_models.json` (المحفوظ في الريبو)
4. لو فيه جديد أو متمسح → رسالة على تليجرام، والقائمة المحفوظة تتحدّث لوحدها

## التشغيل اليدوي

```bash
# محليًا (اختياري)
python watch.py

# أو من GitHub: Actions tab → Check free models → Run workflow
```

## الإعداد (أول مرة)

1. **Secrets** — في الريبو: Settings → Secrets and variables → Actions → New repository secret
   - `TELEGRAM_TOKEN` — توكن البوت بتاعك
   - `TELEGRAM_CHAT_ID` — رقم الشات بتاعك
2. **فعّل الـ workflow** — Actions tab → اختار `Check free models` → Enable

المرة الأولى بتحفظ القائمة الحالية كأساس من غير ما تبعتلك رسايل.

## ملاحظات

- الجدولة بتاعة GitHub بتتأخر شوية أحيانًا (دقايق)، فمش دقيقة للساعة.
- الـ cron بتاع GitHub بتوقيت **UTC**؛ `0 */4 * * *` يعني كل 4 ساعات من منتصف الليل UTC.
- الحالة (`known_free_models.json`) بتتعمل لها commit لوحدها في كل تغيير — دي ذاكرة المراقب.
