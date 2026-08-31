# Briar Bot (Idea by 김동현)

친구들의 군생활 일정과 휴가를 Discord 안에서 공유하는 한국어 중심 Discord Bot입니다. 군생활 프로필, 휴가·외출·외박 일정, 월간 공용 캘린더, 휴가 겹침, 전역 순위, 자동 알림을 제공합니다.

## 주요 기능

- `/군생활 등록`, `/군생활 정보`: 군종별 전역일 자동 추정, 복무율/D-Day 확인
- `/일정 등록`, `/일정 목록`, `/일정 수정`, `/일정 삭제`: 본인 일정 CRUD
- `/캘린더`: 서버 전체 일정 월간 보기 및 이전/이번/다음 달 버튼
- `/이번주`, `/다음휴가`, `/겹치는휴가`, `/전역랭킹`, `/도움`
- `/설정 알림채널`, `/설정 알림켜기`, `/설정 알림끄기`: 관리자 전용 자동 알림 설정
- 휴가 전날·시작일·종료일, 전역 당일 알림. SQLite unique log로 중복 발송 방지

모든 날짜 계산은 기본 `Asia/Seoul` 기준이며, 서버별 데이터는 `guild_id`로 분리됩니다. Message Content Intent는 사용하지 않습니다.

## 준비: Discord 애플리케이션 만들기

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 New Application을 만듭니다.
2. Bot 메뉴에서 Bot을 만들고 토큰을 발급합니다. 토큰은 절대 Git에 올리지 않습니다.
3. OAuth2 URL Generator에서 `bot`과 `applications.commands` scope를 선택합니다.
4. 권한은 최소한 `View Channels`, `Send Messages`, `Embed Links`를 선택하고 서버에 초대합니다.
5. Privileged Gateway Intents는 켜지 않아도 됩니다.
6. Application ID는 General Information의 Application ID입니다.

## 환경 변수

`.env.example`을 `.env`로 복사하고 값을 채웁니다.

```env
DISCORD_TOKEN=봇_토큰
DISCORD_APPLICATION_ID=애플리케이션_ID
# 개발 중에는 즉시 반영을 위해 입력하고, 운영 global sync에서는 비워둡니다.
DISCORD_DEV_GUILD_ID=개발_서버_ID
DATABASE_URL=sqlite:////data/briar.db
TZ=Asia/Seoul
LOG_LEVEL=INFO
```

## Docker Compose 실행 (권장)

```bash
cp .env.example .env
# .env 편집
docker compose up -d --build
docker compose logs -f briar
```

컨테이너 시작 시 `alembic upgrade head`가 먼저 실행됩니다. `./data:/data` 볼륨에 SQLite 파일을 저장하므로 컨테이너를 다시 만들어도 데이터가 유지됩니다.

```bash
docker compose down
git pull
docker compose up -d --build
```

데이터 백업은 봇을 잠시 멈춘 뒤 SQLite 파일과 WAL 파일을 함께 복사하는 방식이 안전합니다.

```bash
docker compose stop
mkdir -p backup
cp data/briar.db backup/briar-$(date +%Y%m%d-%H%M%S).db
docker compose start
```

## 로컬 실행

Python 3.12 이상을 사용합니다.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

SQLite를 프로젝트 폴더에 두려면 로컬 `.env`에서 `DATABASE_URL=sqlite:///./data/briar.db`로 바꿉니다.

## 명령어 예시

```text
/군생활 등록 입대일:2026-10-13 군종:육군
/군생활 정보
/일정 등록 종류:휴가 제목:성탄절 휴가 시작일:2026-12-24 종료일:2026-12-28
/일정 목록
/캘린더
/다음휴가
/겹치는휴가
/전역랭킹
/도움
/설정 알림채널
```

`/일정삭제`와 `/일정수정`은 본인이 등록한 일정만 대상으로 합니다. 날짜는 `YYYY-MM-DD` 형식이며 시작일이 종료일보다 늦으면 사용자 친화적인 오류 Embed를 반환합니다.

군종별 기본 추정 복무기간은 육군·해병대 18개월, 해군 20개월, 공군 21개월, 사회복무요원 21개월입니다. 이는 병무청 안내 기준의 기본값이며, 실제 전역일이 달라지는 경우 `/군생활 등록`의 `전역예정일` 선택 옵션으로 직접 덮어쓸 수 있습니다. [병무청 병역이행 안내서](https://mma.go.kr/download/ebook/2024%EB%85%84%20병역이행%20안내서.pdf)

## 테스트와 검증

```bash
pytest
python -m compileall app migrations
docker compose config
docker compose build
```

테스트는 날짜 검증, 복무율 경계값, 다음 휴가, 실제 날짜 구간 교집합, 월 경계 캘린더를 검증합니다.

## 프로젝트 구조

```text
app/
  bot/                 Discord Bot, Cogs, Button Views
  database/            SQLAlchemy Base, models, sessions
  services/            군생활·일정·캘린더·알림 도메인 로직
  scheduler/           KST 기준 일일 알림
  utils/               날짜와 Embed 공통 도구
migrations/            Alembic migration
tests/                 핵심 도메인 로직 테스트
```

흐름은 `Discord UI → Service → Database`로 유지했습니다. 운영 로그는 `docker compose logs -f briar`로 확인할 수 있고, 내부 오류의 traceback은 로그에만 남으며 Discord 사용자에게 노출되지 않습니다.
