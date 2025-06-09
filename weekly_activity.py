from collections import defaultdict
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений в чате.")
        return

    # Парсим даты сообщений
    for msg in messages:
        try:
            dt = parse_date(msg['date'])
            msg['parsed_date'] = dt
            msg['date_only'] = dt.date()
        except Exception:
            msg['parsed_date'] = None
            msg['date_only'] = None

    valid_dates = [msg['date_only'] for msg in messages if msg['date_only'] is not None]
    if not valid_dates:
        st.warning("Нет валидных дат в сообщениях.")
        return

    min_date = min(valid_dates)
    max_date = max(valid_dates)

    st.subheader(f"Активность пользователей по дням в чате: {chat_name}")

    # Выбор даты начала и конца (без времени)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Начало анализа", value=min_date, min_value=min_date, max_value=max_date, key="week_start_time")
    with col2:
        end_date = st.date_input("Конец анализа", value=max_date, min_value=min_date, max_value=max_date, key="week_end_time")

    if start_date > end_date:
        st.error("Начало анализа не может быть позже конца.")
        return

    # Фильтрация сообщений по дате (включительно)
    filtered_msgs = [msg for msg in messages if msg['date_only'] is not None and start_date <= msg['date_only'] <= end_date]

    if not filtered_msgs:
        st.warning("Нет сообщений в выбранном диапазоне дат.")
        return

    # Считаем активность по дням
    user_week_counts = defaultdict(lambda: [0]*7)

    for msg in filtered_msgs:
        try:
            sender = msg['from']
            day = msg['parsed_date'].day
            shifted_day  = day % 7
            user_week_counts[sender][shifted_day] += 1
        except Exception:
            continue

    if not user_week_counts:
        st.warning("Нет данных для построения графика.")
        return

    days = list(range(7))
    week_labels = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    plt.figure(figsize=(12, 6))
    for user, counts in user_week_counts.items():
        plt.plot(days, counts, label=user, marker='o')

    plt.xticks(days, week_labels)
    plt.xlabel("День недели")
    plt.ylabel("Количество сообщений")
    plt.title("Активность пользователей по дням")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    st.pyplot(plt)
