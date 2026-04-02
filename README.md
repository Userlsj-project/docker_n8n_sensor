# Docker Sensor Dashboard

Docker Compose로 구성한 센서 데이터 수집 · 모니터링 · 챗봇 시스템입니다.  
Python이 가상 센서 데이터를 생성하고, PostgreSQL에 저장하며, n8n 워크플로우로 자동 처리하고 Grafana로 시각화합니다.  
추가로 n8n Chat Trigger 기반의 규칙형 한국어 챗봇이 실시간 센서 데이터를 자연어로 답변합니다.

---

## 시스템 구성도

```mermaid
graph TD
    A([🐍 Python Simulator\n5초마다 랜덤 데이터 생성])
    B[(🗄️ PostgreSQL\nsensordb)]
    C[⚙️ n8n\nSensor Data Monitor\n10초 주기 자동 조회]
    D[📊 Grafana\n실시간 대시보드]
    E([💬 n8n Chatbot\nSensor Chatbot\n규칙 기반 한국어 응답])
    U((👤 사용자))

    A -->|INSERT 온도·습도·기압| B
    B -->|SELECT 최근 5건| C
    B -->|시계열 조회| D
    U -->|채팅 메시지 전송| E
    E -->|SELECT 최신/최근 5건| B
    B -->|센서 데이터 반환| E
    E -->|자연어 응답| U

    subgraph Docker Compose Network
        A
        B
        C
        D
        E
    end
```

---

## 챗봇 동작 흐름

```mermaid
flowchart LR
    MSG([사용자 메시지]) --> SW{키워드 감지}

    SW -->|"온도" 포함| Q1[(SELECT temperature\nLIMIT 1)]
    SW -->|"습도" 포함| Q2[(SELECT humidity\nLIMIT 1)]
    SW -->|"기압" 포함| Q3[(SELECT pressure\nLIMIT 1)]
    SW -->|"최근" 포함| Q4[(SELECT *\nLIMIT 5)]
    SW -->|그 외| D[안내 메시지]

    Q1 --> R1["현재 온도는 N°C 입니다."]
    Q2 --> R2["현재 습도는 N% 입니다."]
    Q3 --> R3["현재 기압은 NhPa 입니다."]
    Q4 --> R4["최근 5건 데이터 목록"]
    D  --> R5["온도·습도·기압·최근 중\n하나를 물어보세요"]

    R1 & R2 & R3 & R4 & R5 --> ANS([챗봇 응답])
```

---

## 데이터 흐름 시퀀스

```mermaid
sequenceDiagram
    participant P as 🐍 Python Simulator
    participant DB as 🗄️ PostgreSQL
    participant N as ⚙️ n8n Monitor
    participant G as 📊 Grafana
    participant U as 👤 사용자
    participant C as 💬 Chatbot

    loop 5초마다
        P->>DB: INSERT sensor_data (온도·습도·기압)
    end

    loop 10초마다
        N->>DB: SELECT 최근 5건
        DB-->>N: 센서 데이터 반환
    end

    loop 실시간
        G->>DB: 시계열 데이터 조회
        DB-->>G: 데이터 반환
        G->>G: 대시보드 갱신
    end

    U->>C: "지금 온도 알려줘"
    C->>DB: SELECT temperature LIMIT 1
    DB-->>C: 18.8°C
    C-->>U: "현재 온도는 18.8°C 입니다."
```

---

## 서비스 구성

| 서비스 | 이미지 | 포트 | 역할 |
|--------|--------|------|------|
| `postgresql` | postgres:15 | 5433 | 센서 데이터 저장 |
| `python-simulator` | python:3.11-slim | - | 가상 센서 데이터 생성 (5초 주기) |
| `n8n` | n8nio/n8n | 5678 | 워크플로우 자동화 + 챗봇 |
| `grafana` | grafana/grafana | 3001 | 데이터 시각화 |

---

## 센서 데이터

