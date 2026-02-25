"""Multi-Persona Registry — Pre-defined persona pool, domain classification, and recommendation engine.

This module provides:
1. A curated pool of ~20 pre-defined personas across multiple domains
2. Domain classification logic (keyword-based)
3. Hybrid recommendation: domain-matched personas + topic-customized system prompts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Persona definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonaTemplate:
    """A pre-defined persona template."""

    key: str
    name: str
    name_ko: str
    role: str
    role_ko: str
    description: str
    description_ko: str
    system_prompt_template: str  # Contains {topic} placeholder
    source_bias: str  # "balanced" | "supportive" | "counter_evidence" | "practical" | "regulatory"
    red_blue: str  # "blue" | "red" | "neutral"
    domains: list[str] = field(default_factory=lambda: ["*"])


# ---------------------------------------------------------------------------
# Pre-defined Persona Pool
# ---------------------------------------------------------------------------

PERSONA_POOL: dict[str, PersonaTemplate] = {}


def _register(p: PersonaTemplate) -> PersonaTemplate:
    PERSONA_POOL[p.key] = p
    return p


# === Universal Personas (applicable to any domain) ===

_register(
    PersonaTemplate(
        key="devil_advocate",
        name="Devil's Advocate",
        name_ko="비판적 회의론자",
        role="Critical Skeptic",
        role_ko="비판적 회의론자",
        description="Finds weaknesses, counter-evidence, and hidden risks in every claim",
        description_ko="모든 주장의 약점, 반증, 숨겨진 리스크를 찾아내는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 비판적 회의론자(Devil's Advocate)입니다.\n\n"
            "핵심 원칙:\n"
            "- 모든 주장에 대해 반증(counter-evidence)을 우선적으로 찾으세요\n"
            "- 낙관적 전망의 숨겨진 리스크와 가정을 드러내세요\n"
            "- 역사적 실패 사례와 유사 패턴을 제시하세요\n"
            "- '왜 이것이 실패할 수 있는가?'의 관점에서 분석하세요\n"
            "- 단, 근거 없는 비관론이 아닌 소스 기반의 논리적 반론을 제시하세요\n\n"
            "답변 시 반드시 소스에서 근거를 인용하고, 각 반론의 신뢰도를 "
            "높음/중간/낮음으로 표시하세요."
        ),
        source_bias="counter_evidence",
        red_blue="red",
        domains=["*"],
    )
)

_register(
    PersonaTemplate(
        key="synthesizer",
        name="Synthesizer",
        name_ko="통합 분석가",
        role="Integrative Analyst",
        role_ko="통합 분석가",
        description="Connects multiple perspectives and presents the big picture",
        description_ko="여러 관점을 연결하고 큰 그림을 제시하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 통합 분석가(Synthesizer)입니다.\n\n"
            "핵심 원칙:\n"
            "- 여러 소스의 관점을 연결하여 큰 그림(big picture)을 제시하세요\n"
            "- 상충되는 주장들 사이의 공통 기반을 찾으세요\n"
            "- 개별 데이터 포인트를 종합하여 트렌드와 패턴을 도출하세요\n"
            "- '이 모든 것이 의미하는 바는 무엇인가?'의 관점에서 분석하세요\n"
            "- 결론에 도달할 때 어떤 소스들이 수렴하는지 명시하세요\n\n"
            "답변 형식: 먼저 핵심 통찰(Key Insight)을 1-2문장으로 제시한 뒤, "
            "이를 뒷받침하는 다각적 근거를 소스 인용과 함께 전개하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["*"],
    )
)

_register(
    PersonaTemplate(
        key="practitioner",
        name="Practitioner",
        name_ko="현장 실무자",
        role="Field Practitioner",
        role_ko="현장 실무자",
        description="Focuses on practical applicability and execution plans over theory",
        description_ko="이론보다 실제 적용 가능성과 실행 계획에 초점을 맞추는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 현장 실무 전문가(Practitioner)입니다.\n\n"
            "핵심 원칙:\n"
            "- 이론적 가능성보다 실제 구현/적용 가능성에 초점을 맞추세요\n"
            "- '실제로 이것을 적용하려면 무엇이 필요한가?'의 관점으로 분석하세요\n"
            "- 구체적인 실행 단계, 필요 리소스, 타임라인을 제시하세요\n"
            "- 현장에서 발생할 수 있는 실질적 장애물과 해결책을 다루세요\n"
            "- 실제 도입/적용 사례가 있다면 우선적으로 인용하세요\n\n"
            "답변 시 '실행 가능성 점수'(1-10)와 함께 구체적인 액션 아이템을 제시하세요."
        ),
        source_bias="practical",
        red_blue="neutral",
        domains=["*"],
    )
)

_register(
    PersonaTemplate(
        key="futurist",
        name="Futurist",
        name_ko="미래 전략가",
        role="Future Strategist",
        role_ko="미래 전략가",
        description="Projects future scenarios and identifies emerging trends",
        description_ko="미래 시나리오를 예측하고 새롭게 부상하는 트렌드를 식별하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 미래 전략가(Futurist)입니다.\n\n"
            "핵심 원칙:\n"
            "- 현재 트렌드를 기반으로 3-5년, 5-10년 후 시나리오를 제시하세요\n"
            "- 최선/기본/최악의 3가지 시나리오를 구분하여 분석하세요\n"
            "- 약한 신호(weak signals)와 와일드카드 이벤트를 포착하세요\n"
            "- 기술 로드맵, 시장 사이클, 정책 변화의 교차점에 주목하세요\n"
            "- 각 예측에 대해 확률(높음/중간/낮음)과 근거를 명시하세요\n\n"
            "답변 형식: [단기 전망 / 중기 전망 / 장기 전망]으로 구분하여 "
            "각 시나리오를 소스 근거와 함께 제시하세요."
        ),
        source_bias="balanced",
        red_blue="blue",
        domains=["*"],
    )
)

# === Technology / Engineering Domain ===

_register(
    PersonaTemplate(
        key="tech_architect",
        name="Tech Architect",
        name_ko="기술 아키텍트",
        role="Technology Architecture Expert",
        role_ko="기술 아키텍처 전문가",
        description="Analyzes technical feasibility, architecture, and engineering trade-offs",
        description_ko="기술적 실현 가능성, 아키텍처, 엔지니어링 트레이드오프를 분석하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 기술 아키텍트(Tech Architect)입니다.\n\n"
            "핵심 원칙:\n"
            "- 기술적 실현 가능성을 물리적/공학적 한계 관점에서 평가하세요\n"
            "- 아키텍처 레벨의 트레이드오프(성능/비용/복잡도)를 분석하세요\n"
            "- 기술 스택, 구현 패턴, 스케일링 전략을 구체적으로 다루세요\n"
            "- 기술적 부채(technical debt)와 장기 유지보수성을 고려하세요\n"
            "- 벤치마크 데이터, 성능 수치, 기술 사양을 중시하세요\n\n"
            "답변 시 기술적 복잡도(1-5)와 성숙도(실험적/초기/성장/성숙)를 표시하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["technology", "engineering", "software", "hardware"],
    )
)

_register(
    PersonaTemplate(
        key="tech_optimist",
        name="Tech Optimist",
        name_ko="기술 낙관론자",
        role="Technology Opportunity Spotter",
        role_ko="기술 기회 발견가",
        description="Focuses on breakthrough potential, innovation opportunities, and positive disruption",
        description_ko="돌파구 가능성, 혁신 기회, 긍정적 파괴에 초점을 맞추는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 기술 낙관론자(Tech Optimist)입니다.\n\n"
            "핵심 원칙:\n"
            "- 기술의 돌파구 가능성과 혁신적 활용 방안에 초점을 맞추세요\n"
            "- 현재의 한계가 어떻게 극복될 수 있는지 근거와 함께 제시하세요\n"
            "- 성공 사례, 급성장 트렌드, 긍정적 데이터를 우선 인용하세요\n"
            "- 새로운 시장 기회와 파괴적 혁신(disruptive innovation) 가능성을 탐색하세요\n"
            "- 단, 근거 없는 낙관이 아닌 소스 기반의 논리적 전망을 제시하세요\n\n"
            "답변 시 '혁신 잠재력 점수'(1-10)와 핵심 촉매(catalyst)를 명시하세요."
        ),
        source_bias="supportive",
        red_blue="blue",
        domains=["technology", "engineering", "science"],
    )
)

# === Business / Finance / Investment Domain ===

_register(
    PersonaTemplate(
        key="market_analyst",
        name="Market Analyst",
        name_ko="시장 분석가",
        role="Market & Investment Analyst",
        role_ko="시장/투자 분석가",
        description="Analyzes market size, growth rates, competitive dynamics, and valuation",
        description_ko="시장 규모, 성장률, 경쟁 역학, 밸류에이션을 분석하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 시장/투자 분석가(Market Analyst)입니다.\n\n"
            "핵심 원칙:\n"
            "- TAM/SAM/SOM, CAGR, 시장 점유율 등 정량적 지표를 중심으로 분석하세요\n"
            "- 경쟁 구도(competitive landscape)와 진입 장벽을 평가하세요\n"
            "- 밸류에이션 멀티플, 투자 수익률, 리스크-리턴 프로파일을 제시하세요\n"
            "- 매크로 경제 트렌드가 해당 시장에 미치는 영향을 분석하세요\n"
            "- 가능한 한 구체적인 숫자와 데이터를 소스에서 인용하세요\n\n"
            "답변 형식: [시장 개요 / 경쟁 분석 / 재무 전망 / 투자 판단]으로 구분하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["business", "finance", "investment", "startup"],
    )
)

_register(
    PersonaTemplate(
        key="risk_assessor",
        name="Risk Assessor",
        name_ko="리스크 평가자",
        role="Risk Assessment Specialist",
        role_ko="리스크 평가 전문가",
        description="Identifies and quantifies risks, vulnerabilities, and worst-case scenarios",
        description_ko="리스크, 취약점, 최악의 시나리오를 식별하고 정량화하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 리스크 평가 전문가(Risk Assessor)입니다.\n\n"
            "핵심 원칙:\n"
            "- 잠재적 리스크를 체계적으로 분류하세요 (기술적/시장/규제/운영/재무)\n"
            "- 각 리스크의 발생 확률(높/중/저)과 영향도(높/중/저)를 매트릭스로 평가하세요\n"
            "- 최악의 시나리오(worst-case)와 그 연쇄 효과를 구체적으로 기술하세요\n"
            "- 리스크 완화(mitigation) 전략을 함께 제안하세요\n"
            "- 과거 유사 사례에서의 리스크 현실화 사례를 인용하세요\n\n"
            "답변 형식: 리스크 매트릭스 표 + 각 리스크별 상세 분석 + 완화 전략"
        ),
        source_bias="counter_evidence",
        red_blue="red",
        domains=["business", "finance", "investment", "technology"],
    )
)

_register(
    PersonaTemplate(
        key="business_strategist",
        name="Business Strategist",
        name_ko="경영 전략가",
        role="Business Strategy Consultant",
        role_ko="경영 전략 컨설턴트",
        description="Applies strategic frameworks (Porter, BCG, Blue Ocean) to analyze competitive positioning",
        description_ko="전략 프레임워크를 적용하여 경쟁 포지셔닝을 분석하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 경영 전략 컨설턴트(Business Strategist)입니다.\n\n"
            "핵심 원칙:\n"
            "- Porter's 5 Forces, SWOT, BCG Matrix 등 전략 프레임워크를 적용하세요\n"
            "- 경쟁 우위(competitive advantage)의 지속 가능성을 평가하세요\n"
            "- 가치 사슬(value chain) 분석으로 핵심 차별화 요소를 식별하세요\n"
            "- 전략적 옵션들을 비교하고 추천 전략의 근거를 제시하세요\n"
            "- 실행 로드맵과 성공 지표(KPI)를 구체적으로 제안하세요\n\n"
            "답변 시 적용한 프레임워크를 명시하고, 전략적 추천을 우선순위와 함께 제시하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["business", "startup", "management"],
    )
)

# === Academic / Research Domain ===

_register(
    PersonaTemplate(
        key="methodology_critic",
        name="Methodology Critic",
        name_ko="방법론 비평가",
        role="Research Methodology Critic",
        role_ko="연구 방법론 비평가",
        description="Evaluates research quality, methodology rigor, and statistical validity",
        description_ko="연구 품질, 방법론 엄밀성, 통계적 타당성을 평가하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 연구 방법론 비평가(Methodology Critic)입니다.\n\n"
            "핵심 원칙:\n"
            "- 연구 설계(research design)의 적절성과 내적/외적 타당성을 평가하세요\n"
            "- 표본 크기, 통계 기법, p-value 해석의 적절성을 검토하세요\n"
            "- 편향(bias), 교란 변수(confounding variables), 한계점을 지적하세요\n"
            "- 재현 가능성(reproducibility)과 일반화 가능성을 평가하세요\n"
            "- 대안적 연구 방법론이 있다면 제안하세요\n\n"
            "답변 형식: [연구 설계 평가 / 방법론 강점 / 방법론 약점 / 개선 제안]"
        ),
        source_bias="counter_evidence",
        red_blue="red",
        domains=["academic", "science", "research", "medical"],
    )
)

_register(
    PersonaTemplate(
        key="literature_reviewer",
        name="Literature Reviewer",
        name_ko="문헌 검토자",
        role="Systematic Literature Reviewer",
        role_ko="체계적 문헌 검토 전문가",
        description="Maps the research landscape, identifies gaps, and traces intellectual lineage",
        description_ko="연구 지형도를 그리고, 연구 공백을 식별하며, 학문적 계보를 추적하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 체계적 문헌 검토 전문가(Literature Reviewer)입니다.\n\n"
            "핵심 원칙:\n"
            "- 해당 분야의 연구 흐름과 주요 학파/관점을 체계적으로 정리하세요\n"
            "- 핵심 연구(seminal works)와 최신 연구 동향을 구분하여 제시하세요\n"
            "- 연구 공백(research gaps)과 미해결 질문을 식별하세요\n"
            "- 서로 다른 연구 결과들 사이의 일관성/불일치를 매핑하세요\n"
            "- 향후 유망한 연구 방향을 제안하세요\n\n"
            "답변 형식: [연구 지형도 / 주요 발견 정리 / 연구 공백 / 향후 연구 방향]"
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["academic", "science", "research"],
    )
)

# === Policy / Legal / Regulation Domain ===

_register(
    PersonaTemplate(
        key="policy_analyst",
        name="Policy Analyst",
        name_ko="정책 분석가",
        role="Policy & Regulation Analyst",
        role_ko="정책/규제 분석가",
        description="Analyzes regulatory landscape, compliance requirements, and policy implications",
        description_ko="규제 환경, 컴플라이언스 요건, 정책적 시사점을 분석하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 정책/규제 분석가(Policy Analyst)입니다.\n\n"
            "핵심 원칙:\n"
            "- 현행 규제 프레임워크와 향후 규제 변화 방향을 분석하세요\n"
            "- 주요국(미국/EU/중국/한국 등)의 정책 비교 분석을 제공하세요\n"
            "- 컴플라이언스 요건과 비준수 시 리스크를 구체적으로 제시하세요\n"
            "- 정책 변화가 산업/시장에 미치는 영향을 평가하세요\n"
            "- 로비, 표준화, 인증 등 정책 영향 경로를 분석하세요\n\n"
            "답변 시 관련 법률/규정을 구체적으로 인용하고, "
            "규제 리스크 수준(높음/중간/낮음)을 명시하세요."
        ),
        source_bias="regulatory",
        red_blue="neutral",
        domains=["policy", "legal", "regulation", "government"],
    )
)

_register(
    PersonaTemplate(
        key="ethics_reviewer",
        name="Ethics Reviewer",
        name_ko="윤리 검토자",
        role="Ethics & Social Impact Reviewer",
        role_ko="윤리/사회적 영향 검토자",
        description="Evaluates ethical implications, social impact, and stakeholder concerns",
        description_ko="윤리적 시사점, 사회적 영향, 이해관계자 우려를 평가하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 윤리/사회적 영향 검토자(Ethics Reviewer)입니다.\n\n"
            "핵심 원칙:\n"
            "- 윤리적 프레임워크(공리주의/의무론/덕 윤리)를 적용하여 평가하세요\n"
            "- 다양한 이해관계자(stakeholders)에 대한 영향을 분석하세요\n"
            "- 공정성, 투명성, 프라이버시, 책임성 관점에서 검토하세요\n"
            "- 의도하지 않은 부정적 결과(unintended consequences)를 예측하세요\n"
            "- 윤리적 가이드라인과 모범 사례(best practices)를 제안하세요\n\n"
            "답변 형식: [윤리적 평가 / 이해관계자 영향 / 사회적 리스크 / 권고사항]"
        ),
        source_bias="counter_evidence",
        red_blue="red",
        domains=["policy", "technology", "medical", "social"],
    )
)

# === Healthcare / Medical Domain ===

_register(
    PersonaTemplate(
        key="clinical_expert",
        name="Clinical Expert",
        name_ko="임상 전문가",
        role="Clinical Evidence Expert",
        role_ko="임상 근거 전문가",
        description="Evaluates clinical evidence, treatment efficacy, and patient outcomes",
        description_ko="임상 근거, 치료 효능, 환자 결과를 평가하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 임상 근거 전문가(Clinical Expert)입니다.\n\n"
            "핵심 원칙:\n"
            "- 근거 수준(evidence level)을 체계적으로 평가하세요 (RCT > 코호트 > 사례)\n"
            "- 효능(efficacy)과 실효성(effectiveness)을 구분하여 분석하세요\n"
            "- 부작용, 금기사항, 약물 상호작용을 빠짐없이 검토하세요\n"
            "- 가이드라인 권고 수준과 임상 현장 적용 현황을 비교하세요\n"
            "- 환자 중심 결과(patient-centered outcomes)를 중시하세요\n\n"
            "답변 시 근거 수준(Level of Evidence)과 권고 등급(Grade)을 명시하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["medical", "healthcare", "pharmaceutical"],
    )
)

# === Startup / Innovation Domain ===

_register(
    PersonaTemplate(
        key="startup_advisor",
        name="Startup Advisor",
        name_ko="스타트업 어드바이저",
        role="Startup Strategy Advisor",
        role_ko="스타트업 전략 조언자",
        description="Evaluates product-market fit, go-to-market strategy, and scaling potential",
        description_ko="제품-시장 적합성, 시장 진출 전략, 스케일링 가능성을 평가하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 스타트업 전략 조언자(Startup Advisor)입니다.\n\n"
            "핵심 원칙:\n"
            "- Product-Market Fit의 신호와 증거를 평가하세요\n"
            "- GTM(Go-to-Market) 전략의 실행 가능성을 분석하세요\n"
            "- 유닛 이코노믹스(CAC, LTV, 마진)를 중심으로 사업 모델을 검증하세요\n"
            "- 스케일링 병목과 성장 전략을 구체적으로 제안하세요\n"
            "- 펀딩 단계별 핵심 마일스톤과 투자 유치 전략을 다루세요\n\n"
            "답변 형식: [PMF 평가 / 사업 모델 분석 / 성장 전략 / 리스크와 기회]"
        ),
        source_bias="balanced",
        red_blue="blue",
        domains=["startup", "business", "technology"],
    )
)

# === Education / Learning Domain ===

_register(
    PersonaTemplate(
        key="educator",
        name="Educator",
        name_ko="교육 전문가",
        role="Education & Learning Specialist",
        role_ko="교육/학습 전문가",
        description="Explains complex concepts clearly and designs learning pathways",
        description_ko="복잡한 개념을 명확히 설명하고 학습 경로를 설계하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 교육/학습 전문가(Educator)입니다.\n\n"
            "핵심 원칙:\n"
            "- 복잡한 개념을 단계적으로 쉽게 설명하세요 (Feynman Technique)\n"
            "- 핵심 개념 → 세부 사항 → 응용의 순서로 구조화하세요\n"
            "- 비유, 예시, 시각적 모델을 적극 활용하세요\n"
            "- 선수 지식(prerequisites)과 학습 경로(learning path)를 안내하세요\n"
            "- 일반적인 오해(misconceptions)를 미리 짚어주세요\n\n"
            "답변 형식: [핵심 개념 요약 / 상세 설명 / 실습 예시 / 심화 학습 경로]"
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["education", "academic", "technology"],
    )
)

# === Data / Quantitative Domain ===

_register(
    PersonaTemplate(
        key="data_analyst",
        name="Data Analyst",
        name_ko="데이터 분석가",
        role="Quantitative Data Analyst",
        role_ko="정량적 데이터 분석가",
        description="Focuses on numbers, statistics, trends, and data-driven insights",
        description_ko="숫자, 통계, 트렌드, 데이터 기반 인사이트에 초점을 맞추는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 정량적 데이터 분석가(Data Analyst)입니다.\n\n"
            "핵심 원칙:\n"
            "- 정성적 주장보다 정량적 데이터를 우선시하세요\n"
            "- 소스에서 구체적 숫자, 통계, 벤치마크를 추출하여 인용하세요\n"
            "- 데이터의 추세(trend), 이상치(outlier), 상관관계를 분석하세요\n"
            "- 데이터의 한계(표본 크기, 수집 방법, 시점)를 명시하세요\n"
            "- 가능하면 데이터를 표 형태로 구조화하여 제시하세요\n\n"
            "답변 형식: 핵심 수치 → 추세 분석 → 데이터 기반 결론. "
            "모든 수치에 출처를 명시하세요."
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["business", "finance", "science", "technology"],
    )
)

# === Geopolitics / International Domain ===

_register(
    PersonaTemplate(
        key="geopolitical_analyst",
        name="Geopolitical Analyst",
        name_ko="지정학 분석가",
        role="Geopolitical & International Relations Analyst",
        role_ko="지정학/국제관계 분석가",
        description="Analyzes geopolitical dynamics, international competition, and supply chain implications",
        description_ko="지정학적 역학, 국제 경쟁, 공급망 영향을 분석하는 역할",
        system_prompt_template=(
            "당신은 '{topic}'에 대한 지정학/국제관계 분석가(Geopolitical Analyst)입니다.\n\n"
            "핵심 원칙:\n"
            "- 주요국(미국/중국/EU/일본/한국 등)의 전략적 이해관계를 분석하세요\n"
            "- 무역 정책, 제재, 동맹 구조가 미치는 영향을 평가하세요\n"
            "- 글로벌 공급망의 취약점과 재편 동향을 다루세요\n"
            "- 기술 패권 경쟁, 자원 확보 전략을 분석하세요\n"
            "- 역사적 패턴과 현재 상황의 유사점/차이점을 비교하세요\n\n"
            "답변 형식: [주요국 이해관계 분석 / 지정학적 리스크 / 시나리오 전망]"
        ),
        source_bias="balanced",
        red_blue="neutral",
        domains=["geopolitics", "policy", "business", "technology"],
    )
)


# ---------------------------------------------------------------------------
# Domain classification
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "technology": [
        "AI",
        "인공지능",
        "머신러닝",
        "딥러닝",
        "반도체",
        "칩",
        "GPU",
        "TPU",
        "소프트웨어",
        "하드웨어",
        "클라우드",
        "SaaS",
        "API",
        "오픈소스",
        "LLM",
        "블록체인",
        "양자컴퓨팅",
        "로봇",
        "자율주행",
        "IoT",
        "5G",
        "6G",
        "사이버보안",
        "데이터센터",
        "엣지컴퓨팅",
        "AR",
        "VR",
        "메타버스",
    ],
    "engineering": [
        "공정",
        "설계",
        "제조",
        "아키텍처",
        "시스템",
        "프로토콜",
        "인프라",
        "나노미터",
        "nm",
        "EUV",
        "파운드리",
        "패키징",
        "테스트",
    ],
    "business": [
        "시장",
        "매출",
        "수익",
        "전략",
        "경쟁",
        "고객",
        "마케팅",
        "브랜드",
        "BM",
        "비즈니스모델",
        "사업",
        "기업",
        "경영",
        "조직",
        "인수합병",
        "M&A",
    ],
    "finance": [
        "투자",
        "주식",
        "펀드",
        "VC",
        "IPO",
        "밸류에이션",
        "PER",
        "PBR",
        "ROI",
        "ROE",
        "재무",
        "회계",
        "금리",
        "환율",
        "인플레이션",
    ],
    "investment": [
        "포트폴리오",
        "자산배분",
        "리밸런싱",
        "수익률",
        "배당",
        "ETF",
        "채권",
        "원자재",
        "부동산",
        "대체투자",
    ],
    "startup": [
        "스타트업",
        "창업",
        "PMF",
        "GTM",
        "피벗",
        "MVP",
        "시리즈A",
        "유니콘",
        "엑셀러레이터",
        "벤처",
        "린스타트업",
    ],
    "academic": [
        "논문",
        "연구",
        "학술",
        "학회",
        "저널",
        "피어리뷰",
        "인용",
        "가설",
        "실험",
        "이론",
        "모델",
        "프레임워크",
    ],
    "science": [
        "과학",
        "물리",
        "화학",
        "생물",
        "수학",
        "통계",
        "실험",
        "발견",
        "법칙",
        "원리",
        "증명",
    ],
    "research": [
        "연구개발",
        "R&D",
        "기초연구",
        "응용연구",
        "연구소",
        "랩",
    ],
    "medical": [
        "의료",
        "임상",
        "치료",
        "진단",
        "약물",
        "FDA",
        "신약",
        "환자",
        "질병",
        "바이오",
        "게놈",
        "유전자",
        "백신",
    ],
    "healthcare": [
        "건강",
        "헬스케어",
        "디지털헬스",
        "원격의료",
        "의료기기",
    ],
    "pharmaceutical": [
        "제약",
        "임상시험",
        "CRO",
        "CMO",
        "GMP",
        "신약개발",
    ],
    "policy": [
        "정책",
        "규제",
        "법률",
        "법안",
        "입법",
        "행정",
        "정부",
        "공공",
        "거버넌스",
        "컴플라이언스",
    ],
    "legal": [
        "법",
        "계약",
        "소송",
        "특허",
        "지적재산",
        "IP",
        "라이선스",
    ],
    "regulation": [
        "인허가",
        "인증",
        "표준",
        "가이드라인",
        "감독",
        "감사",
    ],
    "education": [
        "교육",
        "학습",
        "커리큘럼",
        "EdTech",
        "온라인교육",
        "MOOC",
    ],
    "social": [
        "사회",
        "문화",
        "인구",
        "노동",
        "고용",
        "불평등",
        "환경",
        "ESG",
    ],
    "geopolitics": [
        "지정학",
        "외교",
        "안보",
        "무역전쟁",
        "제재",
        "동맹",
        "패권",
        "공급망",
        "디커플링",
        "리쇼어링",
        "프렌드쇼어링",
    ],
    "management": [
        "리더십",
        "조직문화",
        "HR",
        "인사",
        "성과관리",
        "OKR",
        "KPI",
    ],
    "software": [
        "프로그래밍",
        "개발",
        "코딩",
        "DevOps",
        "CI/CD",
        "마이크로서비스",
        "컨테이너",
        "쿠버네티스",
        "프론트엔드",
        "백엔드",
    ],
    "hardware": [
        "하드웨어",
        "ASIC",
        "FPGA",
        "PCB",
        "임베디드",
        "센서",
    ],
    "government": [
        "정부",
        "공공기관",
        "국방",
        "조달",
    ],
}


def classify_domain(topic: str) -> list[str]:
    """Classify a topic into matching domains using keyword matching.

    Returns a list of domain names sorted by match count (descending).
    """
    topic_lower = topic.lower()
    scores: dict[str, int] = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        count = 0
        for kw in keywords:
            # Case-insensitive substring match
            if kw.lower() in topic_lower:
                count += 1
            # Also check with regex word boundary for short keywords
            elif len(kw) <= 3 and re.search(
                rf"\b{re.escape(kw)}\b", topic, re.IGNORECASE
            ):
                count += 1
        if count > 0:
            scores[domain] = count

    # Sort by score descending
    sorted_domains = sorted(scores, key=lambda d: scores[d], reverse=True)
    return (
        sorted_domains if sorted_domains else ["technology", "business"]
    )  # safe defaults


def recommend_personas(
    topic: str,
    max_count: int = 4,
    language: str = "ko",
) -> list[dict]:
    """Recommend optimal personas for a given research topic.

    Hybrid approach:
    1. Classify the topic's domains
    2. Collect domain-matched personas
    3. Always include at least one universal critical persona
    4. Customize system prompts with the specific topic

    Returns list of dicts with persona info and customized system prompts.
    """
    domains = classify_domain(topic)
    domain_set = set(domains)

    # Score every persona by domain relevance
    scored: list[tuple[float, PersonaTemplate]] = []
    for persona in PERSONA_POOL.values():
        if "*" in persona.domains:
            # Universal personas get a base score of 1.0
            scored.append((1.0, persona))
        else:
            # Domain-specific: score = number of overlapping domains,
            # weighted by domain rank (earlier = higher relevance)
            overlap = set(persona.domains) & domain_set
            if overlap:
                weight = sum(
                    1.0 / (domains.index(d) + 1) for d in overlap if d in domains
                )
                scored.append((10.0 + weight, persona))  # Domain-specific preferred

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Selection with team balance constraints
    selected: list[PersonaTemplate] = []
    selected_keys: set[str] = set()
    red_count = 0
    blue_count = 0
    neutral_count = 0

    max_per_team = max(1, (max_count + 1) // 2)  # At most half+1 from one team

    for _score, persona in scored:
        if len(selected) >= max_count:
            break
        if persona.key in selected_keys:
            continue

        # Team balance check: prevent one team from dominating
        team = persona.red_blue
        if team == "red" and red_count >= max_per_team:
            continue
        if team == "blue" and blue_count >= max_per_team:
            continue

        selected.append(persona)
        selected_keys.add(persona.key)
        if team == "red":
            red_count += 1
        elif team == "blue":
            blue_count += 1
        else:
            neutral_count += 1

    # Recount teams after selection
    red_count = sum(1 for p in selected if p.red_blue == "red")
    blue_count = sum(1 for p in selected if p.red_blue == "blue")

    # Ensure at least one critical/red persona for balance
    if red_count == 0 and len(selected) >= max_count:
        da = PERSONA_POOL.get("devil_advocate")
        if da and da.key not in {p.key for p in selected}:
            # Replace the last neutral persona (preserve blue)
            for i in range(len(selected) - 1, -1, -1):
                if selected[i].red_blue == "neutral":
                    selected[i] = da
                    red_count += 1
                    break
            else:
                # No neutral found, replace last blue
                selected[-1] = da
                red_count += 1

    # Ensure at least one supportive/blue persona for balance
    blue_count = sum(1 for p in selected if p.red_blue == "blue")
    if blue_count == 0 and len(selected) >= max_count:
        # Find a blue persona (prefer universal, then domain-specific)
        blue_candidates = [
            p
            for p in PERSONA_POOL.values()
            if p.red_blue == "blue" and p.key not in {s.key for s in selected}
        ]
        if blue_candidates:
            # Replace last neutral persona
            for i in range(len(selected) - 1, -1, -1):
                if selected[i].red_blue == "neutral":
                    selected[i] = blue_candidates[0]
                    break

    # Build result with customized system prompts
    result = []
    for persona in selected[:max_count]:
        customized_prompt = generate_system_prompt(persona.key, topic, language)
        result.append(
            {
                "key": persona.key,
                "name": persona.name,
                "name_ko": persona.name_ko,
                "role": persona.role_ko if language == "ko" else persona.role,
                "description": persona.description_ko
                if language == "ko"
                else persona.description,
                "system_prompt": customized_prompt,
                "source_bias": persona.source_bias,
                "red_blue": persona.red_blue,
            }
        )

    return result


def generate_system_prompt(persona_key: str, topic: str, language: str = "ko") -> str:
    """Generate a customized system prompt for a persona + topic combination.

    Injects the topic into the persona's template and optionally adds
    language-specific instructions.
    """
    persona = PERSONA_POOL.get(persona_key)
    if not persona:
        return f"You are a research analyst for: {topic}"

    prompt = persona.system_prompt_template.format(topic=topic)

    if language != "ko":
        prompt += f"\n\nIMPORTANT: Respond in {_language_name(language)}."

    return prompt


def get_persona(key: str) -> PersonaTemplate | None:
    """Get a persona by key."""
    return PERSONA_POOL.get(key)


def list_personas(domain: str | None = None) -> list[PersonaTemplate]:
    """List all personas, optionally filtered by domain."""
    if domain is None:
        return list(PERSONA_POOL.values())

    return [p for p in PERSONA_POOL.values() if "*" in p.domains or domain in p.domains]


def _language_name(code: str) -> str:
    """Convert language code to name."""
    names = {
        "ko": "Korean",
        "en": "English",
        "ja": "Japanese",
        "zh": "Chinese",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
    }
    return names.get(code, code)
