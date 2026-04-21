# 🌍 Be Kind Bot

**Be Kind** — это Telegram-бот, который помогает находить и делать простые добрые дела в реальной жизни.

Он превращает идею «хочу сделать что-то хорошее» в конкретные действия:
- что сделать  
- сколько времени нужно  
- кому это поможет  

---

## ✨ Возможности

- Поддержка языков: RU / EN / SR  
- Пошаговый сценарий:
  - выбор категории  
  - выбор времени  
  - генерация идей  
- Генерация идей через AI (Mistral)  
- Кнопка «ещё варианты»  
- Навигация назад  
- Завершение с мотивационной цитатой  

---

## 🧠 Стек

- Python 3.11  
- python-telegram-bot  
- Mistral API  
- python-dotenv  

---

## 🚀 Запуск

git clone https://github.com/YOUR_USERNAME/bekind-bot.git
cd bekind-bot

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

Создать файл .env:

TELEGRAM_TOKEN=your_token_here
MISTRAL_API_KEY=your_api_key_here

Запуск:

python bekind_bot.py