| 항목 | 범위 | 단위 |
|------|------|------|
| 온도 | 15.0 ~ 35.0 | °C |
| 습도 | 30.0 ~ 90.0 | % |
| 기압 | 980.0 ~ 1025.0 | hPa |

---

## n8n 워크플로우

### Sensor Data Monitor
- 10초마다 `sensor_data` 테이블에서 최근 5건을 자동 SELECT
- n8n UI에서 실행 이력 확인 가능

### Sensor Chatbot (신규)
- **Chat Trigger** 기반, API 키 불필요, 공개 채팅 URL 제공
- 한국어 키워드 감지 → PostgreSQL 조회 → 자연어 응답
- 엔드포인트: `http://localhost:5678/webhook/sensor-chatbot-001/chat`

| 키워드 | 동작 | 응답 예시 |
|--------|------|-----------|
| `온도` | 최신 온도 1건 조회 | 현재 온도는 18.8°C 입니다. |
| `습도` | 최신 습도 1건 조회 | 현재 습도는 61.7% 입니다. |
| `기압` | 최신 기압 1건 조회 | 현재 기압은 1020.3hPa 입니다. |
| `최근` | 최근 5건 전체 조회 | 최근 5건의 센서 데이터: ... |
| 그 외 | 안내 메시지 | 온도, 습도, 기압, 최근 중 하나를 물어보세요. |

---

## 실행 방법

### 1. 환경변수 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
POSTGRES_DB=sensordb
POSTGRES_USER=sensor_user
POSTGRES_PASSWORD=sensor_pass

GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

### 2. 컨테이너 실행

```bash
docker compose up -d
```

### 3. 서비스 접속

| 서비스 | URL |
|--------|-----|
| n8n | http://localhost:5678 |
| Grafana | http://localhost:3001 |
| 챗봇 엔드포인트 | http://localhost:5678/webhook/sensor-chatbot-001/chat |

### 4. n8n 초기 설정

1. `http://localhost:5678` 접속 후 계정 생성
2. **Credentials → Add Credential → PostgreSQL** 선택
3. 아래 정보 입력:
   - Host: `postgresql`
   - Port: `5432`
   - Database: `sensordb`
   - User: `sensor_user`
   - Password: `sensor_pass`
4. **Workflows → Import** → `n8n/workflow.json` 업로드 (모니터링 워크플로우)
5. **Workflows → Import** → `n8n/chatbot_workflow.json` 업로드 (챗봇 워크플로우)
6. 두 워크플로우 모두 **Activate**

### 5. 챗봇 테스트

```bash
# 온도 조회
curl -X POST http://localhost:5678/webhook/sensor-chatbot-001/chat \
  -H "Content-Type: application/json" \
  -d '{"action":"sendMessage","chatInput":"지금 온도 알려줘"}'

# 최근 5건 조회
curl -X POST http://localhost:5678/webhook/sensor-chatbot-001/chat \
  -H "Content-Type: application/json" \
  -d '{"action":"sendMessage","chatInput":"최근 데이터 보여줘"}'
```

### 6. 컨테이너 종료

```bash
docker compose down
```

---

## 프로젝트 구조

```
.
├── docker-compose.yml
├── .env                          # 환경변수 (git 제외)
├── postgresql/
│   └── init.sql                  # 테이블 초기화 스크립트
├── python/
│   ├── Dockerfile
│   └── sensor_simulator.py       # 센서 데이터 생성기 (5초 주기)
├── n8n/
│   ├── workflow.json             # Sensor Data Monitor (임포트용)
│   └── chatbot_workflow.json     # Sensor Chatbot (임포트용)
└── grafana/
    ├── dashboards/
    │   └── sensor.json           # 대시보드 정의
    └── provisioning/
        ├── dashboards/
        │   └── dashboard.yml
        └── datasources/
            └── postgresql.yml    # 데이터소스 자동 설정
```
