from datetime import datetime
import streamlit as st
import pandas as pd


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def human_readable_duration(seconds):
    """Форматирует длительность в часы и минуты"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours and minutes:
        return f"{hours}ч {minutes}м"
    elif hours:
        return f"{hours}ч"
    elif minutes:
        return f"{minutes}м"
    else:
        return f"{int(seconds)}с"


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений в чате.")
        return

    st.subheader(f"Длинные паузы в чате — {chat_name}")
    st.markdown("Будут показаны периоды, когда **никто не писал более 30 часов**.")

    # Сортируем сообщения по времени
    messages_sorted = sorted(messages, key=lambda m: m.get("date"))

    # Извлекаем все временные метки
    timestamps = []
    for msg in messages_sorted:
        try:
            dt = parse_date(msg["date"])
            timestamps.append(dt)
        except Exception:
            continue

    if len(timestamps) < 2:
        st.warning("Недостаточно сообщений для анализа.")
        return

    # Анализируем интервалы между сообщениями
    SILENCE_THRESHOLD = 30 * 3600  # 30 часов в секундах
    silence_periods = []

    for i in range(1, len(timestamps)):
        prev_time = timestamps[i - 1]
        curr_time = timestamps[i]
        delta = (curr_time - prev_time).total_seconds()

        if delta >= SILENCE_THRESHOLD:
            silence_periods.append({
                "Начало": prev_time.strftime("%Y-%m-%d %H:%M"),
                "Конец": curr_time.strftime("%Y-%m-%d %H:%M"),
                "Длительность": human_readable_duration(delta),
                "Секунд": int(delta)
            })

    if not silence_periods:
        st.success("В чате не было пауз дольше 30 часов. Все активно!")
        return

    # Сортируем по длительности (по убыванию)
    silence_periods.sort(key=lambda p: p["Секунд"], reverse=True)

    # Выводим таблицу
    df = pd.DataFrame(silence_periods)
    df_display = df.drop(columns=["Секунд"])
    st.dataframe(df_display)

    # Показываем количество найденных пауз
    st.info(f"Найдено пауз: {len(df)}")
