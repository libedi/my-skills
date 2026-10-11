# Kiro 런타임 프로브

Kiro 어댑터(`skills/research/adapters/kiro/`)는 공식 문서만 보고 작성했다. 문서에 없거나 불명확한 동작을 Kiro IDE와 CLI에서 실제로 확인하기 위한 절차다. 실행 시에는 필요 없는 문서다.

- 작성일: 2026-10-11
- 근거 문서: [Custom agents configuration reference](https://kiro.dev/docs/custom-agents/configuration-reference/), [Subagents](https://kiro.dev/docs/custom-agents/subagents/), [Skills](https://kiro.dev/docs/skills/), [Reasoning effort](https://kiro.dev/docs/models/effort/)

## 준비

1. 저장소에서 어댑터의 모델 ID를 `/model` 목록에 맞게 고친다. 설치 후에 고치면 설치기가 제거를 거부한다.
2. 빈 git 프로젝트에 설치한다.

   ```sh
   python scripts/install.py --skill research --target kiro --scope project --root <probe-project>
   ```

3. `<probe-project>`를 Kiro IDE와 Kiro CLI(`kiro-cli chat`)에서 각각 연다.

각 프로브는 연구가 아니므로 프롬프트 첫머리에 `PROBE ONLY, do not research.`를 붙인다.

## 프로브 목록

| ID | 확인할 것 | 방법 | 결과에 따른 어댑터 조치 |
| --- | --- | --- | --- |
| K1 | JSON 에이전트 3개가 IDE·CLI 양쪽에서 로드되는가 | IDE 에이전트 선택기와 CLI 에이전트 목록에서 `research-*` 확인 | 한쪽이 안 되면 해당 화면용 형식(Markdown 등)을 추가 검토 |
| K2 | 정의한 모델 ID로 첫 프롬프트가 성공하는가 | 메인 세션에서 "Use the research-explorer agent to reply PONG" | 실패하면 JSON `model`과 runtime.md 표를 고침 |
| K3 | 서브에이전트가 커스텀 에이전트의 `model`을 따르는가 | K2 실행 중 CLI `Ctrl+G` 에이전트 모니터, IDE 서브에이전트 표시에서 모델 확인 | 따르지 않으면 "모델도 역할별 미보장"으로 runtime.md 공개 범위를 넓힘 |
| K4 | 서브에이전트가 서브에이전트를 띄울 수 있는가 (중첩) | "Use the research-orchestrator agent. Task: start the research-explorer agent with the task 'reply PONG and list your tools', then return its reply." | 안 되면 sibling 대체 경로가 기본 경로가 됨. runtime.md에 명시 |
| K5 | Orchestrator가 `availableAgents` 밖의 에이전트를 못 띄우는가 | K4와 같은 방식으로 기본 에이전트나 임의 이름을 요청 | 띄울 수 있으면 `availableAgents` 강제가 안 됨을 공개 |
| K6 | 워커 도구 제한이 적용되는가 | Explorer에게 도구 목록 출력, `research/probe-ok.txt` 쓰기, 루트에 `probe-denied.txt` 쓰기, `ls`와 `touch x` 실행을 요청. Critic에게 도구 목록 출력 요청 | 루트 쓰기나 `touch`가 성공하면 `permissions` 규칙(`exclude` 의미)을 고침 |
| K7 | `trustedAgents`로 권한 프롬프트 없이 병렬 실행되는가 | Orchestrator가 Explorer 2개를 한 배치로 띄우게 함 | 프롬프트로 멈추면 runtime.md에 사전 승인 절차를 추가 |
| K8 | 끝난 서브에이전트를 재개할 수 있는가 | K2 직후 "send a follow-up to that same subagent: reply ROUND2 and quote your previous reply" | 재개되면 continuation 대신 재개를 기본으로 바꾸는 것을 검토 |
| K9 | 서브에이전트 effort가 무엇을 따르는가 | 세션 effort를 바꿔 가며 K2 반복, 모니터나 로그에 effort가 보이는지 확인 | 보이면 요청값과 대조하도록 runtime.md 갱신 |
| K10 | 서브에이전트 실행 기록이 로컬에 남는가 | 실행 후 `~/.kiro/`와 프로젝트 `.kiro/`에서 모델 ID 문자열 검색 (예: `grep -rl "claude-sonnet" ~/.kiro`) | 모델·도구 호출이 기록되면 Claude 어댑터처럼 검사기를 만들 수 있음 |

## 결과 기록 양식

```text
Kiro IDE 버전:
Kiro CLI 버전:
사용 가능한 모델 ID (/model):

K1:
K2:
...
K10:
```

결과는 이슈로 남기고 어댑터 변경은 그 이슈를 참조한다.
