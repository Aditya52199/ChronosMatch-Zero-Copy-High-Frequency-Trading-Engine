# ChronosMatch — Zero-Copy High-Frequency Trading Engine

ChronosMatch is an educational trading-engine project exploring binary order serialization, memory-mapped buffers, order matching, cross-process communication, trade persistence, latency measurement, and interactive monitoring.

The project combines a Python matching engine with an optional Cython extension, an asyncio order firehose, a separate-process IPC audit, SQLite trade ledgers, and two monitoring interfaces.

> **Project status:** Educational MVP. Benchmark results are machine- and workload-dependent. This project is not designed or validated for live financial trading.

## Project Overview

The system accepts orders, serializes them into fixed-size binary records, processes orders through a matching pipeline, and persists executed trades to SQLite.

It includes a core in-memory simulation, a Streamlit dashboard, a terminal dashboard, an asyncio throughput benchmark, and an mmap-based cross-process IPC audit.

## Features

- **Binary order serialization:** Fixed-size 29-byte order records using Python's `struct` module.
- **Order validation:** Checks order sides, numeric fields, prices, and quantities.
- **Matching engine:** Limit-order matching with price priority, timestamp-based ordering, partial fills, and duplicate order-ID rejection.
- **Memory-mapped ring buffer:** Fixed-capacity binary record transport for the core simulation.
- **Cython matching engine:** Compiled matching implementation for comparative performance testing.
- **Asyncio firehose:** Measures single-process producer-consumer throughput using binary records and a bounded `asyncio.Queue`.
- **Cross-process IPC audit:** Transfers one million orders between processes using mmap-backed binary records, verifies FIFO ordering and checksums, and checks for missing or duplicate IDs.
- **Trade persistence:** Stores executed trades in SQLite.
- **Async ledger:** Uses a bounded asynchronous queue and background batched database writes.
- **Separate-process ledger:** Transfers trade records to a dedicated ledger process using a memory-mapped trade buffer.
- **Latency measurement:** Uses `time.perf_counter_ns()` for matching-call measurements.
- **Streamlit dashboard:** Displays simulation metrics, order-book state, trade executions, and latency charts.
- **Terminal dashboard:** Provides an interactive view of the sample matching simulation.
- **Automated tests:** Covers order serialization, matching, buffers, simulations, Cython parity, IPC auditing, and ledger workflows.

## Architecture

```text
                         Sample Orders
                              |
                              v
                    Binary Order Format
                         29 bytes
                              |
                              v
                     Mmap Ring Buffer
                              |
                              v
                      Matching Engine
                      Python / Cython
                              |
                    +---------+---------+
                    |                   |
                    v                   v
                Resting Book       Executed Trades
                                        |
                         +--------------+--------------+
                         |                             |
                         v                             v
                   SQLite Ledger               Ledger Pipelines
                                                Async / Process

                  Simulation and Benchmark Results
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             Streamlit Dashboard   Terminal Dashboard

     Separate performance paths:
     Asyncio Firehose | Cross-Process IPC Audit
```

The firehose and IPC audit are separate benchmarks. The asyncio firehose measures communication within one process; the IPC audit measures a producer-consumer workflow across processes.

## Technology Stack

- Python 3.13
- `struct` — binary serialization
- `mmap` — memory-mapped record transport
- `asyncio` — asynchronous producer-consumer processing
- Cython — compiled matching-engine implementation
- SQLite — trade persistence
- Streamlit and Pandas — interactive dashboard and tabular display
- `curses` / `windows-curses` — terminal interface
- Pytest — automated tests
- Git — version control

## Project Structure

```text
ChronosMatch-Zero-Copy-High-Frequency-Trading-Engine/
├── src/
│   └── chronosmatch/
│       ├── __init__.py
│       ├── __main__.py
│       ├── order_format.py
│       ├── matching_engine.py
│       ├── matching_engine_cy.pyx
│       ├── ring_buffer.py
│       ├── ledger.py
│       ├── simulator.py
│       ├── ipc_audit.py
│       ├── async_ledger.py
│       └── process_ledger.py
├── tests/
│   ├── test_environment.py
│   ├── test_order_format.py
│   ├── test_matching_engine.py
│   ├── test_ring_buffer.py
│   ├── test_simulator.py
│   ├── test_ipc_audit.py
│   ├── test_cython_parity.py
│   ├── test_async_ledger.py
│   ├── test_async_simulator.py
│   └── test_process_ledger.py
├── dashboard.py
├── terminal_dashboard.py
├── asyncio_firehose.py
├── benchmark.py
├── benchmark_cython.py
├── benchmark_process_ledger.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and Installation

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies and the project

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

If the project configuration does not install all optional development dependencies, install the packages listed in `requirements.txt` and resolve any missing package reported by the relevant command.

### 3. Build the Cython extension

```powershell
python setup.py build_ext --inplace
```

This builds the compiled extension used for Cython performance comparisons. A successful build does not mean every part of the matching engine executes as native C code.

## Run the Simulation

Run the sample order flow:

```powershell
python -m chronosmatch
```

The simulation exercises the core order-processing and matching pipeline and reports order/trade information and matching latency.

## Launch the Dashboards

### Streamlit dashboard

```powershell
python -m streamlit run dashboard.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

