# 📺 Tube Sorter (유튜브 영상 자동 분류기)

`tube-sorter`는 특정 유튜브 채널에 업로드된 영상을 감지하여, 미리 정의된 키워드 규칙에 따라 사용자의 재생목록(Playlist)으로 자동 분류 및 배정해주는 자동화 도구입니다.

---

## 🍴 포크(Fork) 사용자를 위한 퀵 스타트 가이드 (초보자용)

이 프로젝트를 자신의 계정으로 가져와서 바로 사용하고 싶은 분들을 위한 가이드입니다. 2026년 1월 최신 메뉴 이름을 기준으로 작성되었습니다.

### 1단계: 구글 클라우드 콘솔 설정 (유튜브 API 권한 획득)
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속하여 로그인합니다.
2. 상단 메뉴의 **[프로젝트 선택]** (또는 기존 프로젝트 이름)을 누르고 오른쪽 상단의 **[새 프로젝트]**를 클릭하여 생성합니다.
3. 왼쪽 사이드바 메뉴에서 **[API 및 서비스] > [라이브러리]**를 클릭합니다.
4. `YouTube Data API v3`를 검색하여 클릭한 뒤 **[사용]** 버튼을 누릅니다.
5. 왼쪽 메뉴에서 **[API 및 서비스] > [사용자 인증 정보]**를 클릭합니다.
6. 상단의 **[+ 사용자 인증 정보 만들기] > [OAuth 클라이언트 ID]**를 선택합니다.
   - *동의 화면 구성이 필요하다고 뜨면, [동의 화면 구성] -> [외부] 선택 후 필수 항목(앱 이름, 지원 이메일)만 입력하고 저장하세요.*
7. **애플리케이션 유형**에서 **[데스크톱 앱]**을 선택하고 이름을 입력한 뒤 **[만들기]**를 누릅니다.
8. 생성된 목록 오른쪽에 있는 **다운로드 아이콘(JSON 다운로드)**을 눌러 파일을 받고 이름을 **`client_secrets.json`**으로 변경합니다.

### 2단계: 내 유튜브 계정 인증 및 토큰 생성
1. 본 저장소를 **[Fork]**한 뒤 본인의 컴퓨터로 내려받습니다 (Clone).
2. 터미널(또는 명령 프롬프트)에서 해당 폴더로 이동하여 다음을 실행합니다:
   ```bash
   pip install -r requirements.txt
   python authorize.py
   ```
3. 웹 브라우저가 열리면 자동화에 사용할 본인의 유튜브 계정으로 로그인하고 **[허용]**을 누릅니다.
4. 폴더 안에 **`token.json`** 파일이 생성되었는지 확인합니다.

### 3단계: 깃허브 시크릿(Secrets) 및 권한 설정
1. 내 깃허브 저장소 상단 탭에서 **[Settings]**를 클릭합니다.
2. 왼쪽 메뉴에서 **[Secrets and variables] > [Actions]**를 차례로 클릭합니다.
3. **[Secrets]** 탭에서 **[New repository secret]**을 눌러 다음 3개를 추가합니다:
   - `CLIENT_SECRETS_JSON`: `client_secrets.json` 파일 내용 전체 복사
   - `TOKEN_JSON`: `token.json` 파일 내용 전체 복사
   - `ENV_FILE`: `.env` 파일 내용 전체 (채널 ID 등 설정값)
4. 왼쪽 메뉴 **[Actions] > [General]**로 들어가 맨 아래 **[Workflow permissions]**에서 **"Read and write permissions"**를 선택하고 **[Save]**를 누릅니다.

### 4단계: 실행 확인
1. 상단 탭에서 **[Actions]**를 클릭합니다.
2. 왼쪽에서 **[Tube Sorter Manual Run]**을 선택하고, 오른쪽의 **[Run workflow]** 버튼을 클릭하여 실행합니다.

---

## 🚀 주요 기능

- **지능적 매칭**: 영상 제목의 공백과 대소문자를 무시하는 정규화($\text{Normalization}$) 및 긴 키워드 우선 매칭 알고리즘 적용.
- **멱등성($\text{Idempotency}$) 보장**: 재생목록 추가 전 중복 여부를 실시간으로 확인하여 동일 영상의 중복 등록을 원천 차단.
- **할당량 최적화**: 유튜브 API 할당량($\text{Quota}$)을 고려하여 실제 추가 작업 횟수 기준으로 처리량을 제한하고 효율적으로 통신.
- **완전 자동화**: GitHub Actions를 통해 매일 정기 실행 및 수동 트리거 지원.
- **상태 영속성**: 전용 데이터 브랜치(`state-tracking`)를 활용하여 코드 히스토리와 분리된 안정적인 작업 시점 관리.

---

## 🛠 로컬 설치 및 설정 (개발자용)

### 1. 환경 구축
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt
```

### 2. 설정 파일 준비
1. **`.env`**: 환경 변수 설정 (`.env.example` 참고)
   - `TARGET_CHANNEL_ID`: 모니터링할 유튜브 채널 ID
   - `MAX_PROCESS_COUNT`: 한 번에 처리할 영상 개수
2. **`rules.json`**: 분류 규칙 설정
   - `keyword`: 매칭할 단어 (예: "새벽", "주일")
   - `description`: 규칙 설명

---

## 🤖 GitHub Actions 자동화 상세

### 1. 실행 스케줄
- **정기 실행**: 매일 한국 시간(KST) 새벽 3시에 자동으로 실행됩니다.
- **수동 옵션**: `Actions` 탭에서 다음 변수를 직접 입력하여 실행할 수 있습니다.
  - `max_process_count`: 일시적으로 처리량을 늘리고 싶을 때 입력
  - `reset_state`: `true` 입력 시 처음부터 다시 분류 시작

### 2. 상태 저장 구조
자동화 실행 후의 마지막 작업 시점은 **`state-tracking`** 브랜치의 `state.json`에 스냅샷 형태로 저장됩니다.

---

## 🏗 시스템 아키텍처

- `models.py`: 도메인 데이터 구조 정의
- `youtube_service.py`: 유튜브 API 통신 및 멱등성 로직 전담
- `rule_engine.py`: 분류 및 매칭 비즈니스 로직
- `storage.py`: 파일 입출력 및 유효성 검사
- `sorter.py`: 전체 워크플로우 오케스트레이션

---

## 🧪 테스트 실행
```bash
PYTHONPATH=. pytest
```

**참고 문헌:**
- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud Console Help](https://support.google.com/cloud/answer/6158849)
