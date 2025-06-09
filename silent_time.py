from collections import defaultdict
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def human_readable_seconds(seconds):
    """Преобразует секунды в человекочитаемый формат"""
    if seconds < 60:
        return f"{int(seconds)}с"
    elif seconds < 3600:
        return f"{int(seconds // 60)}м"
    else:
        return f"{int(seconds // 3600)}ч"


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений в чате.")
        return

    # Сортируем сообщения по дате
    messages_sorted = sorted(messages, key=lambda m: m.get('date'))

    # Собираем для каждого пользователя список времен сообщений
    user_times = defaultdict(list)
    for msg in messages_sorted:
        try:
            sender = msg['from']
            dt = parse_date(msg['date'])
            user_times[sender].append(dt)
        except Exception:
            continue

    # Вычисляем паузы между последовательными сообщениями каждого пользователя (в секундах)
    user_gaps = defaultdict(list)
    for user, times in user_times.items():
        for i in range(1, len(times)):
            delta = (times[i] - times[i - 1]).total_seconds()
            if delta > 0:
                user_gaps[user].append(delta)

    if not any(user_gaps.values()):
        st.warning("Не удалось вычислить временные паузы.")
        return

    # Определяем бины: степени двойки от 1 секунды до максимальной паузы
    max_gap = max([max(gaps) for gaps in user_gaps.values() if gaps])
    max_exp = int(np.ceil(np.log2(max_gap))) if max_gap > 0 else 10
    bins = [2 ** i for i in range(max_exp + 1)]

    st.subheader(f"Анализ временных пауз между сообщениями — чат: {chat_name}")

    all_users = list(user_gaps.keys())
    selected_users = st.multiselect("Выберите пользователей для отображения", all_users, default=all_users)

    if not selected_users:
        st.warning("Выберите хотя бы одного пользователя.")
        return

    plt.figure(figsize=(12, 6))

    for user in selected_users:
        gaps = user_gaps[user]
        counts, bin_edges = np.histogram(gaps, bins=bins)
        total = counts.sum()
        if total > 0:
            percentages = (counts / total) * 100
            percentages = np.where(percentages < 1, 0, percentages)
        else:
            percentages = counts

        bin_labels = [
            f"{human_readable_seconds(bin_edges[i])}–{human_readable_seconds(bin_edges[i + 1])}"
            for i in range(len(bin_edges) - 1)
        ]
        plt.plot(bin_labels, percentages, marker='o', label=user)

    plt.xlabel("Время паузы между сообщениями")
    plt.ylabel("Доля пауз (%)")
    plt.title("Распределение временных пауз (в процентах от общего числа пауз)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    st.pyplot(plt)

