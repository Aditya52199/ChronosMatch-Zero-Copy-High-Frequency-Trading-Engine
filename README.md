# ChronosMatch --- Zero-Copy High-Frequency Trading Engine

ChronosMatch is an educational high-frequency trading engine prototype
developed in Python. It demonstrates binary order serialization,
limit-order matching, memory-mapped order transport, trade persistence,
latency measurement, and an interactive monitoring dashboard.

## Project Overview

The project implements a simplified trading pipeline that accepts
orders, serializes them into a fixed-size binary format, transports them
through a memory-mapped ring buffer, matches compatible buy and sell
orders, and stores executed trades in SQLite.

A Streamlit dashboard visualizes order-book state, trade executions, and
matching latency.

## Features

-   **Binary order serialization:** Fixed-size 29-byte order records
    using Python's `struct` module.
-   **Order validation:** Validation of order sides, numeric fields,
    prices, and quantities.
-   **Matching engine:** Limit-order matching with price priority,
    timestamp-based ordering, partial fills, and duplicate order-ID
    rejection.
-   **Memory-mapped ring buffer:** Fixed-capacity FIFO buffer for binary
    order records.
-   **Trade ledger:** SQLite persistence for executed trades.
-   **Simulation pipeline:** Integrates order transport, matching, and
    trade storage.
-   **Interactive dashboard:** Displays order-book metrics, resting
    orders, executed trades, and latency statistics.
-   **Performance benchmark:** Measures matching-call latency and
    reports mean, median, P95, P99, and maximum values.
-   **Automated testing:** Pytest coverage for core functionality and
    integration.

## Architecture

``` text
        Sample Orders
             |
             v
    Binary Order Format
       (29 bytes)
             |
             v
     Mmap Ring Buffer
             |
             v
      Matching Engine
             |
       +-----+------+
       |            |
       v            v
  Resting Book   Executed Trades
                      |
                      v
                SQLite Ledger

        Simulation Results
               |
               v
       Streamlit Dashboard
```

## Technology Stack

-   Python 3.13
-   `struct` --- binary serialization
-   `mmap` --- memory-mapped ring buffer
-   SQLite --- trade persistence
-   Streamlit --- interactive dashboard
-   Pandas --- tabular data display
-   Pytest --- automated testing
-   Git and GitHub --- version control

## Project Structure

``` text
ChronosMatch-Zero-Copy-High-Frequency-Trading-Engine/
├── src/
│   └── chronosmatch/
│       ├── __init__.py
│       ├── __main__.py
│       ├── order_format.py
│       ├── matching_engine.py
│       ├── ring_buffer.py
│       ├── ledger.py
│       └── simulator.py
├── tests/
│   ├── test_environment.py
│   ├── test_order_format.py
│   ├── test_matching_engine.py
│   ├── test_ring_buffer.py
│   └── test_simulator.py
├── dashboard.py
├── benchmark.py
├── pyproject.toml
├── .gitignore
└── README.md
```

## Setup and Installation

### 1. Clone the repository

``` bash
git clone <your-repository-url>
cd ChronosMatch-Zero-Copy-High-Frequency-Trading-Engine
```

Replace `<your-repository-url>` with your actual repository URL.

### 2. Create a virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the project and dependencies

``` powershell
python -m pip install -e .
python -m pip install streamlit pandas pytest
```

## Run the Simulation

Run the sample order flow:

``` powershell
python -m chronosmatch
```

The demonstration processes three sample orders and is expected to
generate two trades.

The output includes order and trade counts, best bid and ask, and
matching-call latency statistics.

## Launch the Dashboard

Run:

``` powershell
python -m streamlit run dashboard.py
```

Open the local URL displayed by Streamlit, typically
`http://localhost:8501`.

Click **Run simulation** to populate the dashboard.

The dashboard presents:

-   Processed order and executed trade counts
-   Best bid and best ask
-   Resting orders
-   Executed trades from SQLite
-   Mean and maximum matching latency
-   A matching-latency chart

## Run Automated Tests

Execute the test suite:

``` powershell
python -m pytest -q
```

The tests cover binary order encoding and validation, matching behavior,
ring-buffer operations, and simulation integration.

## Run the Performance Benchmark

Run a 1,000-iteration microbenchmark:

``` powershell
python benchmark.py --iterations 1000
```

Or use the default workload:

``` powershell
python benchmark.py
```

The benchmark reports:

-   Mean matching-call latency
-   Median latency
-   P95 latency
-   P99 latency
-   Maximum latency

Results depend on the machine, Python runtime, and benchmark workload.
Run multiple trials before drawing performance conclusions.

## Latency Measurement

The simulation uses `time.perf_counter_ns()` to measure elapsed time
around the matching-engine call.

These measurements represent matching-call duration, not end-to-end
order-processing latency. The microbenchmark also measures a specific
synthetic workload and does not establish production high-frequency
trading performance.

## Current Limitations

ChronosMatch is an educational MVP and is not suitable for live
financial trading.

-   The ring buffer is intended for single-process use without
    concurrent producer-consumer synchronization.
-   The matching engine uses Python data structures and is not a
    lock-free implementation.
-   The dashboard runs a sample simulation on demand rather than
    consuming a live market feed.
-   Risk controls, exchange connectivity, crash recovery, and
    comprehensive stress testing are not implemented.
-   Performance results require more extensive benchmarking before
    meaningful comparisons can be made.

## Future Improvements

-   Optimize order-book data structures.
-   Implement safe concurrent producer-consumer operations.
-   Add cancellation and replacement of orders.
-   Introduce risk checks and configurable trading limits.
-   Add larger-scale load tests and latency-distribution analysis.
-   Support live or simulated market-data feeds.
-   Improve dashboard refresh and monitoring capabilities.

## Development Workflow

Project development is maintained on the `devavarshita` branch.

To check the active branch:

``` powershell
git branch --show-current
```

To commit and push changes:

``` powershell
git add README.md
git commit -m "docs: update ChronosMatch documentation"
git push origin devavarshita
```

The `main` branch is kept separate from ongoing development.

## Conclusion

ChronosMatch demonstrates the design and integration of a simplified
trading-engine pipeline, from compact binary order representation
through matching and trade persistence to dashboard visualization and
performance measurement. It provides a foundation for further
exploration of low-latency systems, order-book algorithms, and
performance engineering.
