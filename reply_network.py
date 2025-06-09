from collections import defaultdict
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Чат")

    if not messages:
        st.warning("Нет сообщений для анализа.")
        return

    st.subheader(f"Сетевой анализ взаимодействий — {chat_name}")

    # Собираем всех участников
    participants = sorted(set(msg.get("from") for msg in messages if msg.get("from")))
    if not participants:
        st.warning("Не удалось определить участников.")
        return

    # Интерфейс выбора пользователей
    selected_users = st.multiselect("Выберите пользователей для анализа", participants, default=participants)
    if not selected_users:
        st.info("Выберите хотя бы одного пользователя.")
        return

    # Карта: ID сообщения → отправитель
    id_to_user = {}
    for msg in messages:
        msg_id = msg.get("id")
        sender = msg.get("from")
        if msg_id is not None and sender in selected_users:
            id_to_user[msg_id] = sender

    # Подсчёт взаимодействий (ответов)
    interaction_counts = defaultdict(lambda: defaultdict(int))
    for msg in messages:
        sender = msg.get("from")
        reply_id = msg.get("reply_to_message_id")

        if sender in selected_users and reply_id:
            replied_user = id_to_user.get(reply_id)
            if replied_user and replied_user in selected_users and replied_user != sender:
                interaction_counts[sender][replied_user] += 1

    if not interaction_counts:
        st.info("Нет ответов между выбранными пользователями.")
        return

    # Построение графа
    G = nx.DiGraph()
    for sender, replies in interaction_counts.items():
        for receiver, count in replies.items():
            G.add_edge(sender, receiver, weight=count)

    plt.figure(figsize=(10, 8))
    pos = nx.circular_layout(G)
    # pos = nx.spring_layout(G, seed=42)
    raw_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(raw_weights)
    min_weight = min(raw_weights)

    # Избегаем деления на ноль
    if max_weight == min_weight:
        edge_weights = [2 for _ in raw_weights]
    else:
        edge_weights = [1 + 4 * (w - min_weight) / (max_weight - min_weight) for w in raw_weights]

    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=2000,
            font_size=10, arrows=True, width=edge_weights)

    edge_labels = {(u, v): G[u][v]['weight'] for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)

    plt.title("Кто кому отвечает (среди выбранных пользователей)", fontsize=14)
    st.pyplot(plt)
