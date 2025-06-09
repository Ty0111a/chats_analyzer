import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import io
import streamlit as st

video_path = "instruction.mp4"

predefined_plugin_paths = [
    "hourly_activity.py",
    "messages_counter.py",
    "radio_silence.py",
    "reactions_per_user.py",
    "reply_network.py"
]

def create_uploaded_file_from_path(path):
    with open(path, "rb") as f:
        content = f.read()
    # Создаем объект BytesIO для имитации файла
    bytes_io = io.BytesIO(content)
    # streamlit ожидает UploadedFile с атрибутом name
    bytes_io.name = os.path.basename(path)
    return bytes_io

st.set_page_config(page_title="Анализатор чатов", layout="wide")

with st.sidebar.expander("Загрузка чатов"):
    uploaded_chats = st.file_uploader(
        "Загрузите диалог в формате JSON",
        type=["json"],
        accept_multiple_files=True,
        key="chats_uploader",
        label_visibility="visible"
    )
    if uploaded_chats and not isinstance(uploaded_chats, list):
        uploaded_chats = [uploaded_chats]

with st.sidebar.expander("Плагины"):
    uploaded_plugins = st.file_uploader(
        "Загрузите плагины",
        type=["py"],
        accept_multiple_files=True,
        key="plugins_uploader",
        label_visibility="visible"
    )
    if uploaded_plugins and not isinstance(uploaded_plugins, list):
        uploaded_plugins = [uploaded_plugins]

for path in predefined_plugin_paths:
        if os.path.exists(path):
            uploaded_plugins.append(create_uploaded_file_from_path(path))

st.sidebar.title("Диалоги для анализа")
selected_file = None
data = None

if uploaded_chats:
    file_names = [file.name for file in uploaded_chats]
    selected_name = st.sidebar.selectbox("Выберите файл для анализа", file_names)

    for file in uploaded_chats:
        if file.name == selected_name:
            selected_file = file
            break

    if selected_file:
        try:
            data = json.load(selected_file)
        except Exception as e:
            st.sidebar.error(f"Ошибка загрузки JSON: {e}")
else:
    st.sidebar.warning("Сначала загрузите файл с диалогом.")
    st.title("Анализ сообщений в telegram")
    with open(video_path, "rb") as f:
        video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode()

    # HTML с autoplay, loop и controls
    video_html = f"""
        <video width="100%" autoplay loop muted controls>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
            Ваш браузер не поддерживает тег <code>video</code>.
        </video>
    """

    st.markdown(video_html, unsafe_allow_html=True)


def get_module_name_from_path(plugin_path: str) -> str:
    # Создаём уникальное имя на основе пути
    plugin_name = os.path.basename(plugin_path).replace(".py", "")
    plugin_hash = hashlib.md5(plugin_path.encode()).hexdigest()[:8]
    return f"plugin_{plugin_name}_{plugin_hash}"


def load_and_run_plugin(plugin_path: str, data, function_name="run_plugin"):
    module_name = get_module_name_from_path(plugin_path)

    # Проверяем, не загружен ли модуль уже
    if module_name in sys.modules:
        plugin_module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None:
            st.error("Не удалось создать спецификацию плагина.")
            return
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin_module
        try:
            spec.loader.exec_module(plugin_module)
        except Exception as e:
            st.error(f"Ошибка при загрузке модуля: {e}")
            return

    if hasattr(plugin_module, function_name):
        func = getattr(plugin_module, function_name)
        try:
            func(data)
        except Exception as e:
            st.error(f"Ошибка при выполнении плагина: {e}")
    else:
        st.error(f"Функция {function_name} не найдена в плагине")


if uploaded_plugins and data:
    for plugin in uploaded_plugins:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_file:
            tmp_file.write(plugin.read())
            tmp_file_path = tmp_file.name
        st.subheader(f"Плагин: {plugin.name}")
        load_and_run_plugin(tmp_file_path, data)
elif uploaded_plugins and not data:
    st.warning("Вы загрузили плагин, но не выбрали диалог.")
