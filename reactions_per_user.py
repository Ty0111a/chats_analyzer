from collections import defaultdict, Counter
import streamlit as st
import pandas as pd

def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений для анализа.")
        return

    st.subheader(f"Анализ реакций в чате — {chat_name}")

    # --- 1. Счётчики ---
    total_emoji_counts = Counter()            # emoji -> общее количество
    user_emoji_counts = defaultdict(Counter)  # user -> (emoji -> count)

    for msg in messages:
        for reaction in msg.get("reactions", []):
            emoji = reaction.get("emoji")
            count = reaction.get("count", 0)
            total_emoji_counts[emoji] += count

            # Используем recent для определения пользователей
            for entry in reaction.get("recent", []):
                user = entry.get("from")
                if user and emoji:
                    user_emoji_counts[user][emoji] += 1

    # --- 2. Таблица: общее количество эмодзи ---
    st.markdown("### 🔝 Самые популярные реакции")
    if total_emoji_counts:
        df_total = pd.DataFrame(total_emoji_counts.items(), columns=["Эмодзи", "Всего"])
        df_total = df_total.sort_values("Всего", ascending=False).reset_index(drop=True)
        st.dataframe(df_total)
    else:
        st.info("Нет реакций в чате.")

    # --- 3. Таблица: кто что ставил (только recent) ---
    st.markdown("### 👥 Кто какие реакции ставил (по доступным данным)")
    if user_emoji_counts:
        users = sorted(user_emoji_counts.keys())
        all_emojis = sorted({emoji for counter in user_emoji_counts.values() for emoji in counter})

        table = []
        for user in users:
            row = {"Пользователь": user}
            for emoji in all_emojis:
                row[emoji] = user_emoji_counts[user].get(emoji, 0)
            table.append(row)

        df_users = pd.DataFrame(table)
        st.dataframe(df_users.set_index("Пользователь"))
    else:
        st.info("Нет информации о пользователях, поставивших реакции.")

    # --- 4. Выбор пользователя для подробного анализа ---
    st.markdown("### 🔍 Индивидуальный анализ")
    selected_user = st.selectbox("Выберите пользователя", [""] + users)
    if selected_user:
        top_emojis = user_emoji_counts[selected_user].most_common()
        if top_emojis:
            df_user = pd.DataFrame(top_emojis, columns=["Эмодзи", "Количество"])
            st.dataframe(df_user)
        else:
            st.write("Этот пользователь не ставил реакций (или не попал в recent).")
