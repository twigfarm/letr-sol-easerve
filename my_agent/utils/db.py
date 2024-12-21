import sqlite3
from langchain_core.messages import HumanMessage, AIMessage

DB_PATH = "chat_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 채팅방(세션) 테이블
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    # 메시지 테이블
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
    )
    """
    )
    conn.commit()
    conn.close()


def get_sessions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM chat_sessions ORDER BY id ASC")
    sessions = c.fetchall()
    conn.close()
    return sessions


def get_phone_number(session_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT phone_number FROM chat_sessions WHERE id = ?", (session_id,))
    phone_number = c.fetchone()[0]
    print(f"Phone number: {phone_number}")
    conn.close()
    return phone_number


def create_session(name: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO chat_sessions (name, phone_number) VALUES (?, '')", (name,))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    if not session_id:
        raise Exception("Failed to create a new session")
    return session_id


def load_history(session_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    )
    rows = c.fetchall()
    conn.close()

    messages = []
    for role, content in rows:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


def save_message(session_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?,?,?)",
        (session_id, role, content),
    )
    conn.commit()
    conn.close()


def update_phone_number(session_id: int, phone_number: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # NOTE: f-strings로 쿼리를 작성하면 SQL Injection 공격을 당할 수 있다.
    c.execute(
        "UPDATE chat_sessions SET phone_number = ? WHERE id = ?",
        (phone_number, session_id),
    )
    conn.commit()
    conn.close()


def update_session_name(session_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE chat_sessions SET name = ? WHERE id = ?", (name, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 해당 세션의 메시지 먼저 삭제
    c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    # 세션 삭제
    c.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
