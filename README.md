# notebooklm-mcp

Google NotebookLM을 MCP(Model Context Protocol) 서버로 래핑하여 AI 에이전트의 **리서치 도구**, **RAG 백엔드**, **콘텐츠 생성 파이프라인**으로 활용할 수 있게 해주는 프로젝트입니다.

```
[Claude Code / AI Agent] <--MCP--> [notebooklm-mcp] <--async API--> [Google NotebookLM]
```

> **비공식 API 기반** — [notebooklm-py](https://github.com/teng-lin/notebooklm-py)를 사용합니다.
> Google 내부 API가 변경되면 동작이 중단될 수 있습니다. 리서치/개인 프로젝트 용도에 적합합니다.

---

## 주요 기능

### RAG Q&A
소스(URL, PDF, YouTube 등)를 노트북에 추가하고, AI 에이전트가 소스 기반 질의응답을 수행합니다.
NotebookLM이 인덱싱한 소스에서 인용과 함께 답변을 제공합니다.

### 자동 리서치 파이프라인
주제를 입력하면 노트북 생성 → 웹 리서치 → 소스 자동 추가 → 분석 → 리포트 생성까지 한 번에 실행합니다.

### 콘텐츠 생성
팟캐스트(오디오), 비디오, 슬라이드, 퀴즈, 플래시카드, 인포그래픽, 마인드맵, 데이터 테이블, 리포트 등 NotebookLM Studio의 모든 콘텐츠 타입을 생성하고 다운로드합니다.

### 범용 플러그인
MCP 프로토콜을 지원하므로 Claude Code뿐 아니라 다른 MCP 클라이언트(웹 UI, 다른 AI 도구)에서도 연동 가능합니다.

---

## 요구사항

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- Google 계정 (NotebookLM 접근)
- 시스템에 Chrome 브라우저 설치 (로그인용)

---

## 설치

```bash
# 1. 레포 클론
git clone https://github.com/<your-org>/research-notebooklm-mcp.git
cd research-notebooklm-mcp

# 2. 의존성 설치
uv sync

# 3. Playwright 브라우저 설치
uv run playwright install chromium
```

---

## 인증 (최초 1회)

NotebookLM은 Google 계정 인증이 필요합니다. 브라우저에서 로그인한 뒤 세션을 저장합니다.

```bash
# 시스템 Chrome을 사용하는 로그인 스크립트 (Playwright Chromium 크래시 우회)
uv run python scripts/login.py
```

1. Chrome 브라우저가 열리면 Google 계정으로 로그인
2. NotebookLM 홈페이지가 보이면 터미널에서 **Enter** 입력
3. `~/.notebooklm/storage_state.json`에 인증 정보 저장

> 인증 토큰이 만료되면 같은 명령으로 재인증하면 됩니다.

### 인증 확인

```bash
uv run python -c "
import asyncio
from notebooklm import NotebookLMClient

async def check():
    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        print(f'Connected! {len(notebooks)} notebooks found.')

asyncio.run(check())
"
```

---

## Claude Code 연동

### MCP 서버 등록

```bash
claude mcp add notebooklm-research \
  -- uv run --directory /path/to/research-notebooklm-mcp \
  python -m notebooklm_mcp.server
```

### 연동 확인

```bash
claude mcp list
# notebooklm-research: ... - ✓ Connected
```

등록 후 Claude Code를 새로 시작하면 31개의 NotebookLM 도구를 자연어로 사용할 수 있습니다.

---

## 사용 예시

### 1. 소스 기반 Q&A (RAG)

```
사용자: "이 3개 URL의 핵심 차이점을 분석해줘"

Claude Code:
  → notebook_create("URL 비교 분석")
  → source_add_url(nb_id, "https://...")  x 3
  → chat_ask(nb_id, "세 소스의 핵심 차이점을 비교 분석해줘")
  → 인용 포함된 구조화된 답변 반환
```

### 2. 자동 리서치 파이프라인

```
사용자: "LLM fine-tuning 최신 트렌드 리서치해줘"

Claude Code:
  → research_pipeline(
      topic="LLM fine-tuning 2026 trends",
      web_research=True,
      research_mode="deep",
      generate_report=True
    )
  → 노트북 생성 → 웹 리서치 → 소스 자동 추가 → 요약 → 리포트 생성
  → 최종 리포트를 사용자에게 반환
```

### 3. 기존 노트북에 질문

```
사용자: "RHCSA 시험 준비 노트북에서 SELinux 관련 내용 정리해줘"

Claude Code:
  → notebook_list()  // 기존 노트북 확인
  → chat_ask(nb_id, "SELinux 설정과 트러블슈팅 방법을 정리해줘")
```

### 4. 콘텐츠 생성

```
사용자: "이 리서치 내용으로 팟캐스트 만들어줘"

Claude Code:
  → generate_audio(nb_id, instructions="핵심 내용을 대화 형식으로", language="ko")
  → download_artifact(nb_id, "audio", "./podcast.mp3")
```

### 5. MCP Prompt 활용

Claude Code에서 MCP 프롬프트를 사용하여 가이드된 워크플로우를 실행할 수 있습니다:

- `research_deep_dive` — 주제별 심층 리서치 세션
- `comparative_analysis` — 여러 소스 비교 분석
- `content_brief` — 리서치 기반 콘텐츠 제작
- `rag_setup` — RAG 지식 베이스 노트북 구축

---

## 등록된 MCP Tools (31개)

### 노트북 관리

| Tool | 설명 |
|------|------|
| `notebook_create` | 새 노트북 생성 |
| `notebook_list` | 전체 노트북 목록 |
| `notebook_get` | 노트북 상세 정보 + 요약 |
| `notebook_delete` | 노트북 삭제 |
| `notebook_rename` | 노트북 이름 변경 |

### 소스 관리

| Tool | 설명 |
|------|------|
| `source_add_url` | URL을 소스로 추가 (웹페이지, 아티클 등) |
| `source_add_text` | 텍스트 콘텐츠를 소스로 추가 |
| `source_add_file` | 로컬 파일을 소스로 추가 (PDF, Markdown, Word 등) |
| `source_list` | 노트북 내 소스 목록 |
| `source_get_fulltext` | 소스의 전체 인덱싱된 텍스트 추출 |
| `source_get_guide` | AI 생성 소스 가이드/요약 |
| `source_delete` | 소스 삭제 |

### RAG Q&A

| Tool | 설명 |
|------|------|
| `chat_ask` | 소스 기반 질문 (인용 포함 답변) |
| `chat_ask_specific_sources` | 특정 소스만 대상으로 질문 |
| `chat_configure` | 채팅 페르소나/시스템 프롬프트 설정 |

### 리서치

| Tool | 설명 |
|------|------|
| `research_web` | 웹 리서치 + 소스 자동 추가 (fast/deep 모드) |
| `research_drive` | Google Drive 리서치 + 소스 자동 추가 |
| `research_poll` | 진행 중인 리서치 상태 확인 |
| `research_import_sources` | 리서치 결과에서 선택적 소스 임포트 |

### 콘텐츠 생성

| Tool | 설명 |
|------|------|
| `generate_report` | 브리핑 문서, 스터디 가이드, 블로그 포스트 생성 |
| `generate_audio` | 팟캐스트/오디오 오버뷰 생성 (deep-dive, brief, critique, debate) |
| `generate_video` | 비디오 오버뷰 생성 (classic, whiteboard 등 스타일) |
| `generate_quiz` | 퀴즈 생성 (난이도/수량 조절) |
| `generate_flashcards` | 플래시카드 생성 |
| `generate_slides` | 슬라이드 덱 생성 |
| `generate_infographic` | 인포그래픽 생성 (portrait, landscape, square) |
| `generate_mindmap` | 마인드맵 생성 (JSON 구조) |
| `generate_data_table` | 데이터 테이블 생성 (자연어로 구조 지정) |

### 다운로드 / 아티팩트

| Tool | 설명 |
|------|------|
| `download_artifact` | 생성된 아티팩트 다운로드 (MP3, MP4, PDF, PNG, CSV, JSON, MD) |
| `list_artifacts` | 노트북 내 생성된 아티팩트 목록 |

### 파이프라인

| Tool | 설명 |
|------|------|
| `research_pipeline` | 올인원 리서치: 노트북 생성 → URL 추가 → 웹 리서치 → 요약 → 리포트 생성 |

---

## 프로젝트 구조

```
research-notebooklm-mcp/
├── pyproject.toml
├── scripts/
│   └── login.py                     # 시스템 Chrome 기반 로그인 스크립트
└── src/notebooklm_mcp/
    ├── __init__.py
    ├── client.py                    # 싱글톤 NotebookLM 클라이언트 관리
    ├── server.py                    # MCP 서버 메인 (FastMCP)
    ├── tools/
    │   ├── notebook.py              # 노트북 CRUD
    │   ├── source.py                # 소스 관리
    │   ├── chat.py                  # RAG Q&A
    │   ├── research.py              # 웹/드라이브 리서치
    │   ├── generate.py              # 콘텐츠 생성
    │   ├── download.py              # 아티팩트 다운로드
    │   └── pipeline.py              # 자동화 파이프라인
    ├── prompts/
    │   └── __init__.py              # MCP 프롬프트 템플릿
    └── resources/
        └── __init__.py              # MCP 리소스 (노트북 목록, 서버 상태)
```

---

## 아키텍처

```
┌─────────────────────────────────────────────┐
│              MCP Clients                    │
│  ┌───────────┐  ┌───────┐  ┌────────────┐  │
│  │Claude Code│  │Web UI │  │Other Tools │  │
│  │ (stdio)   │  │ (SSE) │  │ (SSE)      │  │
│  └─────┬─────┘  └───┬───┘  └─────┬──────┘  │
└────────┼─────────────┼────────────┼─────────┘
         │             │            │
         ▼             ▼            ▼
┌─────────────────────────────────────────────┐
│       notebooklm-mcp (FastMCP)              │
│                                             │
│  31 Tools + 4 Prompts + 2 Resources         │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Singleton NotebookLMClient (async)  │    │
│  └──────────────┬──────────────────────┘    │
└─────────────────┼───────────────────────────┘
                  │ undocumented Google RPC
                  ▼
         ┌─────────────────┐
         │ Google NotebookLM│
         └─────────────────┘
```

**전송 방식:**
- **stdio** — Claude Code 연동 (기본)
- **SSE** — 웹 UI 등 HTTP 기반 클라이언트 연동 (서버 모드로 실행 시)

---

## 콘텐츠 생성 소요 시간 참고

| 타입 | 예상 소요 시간 | 다운로드 포맷 |
|------|--------------|-------------|
| Report | 5-15분 | Markdown |
| Audio (팟캐스트) | 10-20분 | MP3 |
| Video | 15-45분 | MP4 |
| Quiz | 5-15분 | JSON, Markdown, HTML |
| Flashcards | 5-15분 | JSON, Markdown, HTML |
| Slide Deck | 5-15분 | PDF |
| Infographic | 5-15분 | PNG |
| Mind Map | 즉시 | JSON |
| Data Table | 5-15분 | CSV |

> 콘텐츠 생성 시 MCP 서버가 완료까지 자동으로 대기합니다(timeout 포함).
> Google Rate Limit에 의해 실패할 수 있으며, 이 경우 5-10분 후 재시도하세요.

---

## 알려진 제한사항

- **비공식 API**: Google이 내부 엔드포인트를 변경하면 동작이 중단될 수 있음
- **Rate Limiting**: 과도한 사용 시 Google에 의해 제한될 수 있음 (특히 오디오/비디오 생성)
- **인증 만료**: 세션 쿠키가 만료되면 `scripts/login.py`로 재인증 필요
- **소스 제한**: 노트북당 최대 50개 소스
- **Playwright Chromium 크래시**: macOS에서 Playwright 번들 Chromium이 크래시할 수 있음 → `scripts/login.py`가 시스템 Chrome을 대신 사용

---

## 트러블슈팅

### 인증 에러

```bash
# 인증 상태 확인
uv run notebooklm auth check

# 재인증
uv run python scripts/login.py
```

### MCP 서버 연결 확인

```bash
# 서버가 정상 로드되는지 확인
uv run python -c "from notebooklm_mcp.server import mcp; print(f'Tools: {len(mcp._tool_manager._tools)}')"

# MCP 프로토콜 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' \
  | uv run python -m notebooklm_mcp.server 2>/dev/null

# Claude Code 연동 확인
claude mcp list
```

### 콘텐츠 생성 실패

Google Rate Limit이 원인일 수 있습니다. 5-10분 후 재시도하세요.
안정적으로 동작하는 기능: 노트북 CRUD, 소스 추가/조회, 채팅, 마인드맵, 리포트

---

## 라이선스

MIT
