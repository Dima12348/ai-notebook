# 📒 AI Запписник

<p align="center">
  <img src="assets/icon.png" width="128" alt="AI Записник Icon">
</p>

Настільний додаток з літаючим роботом-помічником. GTK3 + Cairo + SQLite.

<p align="center">
  <img src="assets/screenshot.png" width="600" alt="AI Записник Screenshot">
</p>

## ✨ Можливості

- 📝 **Нотатки та задачі** — категорії, пріоритети (🔴🟡🟢), статуси (📝🔄✅), теги
- 🔍 **Пошук та фільтрація** — по заголовку, тексту, тегах
- 🤖 **Літаючий робот** — літає по екрану, показує думки-нагадування
- ⏰ **Нагадування** — налаштовуваний час, системні повідомлення
- 🎨 **3 стилі робота** — Сучасний, Круглий, Піксельний
- ⚙️ **Налаштування** — колір, розмір, швидкість робота
- 💾 **Локальне зберігання** — SQLite, дані залишаються на вашому ПК

## 🚀 Запуск

```bash
cd ~/ai-notebook
chmod +x start.sh
./start.sh
```

Або напряму:

```bash
python3 main.py
```

## 🤖 Робот-помічник

<p align="center">
  <img src="assets/robot.png" width="200" alt="Jetpack Robot Assistant">
</p>

Робот з **реактивним ранцем**, який:
- 🚀 Літає по екрану з реактивними ефектами
- 💭 Показує "думки" коли спрацьовують нагадування
- 🎨 Має 3 візуальних стилі
- 🖱️ Перетягується мишкою
- ⚙️ Налаштовується: колір, розмір, швидкість

<p align="center">
  <img src="assets/robot_reminder.png" width="200" alt="Robot Reminder">
</p>

## ⏰ Нагадування

При створенні/редагуванні запису вкажіть час **"Нагадати"**:
- Формат: `РРРР-ММ-ДД ГГ:ХХ` (напр. `2026-05-07 14:30`)
- Робот покаже думку з текстом запису
- З'явиться системне повідомлення

## 📁 Структура

```
ai-notebook/
├── app/
│   ├── __init__.py
│   ├── gui.py         # Головне вікно (GTK3)
│   ├── robot.py       # Літаючий робот (Cairo)
│   ├── scheduler.py   # Планувальник нагадувань
│   └── storage.py     # SQLite база даних
├── assets/
│   ├── icon.png       # Іконка додатку
│   ├── robot.png      # Персонаж робота
│   ├── robot_reminder.png
│   ├── background.png # Фонове зображення
│   └── screenshot.png # Скріншот для README
├── data/
│   └── notebook.db    # База даних (створюється автоматично)
├── main.py            # Точка входу
├── start.sh           # Скрипт запуску
└── README.md
```

## 🛠 Технології

| Компонент | Технологія |
|-----------|------------|
| GUI | GTK 3 (PyGObject) |
| Графіка робота | Cairo 2D |
| База даних | SQLite |
| Повідомлення | libnotify |
| Мова | Python 3 |

## 📋 Вимоги

- Python 3.8+
- GTK 3 (`gir1.2-gtk-3.0`)
- PyGObject (`python3-gi`)
- Cairo (`python3-gi-cairo`)
- libnotify (`notify-send`)

Встановлення на Ubuntu/Debian:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 libnotify-bin
```

## 📄 Ліцензія

MIT
