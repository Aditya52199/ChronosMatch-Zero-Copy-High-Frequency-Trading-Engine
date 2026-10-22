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

## ChronosMatch shared-memory prototype

The Python/Cython prototype is separate from the C++ demo above. It uses a fixed-width binary SPSC ring (`mmap` + `struct`) and integer price/quantity units. Each 24-byte order record is `<Qqq`: 8-byte order ID, 8-byte price ticks, and 8-byte quantity lots. Side and order type occupy the order ID's top two bits, leaving a 62-bit order identifier. A small versioned header stores the ring capacity and producer/consumer indexes. The ring avoids JSON/Pickle copies; this educational prototype does **not** provide interprocess atomic memory ordering, crash recovery, multi-producer safety, exchange connectivity, or a sub-50 μs performance guarantee. Benchmark on the target OS and hardware before drawing latency conclusions.

From the repository root, create one ring file, then run the consumer and producer in separate terminals:

```powershell
cd matching-engine
..\.venv\Scripts\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-chronosmatch.txt
.venv\Scripts\python.exe setup.py build_ext --inplace
.venv\Scripts\python.exe -c "from chronosmatch.protocol import SharedOrderRing; SharedOrderRing('chronosmatch.ring', create=True).close()"
```

Terminal 1 (consumer/dashboard):

```powershell
.venv\Scripts\python.exe -m chronosmatch.monitor --path chronosmatch.ring
```

Terminal 2 (100,000-order asyncio firehose, paced toward 100,000 orders/second):

```powershell
.venv\Scripts\python.exe -m chronosmatch.simulator --path chronosmatch.ring --orders 100000 --rate 100000
```

Press `q` to exit the curses monitor. When curses is unavailable (including a default Windows Python install), the monitor falls back to periodic plain-text summaries; install `windows-curses` in the prototype environment to enable the full-screen display. The ring supports one producer and one consumer only, and should be recreated before starting a new run.

The producer uses bounded batches and backpressure: run the consumer first. If the ring stays full without progress for five seconds, it exits with an error. Its completion line reports achieved throughput and full-ring retries; 100,000 orders/second is a target that depends on the OS and hardware, not a guaranteed rate.

## OMS
```bash
cd oms-service
mvn spring-boot:run
```

## Configuration
Use environment variables for secrets and deployment-specific settings. Never commit credentials.
