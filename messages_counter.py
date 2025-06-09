from collections import defaultdict

import streamlit as st


def run_plugin(data):
    messages = data.get("messages", [])
    if not messages:
        st.warning("Нет сообщений в чате.")
        return

    count = defaultdict(int)
    for msg in messages:
        if 'from' in msg:
            count[msg['from']] += 1

    st.write("### Количество сообщений по пользователям")
    for user, c in count.items():
        st.write(f"**{user}**: {c} сообщений")