Use **Run simulation** to display the sample simulation results. The dashboard includes order and trade metrics, resting orders, and matching latency statistics.

The dashboard also includes a button to run the one-million-order IPC audit. This is a separate benchmark, not a million-order rendering of the sample order book.

### Terminal dashboard

```powershell
python terminal_dashboard.py
```

The terminal interface provides an interactive view of the sample order flow.

Available controls:

- **Space / Enter / Right Arrow:** Step through the simulation.
- **A:** Run automatically.
- **R:** Restart the simulation.
- **Q / Esc:** Quit.

Terminal rendering requires a compatible terminal. Windows installations may need the `windows-curses` dependency.

## Run Automated Tests

```powershell
python -m pytest -q
```

The suite covers binary order encoding, order validation, matching behavior, ring-buffer operations, simulation integration, Cython parity, asynchronous ledger behavior, IPC auditing, and separate-process ledger functionality.

A previously completed run reported **46 passing tests**. Run the suite in your current environment to verify the latest code.

## Performance Benchmarks

Benchmark results depend on the processor, operating system, Python version, build configuration, and workload. Use them as measurements of these implementations, not as guarantees of production performance.

### 1. Python matching benchmark

```powershell
python benchmark.py --iterations 1000
```

Run the default workload with:

```powershell
python benchmark.py
```

The benchmark reports matching-call latency statistics, including mean, median, P95, P99, and maximum values.

### 2. Cython comparison

Build the extension first:

```powershell
python setup.py build_ext --inplace
```

Then run:

```powershell
python benchmark_cython.py
```

Compare Python and Cython results under the same workload. The Cython implementation still interacts with Python objects and data structures; it should not be described as a fully native, GIL-free matching loop.

### 3. Asyncio firehose

```powershell
python asyncio_firehose.py --count 100000 --capacity 8192
```

This benchmark measures single-process producer-consumer throughput using binary records and an `asyncio.Queue`. It is not an inter-process communication benchmark.

### 4. One-million-order IPC audit

```powershell
python -m chronosmatch.ipc_audit --count 1000000 --capacity 8192
```

The audit reports orders sent and received, elapsed time, end-to-end throughput, ID and quantity checksums, FIFO verification, and missing/duplicate ID checks.

The order transport uses mmap-backed binary records. The order path avoids pickle serialization; this does not mean every control or result message in the program is pickle-free.

### 5. Separate-process ledger benchmark

```powershell
python benchmark_process_ledger.py --levels 128 --sweeps 50 --capacity 64 --batch-size 32
```

This benchmark measures a small matching-and-persistence workload involving a separate ledger process. Its end-to-end throughput includes process and persistence overhead, so it should not be compared directly with the asyncio firehose rate.

### 6. Asynchronous ledger

The asynchronous ledger implementation is available in `src/chronosmatch/async_ledger.py`. Its behavior is covered by the automated tests. The asynchronous ledger and the separate-process ledger are distinct implementations.

## Recorded Benchmark Results

The following results were observed during development on the project author's environment. They are reference measurements, not portable performance guarantees.

| Workload | Observed result |
|---|---:|
| Asyncio firehose, 100,000 records | 188,130 orders/sec |
| Cross-process IPC audit, 1,000,000 orders | 115,479 orders/sec |
| Separate-process ledger benchmark | 347 orders/sec |
| Separate-process ledger trades persisted | 128 of 128 |
| Automated tests | 46 passed |

The IPC audit verified the expected and actual ID checksums, FIFO sequence, and absence of detected missing or duplicate IDs. The firehose verified its sequence and checksums.

These throughput figures measure different workloads and must not be interpreted as equivalent benchmarks.

## Latency Measurement

Matching-call duration is measured with `time.perf_counter_ns()`. The reported latency measures the matching-engine call under the benchmark's specific conditions.

It does not automatically include the complete time spent serializing, transporting, matching, scheduling other processes, and persisting a trade. Maximum latency can include scheduling or other system-level delays.

A sub-millisecond target should therefore be evaluated against the exact operation and measurement boundaries. These benchmarks do not establish that every operation—or the entire order-to-ledger pipeline—completes within one