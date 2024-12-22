import streamlit as st
import uuid
from .db import load_history, save_message, get_phone_number


def set_selected_session(session_id: int | None):
    st.session_state["selected_session_id"] = session_id
    if session_id is not None:
        st.session_state["messages"] = load_history(session_id)
        st.session_state.config["configurable"]["phone_number"] = get_phone_number(session_id)


def get_selected_session():
    return st.session_state.get("selected_session_id", None)


def init_session_state():
    if "selected_session_id" not in st.session_state:
        st.session_state["selected_session_id"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "config" not in st.session_state:
        thread_id = str(uuid.uuid4())
        st.session_state.config = {
            "configurable": {"phone_number": "", "thread_id": thread_id}
        }
