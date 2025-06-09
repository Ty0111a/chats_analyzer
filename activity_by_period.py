from datetime import datetime, timedelta
from collections import defaultdict

import streamlit as st
import matplotlib.pyplot as plt


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def count_words(text):
    if isinstance(text, list):
        text = ' '.join(item['text'] if isinstance(item, dict) else item for item in text)
    return len(text.split())


@st.cache_data
def preprocess_messages(messages):
    # Добавляем поле parsed_date для каждого сообщения
    for msg in messages:
        if 'parsed_date' not in msg:
            try:
                msg['parsed_date'] = parse_date(msg['date'])
            except Exception:
                msg['parsed_date'] = None
    return messages


@st.cache_data
def filter_messages(messages, start_date, end_date):
    return [msg for msg in messages if msg.get('parsed_date') and start_date <= msg['parsed_date'].date() <= end_date]


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений в чате.")
        return

    messages = preprocess_messages(messages)

    min_date = min(msg['parsed_date'].date() for msg in messages if msg.get('parsed_date'))
    max_date = max(msg['parsed_date'].date() for msg in messages if msg.get('parsed_date'))

    st.subheader(f"Анализ активности в чате: {chat_name}")

    col1, col2, col3 = st.columns(3)
    with col1:
        days_per_period = st.number_input("Длина периода в днях", min_value=1, max_value=365, value=20)
    with col2:
        start_date = st.date_input("Дата начала анализа", min_value=min_date, max_value=max_date, value=min_date)
    with col3:
        end_date = st.date_input("Дата конца анализа", min_value=min_date, max_value=max_date, value=max_date)

    if start_date > end_date:
        st.error("Ошибка: дата начала не может быть позже даты конца.")
        return

    filtered_messages = filter_messages(messages, start_date, end_date)

    if not filtered_messages:
        st.warning("Нет сообщений в выбранном периоде.")
        return

    current_period_start = datetime.combine(start_date, datetime.min.time())
    current_period_end = current_period_start + timedelta(days=days_per_period)

    period_counts = []
    while current_period_start.date() <= end_date:
        period_msgs = [
            msg for msg in filtered_messages
            if current_period_start <= msg['parsed_date'] < current_period_end
        ]
        period_counts.append(process_period(period_msgs))
        current_period_start = current_period_end
        current_period_end += timedelta(days=days_per_period)

    period_labels = []
    dt = datetime.combine(start_date, datetime.min.time())
    for _ in range(len(period_counts)):
        period_labels.append(dt)
        dt += timedelta(days=days_per_period)

    users = set()
    for period_count in period_counts:
        users.update(period_count.keys())

    data_messages = {user: [] for user in users}
    data_words = {user: [] for user in users}
    for period_count in period_counts:
        for user in users:
            data_messages[user].append(period_count.get(user, {}).get('messages', 0))
            data_words[user].append(period_count.get(user, {}).get('words', 0))

    st.pyplot(draw_activity_plot(period_labels, data_messages, data_words))


def process_period(messages):
    period_count = defaultdict(lambda: {'messages': 0, 'words': 0})
    for msg in messages:
        try:
            sender = msg['from']
            period_count[sender]['messages'] += 1
            if msg.get("media_type") != "voice_message":
                period_count[sender]['words'] += count_words(msg.get('text', ''))
        except KeyError:
            continue
    return period_count


def draw_activity_plot(period_labels, data_messages, data_words):
    fig, ax = plt.subplots(figsize=(12, 6))
    for user, counts in data_messages.items():
        ax.plot(period_labels, counts, label=f'{user} - Сообщения', marker='o')
    for user, counts in data_words.items():
        ax.plot(period_labels, counts, label=f'{user} - Слова', linestyle='--', marker='.')

    ax.set_xticks(period_labels)
    ax.set_xticklabels([dt.strftime('%Y-%m-%d') for dt in period_labels], rotation=45)

    ax.set_xlabel('Дата начала периода')
    ax.set_ylabel('Количество')
    ax.set_title('Количество сообщений и слов по пользователям')
    ax.legend()
    fig.tight_layout()
    return fig
