#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neon Synth Telegram Bot — один файл.

Что делает бот:
- по команде /start отправляет кнопку "🎹 Запустить Neon Synth";
- кнопка открывает ваш Mini App с пианино, размещенный на GitHub Pages;
- дополнительно пытается поставить кнопку меню бота "Запустить";
- работает без сторонних Python-библиотек, только стандартная библиотека.

Как запустить:
1) Получите токен у @BotFather.
2) Загрузите пианино на GitHub Pages и получите HTTPS-ссылку.
3) Вставьте токен и ссылку ниже ИЛИ используйте переменные окружения:
   Windows CMD:
      set TELEGRAM_BOT_TOKEN=123456:AB
      set MINI_APP_URL=https://username.github.io/NeonSynth/
      python neon_synth_bot.py

   PowerShell:
      $env:TELEGRAM_BOT_TOKEN="123456:ABC..."
      $env:MINI_APP_URL="https://username.github.io/NeonSynth/"
      python neon_synth_bot.py
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


# ==========================
# НАСТРОЙКИ
# ==========================

# Лучше хранить токен в переменной окружения TELEGRAM_BOT_TOKEN.
# Но можно временно вставить токен прямо сюда:
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or "8676785923:AAGIMozJQun8NQwl-RVVhrVsYv7NYe28ZPQ"

# Сюда вставьте ссылку на ваш GitHub Pages с index.html.
# Пример: https://yourname.github.io/NeonSynth/
MINI_APP_URL = os.getenv("MINI_APP_URL", "").strip() or "https://man970934-create.github.io/neonsynth/"

BOT_NAME = "Neon Synth"
START_TEXT = (
    "🎹 <b>Neon Synth Simulator</b>\n\n"
    "Неоновое пианино и синтезатор прямо в Telegram.\n"
    "Играй ноты, повторяй мелодии, проходи уровни и создавай свой звук.\n\n"
    "Нажми кнопку ниже, чтобы запустить мини-приложение."
)


# ==========================
# БАЗОВЫЕ ФУНКЦИИ TELEGRAM API
# ==========================

def api_url(method: str) -> str:
    """Создает URL для метода Telegram Bot API."""
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


def tg_request(method: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
    """Отправляет POST-запрос в Telegram Bot API."""
    payload = payload or {}
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        api_url(method),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[Telegram HTTP Error] {exc.code}: {body}")
        return {"ok": False, "error": body}
    except Exception as exc:
        print(f"[Request Error] {method}: {exc}")
        return {"ok": False, "error": str(exc)}


def get_updates(offset: Optional[int] = None, timeout: int = 50) -> Dict[str, Any]:
    """Получает новые сообщения через long polling."""
    payload: Dict[str, Any] = {
        "timeout": timeout,
        "allowed_updates": ["message", "callback_query"],
    }
    if offset is not None:
        payload["offset"] = offset

    return tg_request("getUpdates", payload, timeout=timeout + 10)


def send_start_message(chat_id: int) -> None:
    """Отправляет приветствие и кнопку запуска Mini App."""
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🎹 Запустить Neon Synth",
                    "web_app": {"url": MINI_APP_URL},
                }
            ],
            [
                {
                    "text": "🌐 Открыть в браузере",
                    "url": MINI_APP_URL,
                }
            ],
        ]
    }

    tg_request(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": START_TEXT,
            "parse_mode": "HTML",
            "reply_markup": keyboard,
        },
    )


def send_help_message(chat_id: int) -> None:
    """Отправляет короткую справку."""
    text = (
        "ℹ️ <b>Как играть</b>\n\n"
        "1. Нажми <b>Запустить Neon Synth</b>.\n"
        "2. Откроется мини-приложение с пианино.\n"
        "3. Играй мышью, тачем или клавиатурой компьютера.\n\n"
        "Если кнопка не открывается, проверь, что ссылка MINI_APP_URL начинается с https://"
    )
    tg_request(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        },
    )


def set_bot_menu_button() -> None:
    """
    Ставит кнопку меню в Telegram.
    Она появится рядом с полем ввода, если клиент Telegram поддерживает Web Apps.
    """
    result = tg_request(
        "setChatMenuButton",
        {
            "menu_button": {
                "type": "web_app",
                "text": "Запустить",
                "web_app": {"url": MINI_APP_URL},
            }
        },
    )

    if result.get("ok"):
        print("[OK] Menu button set.")
    else:
        print("[WARN] Could not set menu button:", result)


def validate_settings() -> None:
    """Проверяет, что токен и URL заполнены."""
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("Ошибка: укажите токен бота.")
        print("Вариант 1: вставьте токен в переменную BOT_TOKEN внутри файла.")
        print("Вариант 2: задайте TELEGRAM_BOT_TOKEN в переменных окружения.")
        sys.exit(1)

    if "YOUR_USERNAME" in MINI_APP_URL or "YOUR_REPOSITORY" in MINI_APP_URL or not MINI_APP_URL:
        print("Ошибка: укажите ссылку на Mini App.")
        print("Вставьте HTTPS-ссылку GitHub Pages в MINI_APP_URL.")
        print("Пример: https://username.github.io/NeonSynth/")
        sys.exit(1)

    parsed = urllib.parse.urlparse(MINI_APP_URL)
    if parsed.scheme != "https":
        print("Ошибка: MINI_APP_URL должен начинаться с https://")
        print("GitHub Pages подходит, потому что он использует HTTPS.")
        sys.exit(1)


# ==========================
# ОБРАБОТКА СООБЩЕНИЙ
# ==========================

def handle_message(message: Dict[str, Any]) -> None:
    """Обрабатывает входящее сообщение."""
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if chat_id is None:
        return

    if text.startswith("/start"):
        send_start_message(chat_id)
    elif text.startswith("/help"):
        send_help_message(chat_id)
    else:
        send_start_message(chat_id)


def run_bot() -> None:
    """Основной цикл long polling."""
    validate_settings()

    print(f"[OK] {BOT_NAME} bot started.")
    print(f"[OK] Mini App URL: {MINI_APP_URL}")

    # Не критично, если Telegram не разрешит поставить menu button.
    set_bot_menu_button()

    offset: Optional[int] = None

    while True:
        updates = get_updates(offset=offset)

        if not updates.get("ok"):
            print("[WARN] getUpdates failed. Retry in 3 seconds.")
            time.sleep(3)
            continue

        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "message" in update:
                handle_message(update["message"])

        time.sleep(0.2)


if __name__ == "__main__":
    run_bot()
