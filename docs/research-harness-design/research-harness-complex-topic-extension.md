# Research Harness — Complex Topic Extension

용어는 [통합 설계의 공통 용어](research-harness-design.md#공통-용어)를 따른다. 이 문서에서 하위 문제를 뜻하던 `Topic`과 `Track`은 `Subproblem`으로 통일한다. 제목의 Complex Topic은 요청 전체의 복합 주제를 뜻하며 실행 단위 이름이 아니다.

## 1. 목적

이 문서는 기존 **Research Harness v1**에 복합 주제 처리 능력을 추가하기 위한 설계 확장안이다.

기존 Harness는 하나의 문제 공간에 대해 서로 다른 탐색 축을 만들고, 여러 Explorer가 이를 독립적으로 조사한 뒤 Orchestrator가 결과를 종합하는 구조를 가진다.

```text
Problem
  ↓
Problem Framing
  ↓
Exploration Axis Design
  ↓
Parallel Explorers
  ↓
Coverage / Reliability Evaluation
  ↓
Conditional Extra Explorer / Critic
  ↓
Synthesis
```

이 구조는 하나의 문제를 여러 관점에서 탐색하는 데 적합하다.

하지만 실제 사용에서는 하나의 요청 안에 서로 다른 하위 문제가 함께 포함될 수 있다.

예:

- Feature Spec lifecycle 개선
- Module Spec / Architecture 문서 구조 개선
- ADR 책임 분리
- Agent Context Loading 개선
- Migration 정책 정리

이들은 같은 상위 맥락을 공유하지만 서로 다른 질문이며, 일부는 다른 문제의 결론에 의존할 수 있다.

기존 Harness가 이러한 요청을 그대로 하나의 Problem으로 취급하면 다음 문제가 발생할 수 있다.

- 서로 다른 Subproblem을 Exploration Axis로 잘못 취급
- 중요한 하위 문제가 누락
- Explorer 간 탐색 범위 중복
- 서로 다른 전제를 가진 결과가 혼합
- 선행 결정이 필요한 문제를 너무 일찍 탐색
- 최종 Synthesis 복잡도 증가
- 사용자에게 다시 문제 분리를 요청하게 됨

따라서 복합 주제에서는 기존 Research Harness 위에 다음 상위 계층을 추가한다.

```text
Constraint Classification
Subproblem Decomposition
Dependency-aware Ordering
Sequential Subproblem Execution
Global Synthesis
```

핵심 목표는 다음 두 가지다.

1. 사용자가 복합 문제를 직접 여러 요청으로 분리하지 않아도 되게 한다.
2. 기존 Research Harness의 핵심 실행 방식과 Explorer 병렬성을 그대로 유지한다.

---

## 2. 기본 원칙

복합 문제를 지원하기 위해 기존 Harness의 핵심 구조를 바꾸지 않는다.

Subproblem은 조사 대상인 하위 문제다. Research Unit은 하나의 Subproblem을 조사하는 실행 단위이며, 기존 Research Harness의 실행 절차를 사용한다.

```text
Subproblem
  ↓
Problem Framing
  ↓
Exploration Axis Design
  ↓
Explorer × 2~3
  ↓
Evaluation
  ↓
Conditional Extra Explorer / Critic
  ↓
Local Synthesis
```

복합 문제는 이러한 Research Unit을 순차적으로 실행하는 방식으로 처리한다.

```text
Complex Request
  ↓
Subproblem A
  ↓
Subproblem B
  ↓
Subproblem C
  ↓
Global Synthesis
```

즉 복잡도가 증가해도 동시에 실행되는 Agent 수를 늘리지 않는다.

---

## 3. 두 단계 문제 분해

복합 주제에서는 Problem Space Decomposition을 두 단계로 나눈다.

```text
Level 1
Subproblem Decomposition
→ 어떤 하위 문제들이 존재하는가?

Level 2
Exploration Axis Design
→ 각 하위 문제를 어떤 서로 다른 방향으로 탐색할 것인가?
```

이 둘은 서로 다른 개념이다.

### Subproblem

하나의 독립된 질문 묶음 또는 설계 대상이다.

예:

- Feature Spec lifecycle
- Persistent Architecture 구조
- Agent Context Loading
- Migration Strategy

### Exploration Axis

하나의 Subproblem 안에서 서로 다른 답 또는 위험을 탐색하기 위한 질문 방향이다.

예:

```text
Subproblem:
Feature Spec lifecycle

Axis A:
현재 lifecycle에서 누락된 단계는 무엇인가?

Axis B:
Feature Spec 삭제 후에도 미래 설계에 필요한 지식이 보존되는가?

Axis C:
Architecture Knowledge Promotion이 과도한 문서화를 유발하지 않는가?
```

핵심 원칙:

> **먼저 문제를 나누고, 그 다음 각 문제의 탐색 축을 나눈다.**

Subproblem과 Exploration Axis를 혼동하지 않는다.

---

## 4. Constraint Classification

복합 요청에는 단순한 질문뿐 아니라 반드시 지켜야 하는 제약, 사용자의 선호 방향, 검증이 필요한 가설, 제외 범위, 요구 산출물이 함께 포함될 수 있다.

이들을 하나의 `Fixed Principles`로 묶으면 서로 성격이 다른 상위 Context가 동일하게 취급될 수 있다.

따라서 다음과 같이 분류한다.

```text
Hard Constraints
Goals / Preferences
Hypotheses
Open Questions
Out of Scope
Required Outcomes
```

### Hard Constraints

반드시 지켜야 하는 경계다.

Hard Constraint는 Research 결과에 의해 임의로 뒤집지 않는다.

### Goals / Preferences

사용자가 중요하게 보는 방향 또는 선호다.

이들은 Explorer가 고려해야 할 **평가 기준**이지, 결론을 미리 정하는 답이 아니다.

Research 결과에 따라 해당 Goal은 유지, 재해석, 우선순위 조정될 수 있다.

### Hypotheses

사용자가 현재 가능성이 높다고 생각하지만 Research를 통해 검증해야 하는 주장이다.

Hypothesis는 확인될 수도 있고, 수정되거나 기각될 수도 있다.

### Open Questions

실제 Research를 통해 답을 찾아야 하는 문제다.

Explorer는 대안, 위험, 근거, trade-off를 탐색한다.

### Out of Scope

이번 Research에서 다루지 않을 사항이다.

### Required Outcomes

최종 결과가 반드시 포함해야 하는 산출물이다.

Constraint Classification의 목적은 결론을 미리 고정하는 것이 아니라,
**각 Subproblem이 어떤 경계 안에서 무엇을 검증해야 하는지 명확하게 만드는 것**이다.

핵심 원칙:

> **Hard Constraints constrain the research. Goals and hypotheses guide what to evaluate, not what to conclude.**

## 5. Complexity Check

모든 요청에 복합 처리 절차를 적용하지 않는다.

Complexity Check의 목적은 요청을 정교하게 점수화하거나 등급화하는 것이 아니라,
**Subproblem Decomposition이 필요한지 판단하는 것**이다.

현재 실행 모델에서는 Subproblem을 병렬 스케줄링하지 않으므로,
복잡도 점수가 실행계획을 직접 결정할 필요가 없다.

따라서 Orchestrator는 고정 점수표보다 다음과 같은 **휴리스틱 신호**를 사용한다.

### Simple로 처리할 가능성이 높은 신호

다음과 같은 경우에는 기존 Research Harness 흐름을 그대로 사용한다.

- 핵심 질문이 하나로 명확하게 수렴한다.
- 여러 관점이 필요하더라도 하나의 Problem Space 안에서 Exploration Axis로 표현할 수 있다.
- 별도의 독립적인 Local Synthesis가 필요한 하위 문제가 없다.
- 선행 결론을 필요로 하는 별도의 후속 문제가 없다.

예:

```text
Spring Batch에서 Cursor와 Paging 중 어떤 구조가 더 적절한가?
```

이 경우:

```text
Problem Framing
→ Exploration Axis Design
→ Explorer
→ Synthesis
```

로 충분하다.

### Subproblem Decomposition을 고려해야 하는 신호

다음 신호가 나타나면 요청 안에 여러 Subproblem이 존재하는지 검토한다.

- 서로 다른 핵심 질문이 여러 개 존재한다.
- 하나의 결론으로 합치기 어려운 별도 설계 대상이 존재한다.
- 어떤 질문의 결론이 다른 질문의 입력이 된다.
- 서로 다른 종류의 결과물 또는 결정이 필요하다.
- Hard Constraints, Goals / Preferences, Open Questions, Out of Scope가 복합적으로 섞여 있다.
- 하나의 Exploration Axis 집합으로 다루면 범위가 지나치게 넓어진다.
- 각 영역에 대해 독립적인 Local Synthesis가 의미가 있다.

이 신호들은 **점수가 아니다**.

예를 들어 신호가 두 개 있다고 자동으로 Compound가 되고,
네 개 있다고 Complex가 되는 식으로 분류하지 않는다.

Orchestrator는 다음 질문을 중심으로 판단한다.

> **이 요청을 하나의 Problem Space 안에서 서로 다른 Exploration Axis로 충분히 탐색할 수 있는가?**

가능하다면 Simple로 처리한다.

그렇지 않고 서로 독립적인 결론이 필요한 질문 묶음이 존재한다면 Subproblem Decomposition을 수행한다.

### Dependency는 분해 이후 확인한다

Complexity Check 단계에서 모든 의존성을 미리 정교하게 분석할 필요는 없다.

먼저 Subproblem 후보를 식별한 뒤,
실제 Subproblem이 여러 개라면 Dependency Mapping에서 다음을 확인한다.

```text
어떤 Subproblem이 다른 Subproblem의 결과를 필요로 하는가?
```

Dependency는 Subproblem의 병렬성 판단이 아니라
**순차 실행 순서를 결정하기 위한 정보**로 사용한다.

### 휴리스틱 사용 원칙

> **Use signals, not scores.**

> **Complexity Check는 분류 자체가 목적이 아니라, 필요한 경우에만 Subproblem Decomposition을 활성화하기 위한 게이트다.**

> **애매한 경우에는 점수에 맞춰 기계적으로 분리하지 말고, 하나의 Problem Space로 유지할 수 있는지를 먼저 판단한다.**

이 방식은 불필요한 Subproblem 분할과 과도한 오케스트레이션을 줄이면서도,
실제로 복합적인 요청에서는 필요한 상위 분해 단계를 활성화할 수 있게 한다.

---

## 6. Subproblem Decomposition

복합 요청에서는 먼저 상위 문제를 Subproblem으로 분해한다.

Orchestrator는 다음 요소를 식별한다.

```text
Shared Context
Subproblems
Cross-cutting Concerns
Dependencies
```

### Shared Context

모든 Subproblem이 공유하는 전제와 방향이다.

예:

```text
Code + Tests = source of truth
Feature Spec = temporary artifact
Architecture Knowledge = persistent context
문서를 늘리는 것이 목적이 아님
```

### Subproblems

독립적으로 질문하고 탐색할 가치가 있는 문제 묶음이다.

예:

```text
Feature Spec Lifecycle
Persistent Architecture Structure
Agent Context Workflow
Migration & Consistency
```

### Cross-cutting Concerns

여러 Subproblem에 공통으로 적용되는 원칙이다.

예:

```text
single authoritative owner
duplication 방지
obsolete decision 제거
human approval
```

Cross-cutting Concern은 별도 Subproblem으로 무조건 분리하지 않는다.

여러 Subproblem이 공유하는 Context 또는 최종 Cross-Subproblem Consistency Check에서 관리할 수 있다.

---

## 7. Subproblem 분해 기준

사용자 프롬프트의 모든 항목을 각각 하나의 Subproblem으로 만들지 않는다.

과도한 분해는 다음 문제를 만든다.

- Research Unit 수 증가
- 전체 실행시간 급증
- Local Synthesis 증가
- 관련성이 높은 문제를 불필요하게 분리
- Global Synthesis 부담 증가

따라서 세부 질문들은 의미적으로 응집된 Subproblem으로 묶는다.

예:

```text
Feature Spec 삭제
Feature Spec lifecycle
Architecture Knowledge Promotion
기존 Architecture와 새 Feature 충돌 처리
```

이들은 모두 다음 하나의 Subproblem으로 묶을 수 있다.

```text
Feature Spec Lifecycle
```

좋은 Subproblem은 다음 성질을 가진다.

```text
하나의 명확한 핵심 질문
내부적으로 여러 Exploration Axis 생성 가능
다른 Subproblem과 구분되는 목적
독립적인 Local Synthesis가 의미 있음
```

핵심은:

> **질문 수만큼 Subproblem을 만드는 것이 아니라, 하나의 일관된 결론이 필요한 질문 묶음 단위로 분해한다.**

---

## 8. Subproblem Independence

Subproblem Decomposition의 목적은 복합 문제를 관리 가능한 단위로 나누는 것뿐 아니라,
각 Subproblem의 **독립적인 탐색 가능성**을 보존하는 것이다.

상위 Goal이나 Preference가 존재하더라도 각 Subproblem의 결론을 그 방향에 맞추도록 유도하지 않는다.

Goal / Preference는 각 Subproblem이 반드시 고려해야 할 평가 기준으로 사용한다.

조사 결과가 초기 Goal과 충돌한다면 그 충돌 자체를 결과로 유지한다.

### 독립 Subproblem 사이에는 Local Conclusion을 전파하지 않는다

실행 순서상 Subproblem A가 Subproblem B보다 먼저 수행되더라도,
A의 Recommendation을 B의 전제로 자동 전달하지 않는다.

```text
A Local Conclusion
≠
B Constraint
```

이는 순차 실행이 불필요한 Anchoring Effect를 만드는 것을 방지한다.

다만 B의 연구에 실제로 필요한 다음 정보는 전달할 수 있다.

```text
Verified Facts
Hard Constraints
True Structural Dependencies
Required Shared Context
```

핵심 원칙:

> **Research subproblems independently unless a real factual or structural dependency requires context propagation.**

> **A prior subproblem’s recommendation must not become a constraint for another independent subproblem.**

실행은 로컬 리소스 제약 때문에 순차적이지만,
논리적인 연구 구조는 가능한 한 독립성을 유지한다.

```text
Execution:
A → B → C

Reasoning Structure:
A ┐
B ├→ Global Synthesis
C ┘
```


## 9. Dependency Mapping

Subproblem은 순차 실행한다.

Dependency Mapping의 목적은 병렬 실행 여부를 결정하는 것이 아니라
**실제 의존성이 존재할 때 올바른 실행 순서와 필요한 Context 전달 범위를 결정하는 것**이다.

예:

```text
Feature Lifecycle
        ↓
Agent Context Workflow
        ↓
Migration
```

Agent Context Workflow를 설계하려면 Feature Lifecycle에서 확인된 구조적 사실이나 Hard Constraint가 먼저 필요할 수 있다.

이 경우 선행 Subproblem을 먼저 수행한다.

반대로 서로 독립적인 Subproblem이라면 특정 순서 제약은 없다.

그 경우 Orchestrator는 다음 기준으로 실행 순서를 정할 수 있다.

```text
foundation first
high-impact first
high-uncertainty first
user emphasis
natural conceptual order
```

다만 실행 순서가 곧 reasoning dependency를 의미하지는 않는다.

독립 Subproblem 사이에서는 Recommendation이나 Local Conclusion을 전달하지 않는다.

핵심 원칙:

> **Subproblem은 순차 실행한다. 실제 의존성이 있을 때만 필요한 Context를 선택적으로 전달한다.**

## 10. 왜 Subproblem을 순차 실행하는가

현재 Harness의 기본 Explorer 구조는 하나의 문제에 대해 여러 독립적인 탐색 축을 병렬 조사하는 방식이다.

```text
Subproblem A
├─ Explorer A1
├─ Explorer A2
└─ Explorer A3
```

이 구조의 목적은 처리량 증가보다 **reasoning diversity 확보**에 있다.

현재 로컬 실행 환경에서는 다음 상한을 유지한다.

```text
Orchestrator = 1
Subagent = 최대 3

Max Concurrent Agents = 4
```

하나의 Subproblem이 최대 3개의 Explorer를 사용하면 다른 Subproblem을 같은 깊이로 동시에 탐색할 Subagent가 남지 않는다.

따라서 Subproblem 병렬화를 위해 Explorer 수를 줄이지 않는다.

예를 들어 다음과 같은 방식은 기본 전략으로 사용하지 않는다.

```text
A1 + B1 + C1
→ A2 + B2 + C2
→ A3 + B3 + C3
```

이는 각 Subproblem이 하나의 Explorer 관점만 가진 상태에서 다음 문제로 넘어가므로 기존 Harness의 reasoning diversity를 약화할 수 있다.

기본 실행은 다음과 같다.

```text
A1 + A2 + A3
      ↓
A Local Synthesis
      ↓
B1 + B2 + B3
      ↓
B Local Synthesis
      ↓
C1 + C2 + C3
```

이 방식은 전체 실행시간을 늘릴 수 있지만 다음을 보존한다.

- Subproblem별 reasoning diversity
- Local Synthesis 품질
- 다음 Subproblem으로 전달되는 정리된 Context
- 로컬 리소스 사용량의 예측 가능성

이는 의도된 trade-off다.

---

## 11. Explorer 실행 기준

복합 문제에서도 Research Harness v1의 Explorer 기준을 그대로 사용한다.

### Initial Explorers

```text
2~3개
기본값: 3
```

Explorer는 같은 질문을 반복하지 않는다.

각 Explorer는 서로 다른 Exploration Axis를 담당한다.

### Extra Explorer

Coverage Gap이 명확한 경우에만 추가한다.

```text
Extra Explorer = 최대 1개
```

Extra Explorer는 새로운 Agent 종류가 아니다.

동일한 Explorer agent definition을 새로운 Axis에 대해 한 번 더 실행한다.

### Critic

다음과 같은 경우 조건부로 호출한다.

```text
결과가 너무 쉽게 수렴함
중요 가정의 검증이 부족함
고위험 Architecture Decision
근거의 신뢰성 검토가 필요함
```

권장 기준:

```text
Critic = 최대 1회
```

### Additional Round

기본은 one-pass다.

추가 탐색은 근거가 있을 때만 수행한다.

> **Default one-pass, iterate only on evidence.**

---

### 실행 제약

복합도와 무관하게 동시 실행 상한은 유지한다.

```text
Max Concurrent Subagents = 3
Max Concurrent Agents = 4
```

Explorer, Extra Explorer, Critic은 동일한 Subagent 슬롯을 공유한다.

복합 문제 전체에 별도의 전역 Explorer 호출 제한은 두지 않는다. 탐색량은 위의 Subproblem별 실행 기준으로 제어한다.

Subproblem 수가 증가하면 전체 실행시간은 증가할 수 있으며, 이는 로컬 리소스 안정성과 Subproblem별 reasoning diversity를 유지하기 위해 의도적으로 수용하는 trade-off다.

---

## 12. Subproblem 내부 Exploration Axis Design

각 Subproblem 안에서는 기존 Exploration Axis 설계를 그대로 사용한다.

```text
Subproblem
  ↓
Problem Framing
  ↓
Dimension Extraction
  ↓
Candidate Axis Generation
  ↓
Overlap Removal
  ↓
Coverage Check
  ↓
Question-based Final Axes
  ↓
Parallel Explorers
```

좋은 Axis는 다음 성질을 가진다.

### Distinct

다른 Axis와 실질적으로 다른 질문이다.

### Relevant

핵심 문제 해결에 직접 기여한다.

### Covering

여러 Axis가 함께 중요한 문제 공간을 충분히 덮는다.

### Independent

다른 Explorer의 결과 없이도 탐색할 수 있다.

### Synthesizable

최종적으로 비교 및 통합할 수 있다.

### Cost-effective

별도 Explorer를 사용할 가치가 있다.

핵심 원칙:

> **Explorer를 여러 개 만드는 것이 아니라, 서로 다른 질문을 여러 개 만든다.**

---

## 13. Local Synthesis

각 Subproblem이 끝날 때마다 Orchestrator가 Local Synthesis를 수행한다.

```text
Explorer A1
Explorer A2
Explorer A3
      ↓
Local Synthesis
```

Local Synthesis에서는 다음을 확인한다.

- Explorer 결과의 공통점
- 서로 충돌하는 주장
- 핵심 trade-off
- Coverage Gap
- 근거 신뢰성
- Extra Explorer 필요 여부
- Critic 필요 여부
- 다음 Subproblem에 전달할 Context

Local Synthesis는 단순 요약이 아니다.

다음 Subproblem이 앞선 탐색 결과를 **정제된 Context**로 사용할 수 있게 만드는 단계다.

---

## 14. Selective Context Propagation

Subproblem은 순차 실행되지만,
앞선 Local Synthesis의 전체 결론을 다음 Subproblem에 자동으로 전달하지 않는다.

기본 원칙은 다음과 같다.

```text
Independent Subproblem
→ Local Conclusion을 다음 Subproblem에 전파하지 않음
```

전달 가능한 것은 다음과 같은 **필수 Context**다.

```text
Verified Facts
Hard Constraints
Structural Dependencies
Required Shared Context
```

Recommendation은 독립 Subproblem의 입력으로 사용하지 않는다.

이 구분은 순차 실행으로 인한 Anchoring Effect를 줄이고
각 Subproblem의 독립적인 Research를 보존한다.

Orchestrator는 다음 Subproblem에 Context를 전달하기 전에 확인한다.

```text
이 정보가 없으면 다음 Subproblem의 Research가 사실적으로 잘못되거나
구조적으로 불가능해지는가?
```

Yes인 경우에만 전달한다.

핵심:

> **Propagate dependencies, not recommendations.**

## 15. Cross-Subproblem Consistency Check

복합 문제는 여러 Local Synthesis를 단순히 이어 붙이는 것으로 끝내지 않는다.

모든 Subproblem 탐색이 끝난 후 Orchestrator는 전체 결과를 다시 비교한다.

확인 항목:

```text
Subproblem 간 직접적인 결론 충돌
동시에 최적화하기 어려운 Subproblem 간 tension
Hard Constraint 위반
Goals / Preferences와 Research 결과의 긴장
Hypothesis의 확인 / 수정 / 기각 여부
Cross-cutting Concern 누락
중복된 책임 또는 문서 소유권
서로 양립할 수 없는 Recommendation
후속 Human Decision 필요 여부
```

예:

```text
Feature Lifecycle에서는 Architecture 문서가 A를 소유한다고 결론
Architecture Structure에서는 ADR이 A를 소유한다고 결론

→ Cross-Subproblem Conflict
→ Global Synthesis에서 해결 필요
```

이 검사는 복합 문제의 결과를 단순한 여러 보고서 묶음이 아니라 **하나의 일관된 설계안**으로 만들기 위해 필요하다.

---

## 16. Global Synthesis

모든 Subproblem이 종료된 후 Orchestrator가 최종 Global Synthesis를 수행한다.

Global Synthesis에는 다음이 포함된다.

```text
전체 문제에 대한 통합 결론
Subproblem 간 관계
확정된 제안
중요 trade-off
남은 불확실성
Human Decision 필요 사항
실행 또는 Migration 순서
```

필요하면 사용자가 요구한 산출물 형식으로 다시 구성한다.

예:

```text
Current State
Problems
Proposed Target State
Migration Impact
Proposed Changes
```

---

## 17. Human Escalation

복합 주제에서도 기존 Research Harness의 Human Escalation 원칙을 유지한다.

### Level 0 — Autonomous

기술적 사실, 코드, 문서, 근거 조사로 해결할 수 있다.

→ Harness가 계속 진행한다.

### Level 1 — Assumption

합리적이고 되돌릴 수 있는 가정이다.

→ 가정을 명시하고 진행한다.

### Level 2 — Human Decision

다음과 같은 판단이다.

```text
business intent
risk acceptance
cost acceptance
policy decision
architecture governance
accountability
```

→ 사용자 판단이 필요하다.

원칙:

> **Don’t ask just because you can ask. Ask when a human decision is genuinely required.**

---

## 18. User-facing Output Contract

Research Harness의 내부 실행 구조와 사용자에게 보여주는 최종 출력 구조는 분리한다.

Harness 내부에서는 다음과 같은 절차가 수행될 수 있다.

```text
Subproblem Decomposition
→ Subproblem A
   ├─ Explorer A1
   ├─ Explorer A2
   └─ Explorer A3
→ Local Synthesis
→ Subproblem B
→ Critic
→ Cross-Subproblem Consistency Check
→ Global Synthesis
```

하지만 사용자가 알아야 하는 것은 이러한 내부 오케스트레이션 구조 자체가 아니다.

사용자에게 중요한 것은 다음이다.

```text
무엇이 결론인가?
왜 그런 결론에 도달했는가?
어떤 중요한 대안과 trade-off가 있었는가?
아직 결정해야 할 것은 무엇인가?
다음에 무엇을 해야 하는가?
```

따라서 Harness의 내부 구조는 사용자 출력에서 기본적으로 캡슐화한다.

> **Internal orchestration is implementation detail. The user-facing result is the synthesized outcome.**

이 원칙은 객체지향 프로그래밍의 캡슐화와 유사하다.

사용자는 내부에서 몇 개의 Explorer가 호출되었는지,
어떤 Subproblem 순서로 조사했는지,
Critic이 어느 시점에 실행되었는지를 알 필요가 없다.

내부 구현은 변경될 수 있지만 사용자-facing contract는 안정적으로 유지해야 한다.

### 내부 구조를 그대로 노출하지 않는다

기본 출력에서 다음과 같은 형태는 피한다.

```text
Explorer 1의 의견
Explorer 2의 의견
Explorer 3의 의견
Critic의 반론
```

이 방식은 최종 결과를 Research Report가 아니라 Agent 회의록처럼 보이게 만든다.

Explorer 결과는 Local Synthesis의 입력이고,
Local Synthesis는 Global Synthesis의 입력이다.

사용자에게는 최종적으로 정제된 결과를 전달한다.

```text
Explorer Results
      ↓
Local Synthesis
      ↓
Cross-Subproblem Consistency Check
      ↓
Global Synthesis
      ↓
User-facing Result
```

### Subproblem은 자연스러운 주제명으로 표현한다

내부적으로는 다음처럼 관리할 수 있다.

```text
Subproblem A
Subproblem B
Subproblem C
```

하지만 사용자에게는 내부 식별자를 노출하지 않는다.

예:

```text
Feature Spec Lifecycle
Persistent Architecture
Agent Context Workflow
Migration
```

처럼 실제 의미를 나타내는 주제명으로 표현한다.

즉 Subproblem은 내부에서 식별하는 하위 문제이며, 실행은 해당 Research Unit이 담당한다.
사용자-facing 정보 구조는 문제 영역의 의미를 기준으로 구성한다.

### 기본 출력 구조

특별한 사용자 지정이 없다면 최종 결과는 다음 구조를 기본으로 한다.

```text
# Research Result

## Executive Summary
- 핵심 결론
- 가장 중요한 근거
- 핵심 trade-off
- Human Decision이 필요한 사항

## Problem Framing
- 해결하려는 문제
- Hard Constraints
- Goals / Preferences
- Hypotheses
- Open Questions
- 중요한 Scope / Out of Scope

## Findings
### <하위 문제의 실제 이름 A>
- 핵심 발견
- 주요 근거
- 중요한 대안
- 주요 위험 또는 제약

### <하위 문제의 실제 이름 B>
...

## 통합 결론
- 하위 문제 간 관계
- 독립적인 Local Conclusion의 비교
- Subproblem 간 충돌 / 긴장
- Goals / Preferences와의 관계
- Hypothesis의 확인 / 수정 / 기각
- Research 결과에서 도출된 상위 원칙
- 전체적으로 일관된 Target State

## Proposed Direction
- 최종 제안
- 제안 이유
- 주요 trade-off

## Open Questions / Human Decisions
- AI가 대신 결정하지 않아야 할 사항
- 남아 있는 중요한 불확실성

## Next Actions
- 다음 실행 단계
```

이 구조는 고정 템플릿이라기보다 기본 contract다.

사용자 요청이나 Research 성격에 따라 섹션은 축소, 병합, 재배치할 수 있다.

초기 Goals, Preferences, Hypotheses는 최종 결론을 구속하지 않는다.

> **Initial goals, preferences, and hypotheses may be confirmed, refined, or rejected by the research findings.**

### Executive Summary는 결론 중심으로 작성한다

사용자가 전체 Research 과정을 읽어야만 결론을 이해할 수 있게 만들지 않는다.

Executive Summary에는 최소한 다음이 드러나야 한다.

```text
결론
핵심 이유
가장 중요한 trade-off
사용자가 결정해야 할 사항
```

상세 근거는 이후 섹션에서 설명한다.

즉 출력은 다음 순서를 우선한다.

```text
Conclusion First
→ Evidence
→ Trade-offs
→ Details
```

Research 수행 순서를 그대로 출력 순서로 사용하지 않는다.

### Findings는 Local Synthesis 결과를 사용한다

Findings는 개별 Explorer의 raw result를 나열하는 공간이 아니다.

각 Subproblem의 Findings는 해당 Subproblem의 Local Synthesis를 기반으로 작성한다.

따라서 다음을 중심으로 한다.

```text
핵심 발견
근거
의미 있는 대안
중요한 disagreement
trade-off
risk
```

Explorer 간 의견 차이가 최종 판단에 중요한 경우에만
그 차이를 사용자에게 노출한다.

단순한 중간 논쟁이나 반복 의견은 제거한다.

### Global Synthesis는 단순한 요약이 아니다

여러 Subproblem을 조사한 경우 최종 결과를 각 Subproblem 요약의 모음으로 끝내지 않는다.

Global Synthesis에서는 다음을 수행한다.

```text
Subproblem 간 관계 연결
공통 원칙 도출
충돌 조정
상호 영향 분석
Target State 통합
```

즉:

```text
A 결과
B 결과
C 결과
```

가 아니라:

```text
A + B + C
→ 하나의 일관된 결론
```

을 만드는 단계다.

### Research Trace는 기본적으로 숨긴다

다음과 같은 내부 실행 정보는 기본 출력에 포함하지 않는다.

```text
Explorer 호출 수
Subproblem 실행 순서
Agent model
Critic 호출 시점
내부 prompt
중간 reasoning trace
```

사용자가 수행 과정 자체를 요청한 경우에는
필요한 범위에서 요약된 Research Trace를 별도로 제공할 수 있다.

그러나 이 정보도 최종 결론보다 우선하지 않는다.

### 출력 깊이는 내부 탐색량과 분리한다

복합 문제라고 해서 최종 결과가 반드시 매우 길어야 하는 것은 아니다.

```text
Deep Internal Research
≠
Verbose User Output
```

충분히 조사한 뒤에도 결론이 단순하다면 결과는 간결할 수 있다.

반대로 중요한 trade-off나 Human Decision이 많다면 필요한 만큼 상세하게 설명한다.

기준은 Agent가 얼마나 많이 일했는지가 아니라
사용자가 결정을 내리는 데 필요한 정보량이다.

### 사용자 출력의 성공 기준

최종 출력 품질은 다음 질문으로 평가한다.

```text
사용자가 결론을 빠르게 파악할 수 있는가?
근거를 추적할 수 있는가?
중요한 trade-off가 드러나는가?
남은 Human Decision이 명확한가?
여러 Subproblem의 결과가 하나의 방향으로 통합되어 있는가?
내부 Agent 구조를 몰라도 결과를 이해할 수 있는가?
```

핵심 원칙:

> **The harness may be multi-agent internally, but it should speak to the user with one coherent voice.**

> **Internal = decomposition, diversity, criticism, synthesis.**

> **External = conclusion, evidence, trade-offs, decisions, next actions.**

---

## 19. 추천 전체 흐름

### Simple Request

```text
User Request
   ↓
Complexity Check
   ↓
Problem Framing
   ↓
Exploration Axis Design
   ↓
Explorer × 2~3
   ↓
Coverage / Reliability Evaluation
   ├─ Extra Explorer 최대 1
   ├─ Critic 최대 1
   └─ Sufficient
   ↓
Synthesis
```

### Complex Request — 복합 요청

```text
User Request
   ↓
Complexity Check
   ↓
Constraint Classification
   ↓
Subproblem Decomposition
   ↓
Shared Context / Cross-cutting Concerns
   ↓
Dependency Mapping
   ↓
Subproblem Ordering
   ↓
────────────────────────────
Subproblem A
   ↓
Problem Framing
   ↓
Exploration Axis Design
   ↓
Explorer × 2~3
   ↓
Coverage / Reliability Evaluation
   ├─ Extra Explorer 최대 1
   ├─ Critic 최대 1
   └─ Sufficient
   ↓
Local Synthesis
────────────────────────────
   ↓
Context Propagation
   ↓
────────────────────────────
Subproblem B
   ↓
same Research Unit
────────────────────────────
   ↓
...
   ↓
Cross-Subproblem Consistency Check
   ↓
Global Synthesis
   ↓
Human Escalation if required
```

---

## 20. 실행 기준

### Global

```text
Subproblem
= 순차 실행

Max Concurrent Subagents
= 3

Max Concurrent Agents
= 4
```

### Per Subproblem

```text
Initial Explorers
= 2~3
기본값 3

Extra Explorer
= 최대 1

Critic
= 최대 1회

Additional Round
= 명확한 근거가 있을 때만
```

### Global Exploration Budget

```text
사용하지 않음
```

복합도는 전역 Explorer 호출 제한으로 제어하지 않는다.

---

## 21. 설계 동기

### 21.1 사용자가 복합 요청을 직접 분해할 필요가 없다

Harness가 요청 안에서 다음을 식별한다.

```text
Constraint Classification 결과
Shared Context
Subproblems
Dependencies
Cross-cutting Concerns
```

사용자는 하나의 자연어 요청으로 복합 Research를 시작할 수 있다.

### 21.2 기존 Harness의 reasoning diversity를 유지한다

각 Subproblem에 Explorer 2~3개를 배정해 서로 다른 Exploration Axis를 독립적으로 탐색한다.

Subproblem 병렬화를 위해 이 구조를 약화하지 않는다.

### 21.3 로컬 리소스 사용량을 예측 가능하게 유지한다

```text
Subagent ≤ 3
Total Concurrent Agent ≤ 4
```

복잡도가 증가해도 이 상한을 유지한다.

### 21.4 선행 결과가 후속 탐색에 반영된다

앞선 Local Synthesis의 핵심 결론과 제약을 다음 Subproblem에 전달한다.

따라서 후속 Explorer가 이미 밝혀진 사실을 다시 가정하거나 상충되는 전제를 만들 가능성이 줄어든다.

### 21.5 복잡도 증가를 실행시간으로 흡수한다

복합 문제에서는 전체 실행시간이 증가한다.

하지만 Agent 수를 무리하게 늘려 로컬 환경을 불안정하게 만드는 것보다 예측 가능한 순차 실행을 선택한다.

### 21.6 전역 Budget으로 정상적인 복합 탐색을 차단하지 않는다

Subproblem 수가 많은 문제는 Explorer 총 호출 수가 자연스럽게 증가한다.

따라서 전체 Explorer 호출 수를 6회, 8회처럼 고정 제한하지 않는다.

탐색 폭발은 각 Subproblem의 기존 제한으로 제어한다.

### 21.7 복합 문제 결과를 하나의 설계로 통합한다

Local Synthesis만으로 끝내지 않고 Cross-Subproblem Consistency Check와 Global Synthesis를 수행한다.

이를 통해 각 Subproblem의 결론이 서로 충돌하지 않는지 확인한다.

---

## 22. 최종 원칙

> **먼저 문제를 나누고, 그 다음 각 문제의 탐색 축을 나눈다.**

> **Subproblem은 순차 실행한다.**

> **Subproblem 간 의존성이 있으면 Dependency Mapping으로 실행 순서를 결정한다.**

> **각 Subproblem은 기존 Research Harness와 동일한 Research Unit으로 처리한다.**

> **각 Subproblem 내부에서는 서로 다른 Exploration Axis를 최대 3개의 Explorer가 병렬 탐색한다.**

> **복잡도가 증가해도 동시 Agent 수는 늘리지 않는다.**

> **복잡도 증가는 Subproblem 수와 전체 실행시간 증가로 흡수한다.**

> **전역 Exploration Budget은 두지 않고 기존 Per-Subproblem Explorer 기준을 유지한다.**

> **모든 Subproblem이 끝난 후 Cross-Subproblem Consistency Check와 Global Synthesis를 수행한다.**

최종 구조:

```text
Complex Request
   ↓
Constraint Classification
   ↓
Subproblem Decomposition
   ↓
Dependency Mapping
   ↓
Subproblem Ordering
   ↓
Subproblem A
   ├─ Explorer A1
   ├─ Explorer A2
   └─ Explorer A3
   ↓
Local Synthesis
   ↓
Context Propagation
   ↓
Subproblem B
   ├─ Explorer B1
   ├─ Explorer B2
   └─ Explorer B3
   ↓
Local Synthesis
   ↓
...
   ↓
Cross-Subproblem Consistency Check
   ↓
Global Synthesis
```

이 확장은 Research Harness v1의 핵심 실행 모델을 변경하지 않는다.

복합 문제를 위해 추가되는 핵심 기능은 다음과 같다.

```text
Constraint Classification
Subproblem Decomposition
Dependency-aware Ordering
Sequential Subproblem Execution
Cross-Subproblem Context Propagation
Cross-Subproblem Consistency Check
Global Synthesis
```
