# LETR-SOL: AI 기반 예약 관리 시스템

<p align="left">
    <img alt="License" src="https://img.shields.io/badge/LICENSE-MIT-green">
</p>

여기에서는 LangGraph와 OpenAI를 활용하여 자연어 처리 기반의 지능형 예약 관리 시스템을 구현합니다. LangGraph의 Agent 기능을 활용하여 사용자의 예약 요청을 자연스럽게 처리하고, 예약 관련 상담을 수행할 수 있습니다.

## Architecture

이 프로젝트는 다음과 같은 구조로 구성되어 있습니다:

1. **LangGraph Agent**: 사용자의 자연어 요청을 처리하고 적절한 응답을 생성
2. **Supabase Database**: 예약 정보 저장 및 관리
3. **Streamlit UI**: 사용자 친화적인 웹 인터페이스 제공

## 핵심 로직 설명

### 1. LangGraph 기반 상태 관리

프로젝트는 LangGraph의 StateGraph를 활용하여 대화 상태를 관리합니다. 주요 상태 및 노드는 다음과 같습니다:

```python
class ReservState(TypedDict):
    """예약 시스템의 상태를 관리하는 클래스"""
    messages: List[Message]  # 대화 이력
    config: Dict  # 설정 정보 (전화번호, thread_id 등)
```

### 2. Graph 구조

예약 시스템의 워크플로우는 다음과 같은 노드들로 구성됩니다:

```python
def buildGraph():
    builder = StateGraph(ReservState)

    # 주요 노드 정의
    builder.add_node("first_question_router", route_question_adaptive)  # 초기 질문 라우팅
    builder.add_node("reservation_assistant", Assistant(assistant_runnable))  # 예약 처리
    builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))  # 안전한 작업
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))  # 민감한 작업
    builder.add_node("rag_assistant", rag_assistant)  # RAG 기반 응답 생성

    # 노드 간 연결 설정
    builder.add_edge(START, "first_question_router")
    builder.add_edge("safe_tools", "reservation_assistant")
    builder.add_edge("sensitive_tools", "reservation_assistant")
```

### 3. 도구(Tools) 시스템

예약 관리를 위한 도구들은 안전성에 따라 분류됩니다:

- **Safe Tools**: 기본적인 예약 정보 조회
- **Sensitive Tools**: 개인정보 관련 작업
- **RAG Tools**: 지식베이스 기반 응답 생성

### 4. Streamlit 기반 사용자 인터페이스

```python
def run_chat_interface():
    st.title("강아지 미용 예약 서비스 챗봇입니다!")

    # 사용자 입력 처리
    if prompt := st.chat_input():
        # 전화번호 확인 및 처리
        if not phone_number:
            handle_phone_number_input(prompt)

        # 예약 관련 대화 처리
        events = graph.stream({"messages": messages}, config)
        for event in events:
            handle_event(event)
```

## 주요 기능 및 구현 예시

### 1. 예약 처리 Agent

예약 요청을 처리하는 핵심 Agent의 구현 예시:

```python
def process_reservation_request(state: State) -> dict:
    """
    사용자의 예약 요청을 처리하는 함수

    Parameters:
        state (State): 현재 대화 상태 정보

    Returns:
        dict: 처리된 예약 정보

    Example:
        Input: "내일 오후 3시에 2인 테이블 예약하고 싶어요"
        Output: {
            "date": "2024-12-21",
            "time": "15:00",
            "guests": 2,
            "status": "confirmed"
        }
    """
    # 자연어 처리 및 예약 정보 추출
    extracted_info = extract_reservation_details(state.message)

    # 예약 가능 여부 확인
    if check_availability(extracted_info):
        # 예약 정보 저장
        reservation_id = save_reservation(extracted_info)
        return {"status": "success", "reservation_id": reservation_id}
    else:
        return {"status": "failed", "reason": "unavailable"}
```

### 2. 대화 관리 시스템

사용자와의 자연스러운 대화를 위한 대화 관리 시스템:

```python
class ConversationManager:
    """
    대화 흐름을 관리하고 적절한 응답을 생성하는 클래스

    주요 기능:
    - 대화 문맥 유지
    - 사용자 의도 파악
    - 적절한 응답 생성
    """
    def handle_conversation(self, user_input: str) -> str:
        # 사용자 의도 파악
        intent = self.identify_intent(user_input)

        # 의도에 따른 응답 생성
        if intent == "reservation":
            return self.handle_reservation(user_input)
        elif intent == "inquiry":
            return self.handle_inquiry(user_input)
        else:
            return self.generate_general_response(user_input)
```

## 설치 및 실행 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/letr-sol-easerve.git
cd letr-sol-easerve
```

2. 필요한 패키지 설치
```bash
pip install langchain_core langchain_openai langgraph supabase streamlit
```

3. 환경 변수 설정
```bash
export OPENAI_API_KEY="your-api-key"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

4. 실행
```bash
python3 -m my_agent.agent
```

## 프로젝트 구조

```
letr-sol-easerve/
├── csv/                    # 데이터 파일
│   └── reservation_data/   # 예약 관련 데이터
├── my_agent/              # 에이전트 관련 코드
│   ├── agent.py          # 메인 에이전트 로직
│   ├── conversation.py   # 대화 관리 시스템
│   └── database.py      # 데이터베이스 연동
├── ReservationAssistant.ipynb  # 주요 기능 구현 노트북
└── document-loader.ipynb   # 문서 로딩 관련 코드
```

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
