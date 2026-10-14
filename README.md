# Trading Platform Starter

A multi-service starter project with a React/TypeScript frontend, C++ matching-engine demo, Go API gateway, Java/Spring Boot OMS skeleton, Python market-data and risk services, and local infrastructure.

## Important
This is an educational starter, **not a production-ready exchange**. It does not connect to a real broker or exchange, and the matching engine is a simplified demonstration. Before handling real money or user data, add security review, persistence, authentication hardening, observability, reconciliation, regulatory controls, and comprehensive tests.

## Requirements
- Node.js 20+
- Go 1.22+
- C++17 compiler and CMake
- Python 3.11+
- Java 17+ and Maven
- Docker Compose (optional)

## Quick start: frontend
```bash
cd frontend
npm install
npm run dev
```
The frontend uses mock market data and a local UI. The gateway is a separate service.

## Gateway
```bash
cd gateway-service
go run ./cmd/server
```
Default address: `http://localhost:8080`

## Python services
```bash
cd market-data-service
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/publisher.py
```
In another terminal:
```bash
cd risk-engine
pip install -r requirements.txt
python src/monitor.py
```

## Matching engine
```bash
cd matching-engine
cmake -S . -B build
cmake --build build
./build/matching_engine
```

## OMS
```bash
cd oms-service
mvn spring-boot:run
```

## Configuration
Use environment variables for secrets and deployment-specific settings. Never commit credentials.
