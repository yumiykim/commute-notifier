# commute-notifier

마포역 5호선 → 종로3가역 3호선 → 충무로역 1번 출구.
수업 10분 전까지 출구에 도착할 수 있는 열차를 계산하여 디스코드로 안내합니다.

## 기능

- 서울교통공사 공식 역별 시간표 조회 (현재 운행표 기준, 실시간 지연 미반영)
- 동일 열차 번호·출발역·종착역을 기준으로 역별 시각 연결
- 종로3가 환승 3분, 충무로 1번 출구 도보 2분 반영
- 추천 열차 (추가 여유 3분)와 시간표상 마지막 가능한 열차 표시
- 한국 시간 전날 20:00, 당일 06:00 예약 발송
- 주말·한국 공휴일·등록한 휴강일 제외, 보강일 설정 지원
- 날짜와 발송 슬롯을 구분한 중복 방지, 네트워크 실패 시 비밀값 미출력

## 시간 기준

| 등교일 | 수업 시작 | 출구 도착 마감 |
|---|---|---|
| 월~목 | 10:00 | 09:50 |
| 금 | 13:00 | 12:50 |

전날 안내는 일~목 20:00, 당일 안내는 월~금 06:00입니다.
추천 도착 마감은 추가 여유 3분을 적용한 09:47 / 12:47입니다.
시간표가 달라질 수 있어 매번 조회하며 분 단위 반올림 대신 초까지 표시합니다.

## 구조

```text
commute/
  planner.py       # API와 독립적인 환승 계산
  seoul.py         # 역별 시간표 조회와 열차 연결
  calendar.py      # 공휴일·휴강·등교일 판단
  messages.py      # 디스코드 안내문
  discord.py       # 웹훅 발송
  delivery.py      # 발송 기록
  management/commands/
    notify_commute.py
    test_discord.py
  tests/
config/            # Django 설정과 로컬 상태 화면
calendar.json      # 휴강 및 보강일
scripts/           # GitHub Actions 기록 복원
.github/workflows/ # 테스트 및 예약 실행
```

## Windows 로컬 실행

```powershell
cd C:\WORKSPACE\commute-notifier
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env  # 이미 .env가 있다면 복사하지 마세요
```

`.env`에 `SEOUL_API_KEY`, `DISCORD_WEBHOOK_URL`을 직접 입력합니다.
서울시 공식 API는 HTTP를 사용해 인증키가 암호화되지 않은 경로로 전송됩니다.
프로젝트 소유자가 이 위험을 승인했습니다. `ALLOW_HTTP_SEOUL=true`로 명시적으로
허용하며, 이 설정이 없으면 API 조회를 차단합니다. API 주소와 인증키를 로그에 출력하지 않습니다.
타인이 사용할 경우 이 설정을 복사하기 전에 위험을 확인해야 합니다.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
# 실제 시간표 계산만: 디스코드로 보내지 않음
.\.venv\Scripts\python.exe manage.py notify_commute --slot morning --date 2026-10-06
# 개인 채널에 연결 확인 메시지 한 번 발송
.\.venv\Scripts\python.exe manage.py test_discord
# 다음 날 실제 안내 발송
.\.venv\Scripts\python.exe manage.py notify_commute --slot evening --send
```

`--send`가 없으면 항상 미리보기입니다. 휴강일은 API 조회와 발송을 생략합니다.
같은 날 같은 슬롯은 발송 기록이 있으면 재발송하지 않습니다.

## 무료 자동 실행 설정

1. 공개 GitHub 저장소에 코드를 업로드합니다.
2. Settings → Secrets and variables → Actions → New repository secret에 등록합니다.
   - `SEOUL_API_KEY`
   - `DISCORD_WEBHOOK_URL`
3. Actions → Commute notification → Run workflow에서 `date`를 등교일로 설정합니다.
   처음에는 `send`를 해제해 계산 결과를 확인합니다.
4. 같은 화면에서 `send`를 체크해 실제 채널 발송을 확인합니다.
5. 기본 브랜치의 예약 작업이 이후 자동으로 실행됩니다.

한국 시간 06:00 = 전날 UTC 21:00, 한국 시간 20:00 = UTC 11:00입니다.
GitHub Actions 표준 Linux 실행 환경만 사용하고 artifact는 최대 30일 보관합니다.
공개 저장소의 표준 실행 시간은 무료지만 저장 용량에도 한도가 있으므로 큰 파일을 저장하지 않습니다.
유료 서버·DB·도메인·대형 실행 환경·외부 유료 API는 사용하지 않습니다.

### 운영 한계

- GitHub 예약 실행은 정각을 보장하지 않으며 지연·누락될 수 있습니다.
- 공개 저장소는 60일 동안 저장소 활동이 없으면 예약 작업이 자동 중지될 수 있습니다.
- 실행 실패는 GitHub Actions에서 확인합니다. API 실패 시 예시 시각을 대신 보내지 않습니다.
- 발송 기록은 Actions artifact로 복원합니다. 기록 복원이 실패하면 중복 방지를 위해 발송을 중단합니다.
- 발송 전 `pending`을 기록하고 성공 후 `sent`로 바꿉니다. 발송 도중 연결이 끊기면
  수신 여부가 불확실하므로 자동 재발송하지 않습니다. 채널을 확인한 뒤 기록을 처리해야 합니다.
- 발송 후 기록 업로드까지 실패하거나 artifact가 만료되면 중복 방지가 완전하지 않습니다.
  Discord 웹훅과 artifact 저장은 하나의 트랜잭션이 아니므로 정확히 한 번 발송을 보장하지 않습니다.
- 시간표는 미래 특정 날짜의 개정 예정 시간표가 아닌 조회 시점의 요일별 운행표입니다.
- 전날 안내는 내일 날짜로 계산합니다. 자정~06시 전으로 지연된 저녁 작업은 당일 날짜를 사용합니다. 허용 시간대를 벗어난 예약 작업은 중단합니다.
- 공휴일 라이브러리에 아직 반영되지 않은 임시 공휴일은 `extra_holidays`에 등록합니다.

## 휴강·보강 설정

`calendar.json`에서 날짜를 등록합니다. 아래는 형식 예시이며 기본 파일은 빈 목록입니다.

```json
{
  "skip_dates": ["2026-10-06"],
  "extra_holidays": ["2026-11-02"],
  "class_overrides": {"2026-10-10": "10:00:00"}
}
```

`skip_dates`는 최우선 휴강이며 `class_overrides`는 공휴일·주말에도 수업을 설정할 수 있습니다.
보강일에도 실제 운행일의 토요일·공휴일 시간표를 선택합니다.

## 검증

계산의 환승 3분 경계, 출구 마감 초과, 늦은 출발 선택, 주간 수업,
열차 식별자 매칭, 중복·비정상 시각, 공휴일 보강, 휴강, 날짜 경계,
슬롯별 발송 기록을 테스트합니다. 실제 API와 디스코드 연결은 로컬에서 별도로 검증했습니다.
CI는 API 키 없이 실행됩니다.

## 데이터 출처

- [서울교통공사 역별 열차 시간표 / 서울 열린데이터광장](https://data.seoul.go.kr/dataList/OA-101/A/1/datasetView.do)
- [서울시 역명으로 역 검색](https://data.seoul.go.kr/dataList/OA-121/A/1/datasetView.do)
- [디스코드 웹훅](https://docs.discord.com/developers/resources/webhook)
- [GitHub Actions 요금](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [GitHub 예약 실행](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

서울교통공사 데이터를 서울 열린데이터광장을 통해 이용합니다. 실제 지연·혼잡·환승 속도에 따라 결과와 차이가 있습니다.
