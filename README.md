# LETR-SOL: AI 기반 예약 관리 시스템

- [LETR-SOL: AI 기반 예약 관리 시스템](#letr-sol-ai-기반-예약-관리-시스템)
  - [Architecture](#architecture)
  - [핵심 로직 설명](#핵심-로직-설명)
    - [1. LangGraph 기반 상태 관리](#1-langgraph-기반-상태-관리)
    - [2. Graph 구조](#2-graph-구조)
    - [3. 도구(Tools) 시스템](#3-도구tools-시스템)
    - [4. Streamlit 기반 사용자 인터페이스](#4-streamlit-기반-사용자-인터페이스)
  - [주요 기능 및 구현 예시](#주요-기능-및-구현-예시)
    - [1. Primary Agent](#1-primary-agent)
    - [2. 예약 수정, 취소 시스템](#2-예약-수정-취소-시스템)
    - [3. RAG를 활용한 가격 조회, 예약 추가 시스템](#3-rag를-활용한-가격-조회-예약-추가-시스템)
  - [추후 발전 방향](#추후-발전-방향)
    - [1. enter_node와 leave(kill)\_node 추가](#1-enter_node와-leavekill_node-추가)
    - [2. 동적 라우팅(Command)과 정적 라우팅(Edge)의 적절한 사용](#2-동적-라우팅command과-정적-라우팅edge의-적절한-사용)
    - [3. 범용성 높이기](#3-범용성-높이기)
  - [설치 및 실행 방법](#설치-및-실행-방법)
  - [프로젝트 구조](#프로젝트-구조)
  - [기여 방법](#기여-방법)
  - [라이선스](#라이선스)

<p align="left">
    <img alt="License" src="https://img.shields.io/badge/LICENSE-MIT-green">
</p>

LangGraph를 이용한 AI 기반 예약 관리 시스템입니다. LangGraph를 이용해서 자연어를 처리하고 사용자와의 대화에서 정보를 적절하게 추출합니다. LangGraph를 이용해서 LangChain을 사용했을 때보다 다양하고 유연한 대처가 가능하도록 설계했습니다.

현재는 Open AI의 "gpt-4o-mini" 모델을 사용했습니다. 추후에도 상황에 맞게 여러 LLM의 API를 적절하게 변경하여 사용할 수 있습니다.

## Architecture

이 프로젝트는 다음과 같은 구조로 구성되어 있습니다:

1. **LangGraph Agent**: 사용자의 자연어 요청을 처리하고 적절한 응답을 생성
2. **Supabase Database**: 예약 정보 저장 및 관리
3. **Streamlit UI**: 사용자 친화적인 웹 인터페이스 제공

## 핵심 로직 설명

### 1. LangGraph 기반 상태 관리

프로젝트는 LangGraph의 StateGraph를 활용하여 대화 상태를 관리합니다. 상태관리는 TypedDict로 정의되어 있는 State와 Dict 형식으로 저장되어 있는 config를 사용합니다.

State는 동적 데이터를, config는 정적 데이터를 관리합니다. State는 다음과 같은 개요를 가집니다:

```python
class ReservState(TypedDict):
    """예약 시스템의 상태를 관리하는 클래스"""
    messages: List[Message]  # 대화 이력
    user_info: str
    documents: List[str]
```

### 2. Graph 구조

예약 시스템의 워크플로우는 다음과 같은 노드들로 구성됩니다:

```python
def buildGraph():
    builder = StateGraph(ReservState)

    builder.add_node("first_question_router", route_question_adaptive)
    builder.add_node("reservation_assistant", Assistant(assistant_runnable))
    builder.add_node(
        "primary_safe_tools", create_tool_node_with_fallback(primary_safe_tools)
    )
    builder.add_node(
        "primary_sensitive_tools",
        create_tool_node_with_fallback(primary_sensitive_tools),
    )
    builder.add_node("rag_assistant", rag_assistant)
    builder.add_node("rag_safe_tools", create_tool_node_with_fallback(rag_safe_tools))
    builder.add_node(
        "rag_sensitive_tools", create_tool_node_with_fallback(rag_sensitive_tools)
    )

    builder.add_edge("primary_safe_tools", "reservation_assistant")
    builder.add_edge("primary_sensitive_tools", "reservation_assistant")
    builder.add_edge("rag_safe_tools", "rag_assistant")
    builder.add_edge("rag_sensitive_tools", "rag_assistant")
```

### 3. 도구(Tools) 시스템

예약 관리를 위한 도구들은 안전성에 따라 분류됩니다:

- **Safe Tools**: 정보를 읽는(Read) 툴. DB나 시스템에 영향을 끼치지 않습니다..
- **Sensitive Tools**: DB나 시스템에 쓰는(Write) 툴. DB나 시스템에 영향을 끼치기 때문에 Human in the loop로 처리합니다.

### 4. Streamlit 기반 사용자 인터페이스

streamlit을 기반으로 한 챗봇 인터페이스를 구축합니다.

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

### 1. Primary Agent

사용자의 요청을 받고 해당 요청을 처리할 수 있는 Agent 또는 Tool을 골라줍니다.

간단한 예약의 수정과 취소를 담당하는 경우 reservation_assistant를 사용합니다.
RAG를 이용해서 가격을 불러오고 예약을 추가하는 경우 rag_assistant를 사용합니다.
처리하려는 로직과 상관없는 질문이 들어올 수 있습니다. 이의 경우 terminate 분기로 처리되어 답변을 생성하지 않도록 합니다.:

```python
def route_question_adaptive(state: ReservState):

    latest_message = state["messages"]
    try:
        result = router_runnable.invoke({"messages": latest_message})

        datasource = result.tool

        if datasource == "reservation_assistant":
            return Command(goto="reservation_assistant")
        elif datasource == "rag_assistant":
            return Command(goto="rag_assistant")
        else:
            return Command(goto=END)
    except Exception as e:
        return Command(goto=END)
```

### 2. 예약 수정, 취소 시스템

사용자 예약의 수정과 취소를 간단하게 처리할 수 있는 관리 시스템 입니다.:

```python
class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: ReservState, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state, config=config)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                # 설명 필요
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
```

### 3. RAG를 활용한 가격 조회, 예약 추가 시스템

사용자 예약 추가를 RAG와 결합하여 가격 정보와 함께 처리할 수 있는 관리 시스템 입니다. 구현 방향성은 2번과 같이 assistant가 tool을 호출하고 이를 ToolNode가 처리하는 방식으로 구현되어 있습니다.

## 향후 발전 방향

### 1. enter_node와 leave(kill)\_node 추가

Primairy Assistant와 Sub Assistant로 나뉘고 LangGraph 특성상의 복잡도로 LLM의 인지 정확도 하락 문제 발생.

이를 enter_node와 leave_node 로 나누어 현재의 위치와 Stack을 정확하게 알려주는 방법 추가.

### 2. 동적 라우팅(Command)과 정적 라우팅(Edge)의 적절한 사용

동적 라우팅은 Node에서 분기를 처리하며 통일된 코드 양식을 보여주고 동적으로 라우팅이 가능토록 하지만, Node 내부의 복잡도가 증가한다.

이에 이를 적절하게 조화하여 사용할 필요가 있다.

### 3. 범용성 높이기

현재는 도메인/직군에만 사용이 가능한 폐쇄적 형태를 이루고 있지만 모듈화를 통한 오픈소스화 필요

### 4. 클라이언트 사이드와 결합

<p align="left">
  <img src="https://github.com/user-attachments/assets/ff78e669-f7df-4250-97f4-cabc02417232" align="left">
  <img src="https://github.com/user-attachments/assets/ff78e669-f7df-4250-97f4-cabc02417232" align="left">
</p>
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
letr-sol-easerve/my_agent/
├── agent.py                # agent의 시작점
└── utils/
    ├── __init__.py
    ├── embedding.py        # UPSTAGE 임베딩
    ├── grade_doc.py        # retrieval grader, 문서의 관련성 보장
    ├── nodes.py            # langGraph를 구성하는 Node 모음
    ├── rpc.py              # supabase와 소통하는 rpc 모음
    ├── runnables.py
    ├── state.py
    ├── supabase_client.py
    ├── tools/              # Agent가사용하는 tools 모음
    │   ├── rag.py
    │   ├── reservation.py
    │   ├── tools_prompt.py
    │   └── user.py
    ├── utils.py
    └── vector_db.py
```

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
