import streamlit as st
from langchain_core.messages import HumanMessage
from .db import (
    get_sessions,
    create_session,
    update_session_name,
    delete_session,
)
from .chat import set_selected_session, get_selected_session


def sidebar_ui():
    st.subheader("채팅방 관리")
    sessions = get_sessions()
    selected_session_id = None

    # CSS로 버튼 스타일 지정
    st.markdown(
        """
        <style>
        .stButton > button {
            width: 100%;
            margin: 0;
        }
        div[data-testid="column"] {
            padding: 0 0.2rem;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # 새 채팅방 생성 버튼
    if st.button("새 채팅방", use_container_width=True):
        new_id = create_session("")  # 빈 이름으로 채팅방 생성
        set_selected_session(new_id)
        st.rerun()

    # 채팅방 목록 표시
    if sessions:
        st.write("채팅방 목록")
        for session_id, session_name in sessions:
            # 채팅방 선택 버튼과 관리 버튼을 가로로 배치
            col1, col2, col3 = st.columns([5, 2, 2])

            # 채팅방 선택 버튼
            with col1:
                display_name = session_name if session_name.strip() else "제목 없음"
                if st.button(
                    display_name, key=f"session_{session_id}", use_container_width=True
                ):
                    selected_session_id = session_id
                    set_selected_session(session_id)
                    st.rerun()

            # 이름 변경 버튼
            with col2:
                if st.button(
                    "변경", key=f"edit_{session_id}", use_container_width=True
                ):
                    st.session_state[f"editing_{session_id}"] = True
                    st.rerun()

            # 삭제 버튼
            with col3:
                if st.button(
                    "삭제",
                    key=f"delete_{session_id}",
                    type="secondary",
                    use_container_width=True,
                ):
                    if session_id == get_selected_session():
                        set_selected_session(None)
                    delete_session(session_id)
                    st.rerun()

            # 이름 변경 입력 필드 (편집 모드일 때만 표시)
            if st.session_state.get(f"editing_{session_id}", False):
                with st.container():
                    new_name = st.text_input(
                        "새 이름", value=session_name, key=f"new_name_{session_id}"
                    )
                    col4, col5 = st.columns(2)
                    with col4:
                        if st.button(
                            "저장", key=f"save_{session_id}", use_container_width=True
                        ):
                            update_session_name(session_id, new_name or "")
                            st.session_state.pop(f"editing_{session_id}")
                            st.rerun()
                    with col5:
                        if st.button(
                            "취소", key=f"cancel_{session_id}", use_container_width=True
                        ):
                            st.session_state.pop(f"editing_{session_id}")
                            st.rerun()

    return selected_session_id



def display_messages(messages):
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"] if isinstance(msg, dict) else msg.content)


def handle_user_input():
    prompt = st.chat_input("메시지를 입력하세요.")
    return prompt
