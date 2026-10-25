# \# ChronosMatch — High-Performance Order Matching Engine

# 

# ChronosMatch is an educational trading-engine MVP built to demonstrate binary order serialization, price-time-priority matching, an mmap-backed ring buffer, trade persistence, latency measurement, and an interactive dashboard.

# 

# \## Features

# 

# \- \*\*Binary order format:\*\* Fixed-size 29-byte order records using Python's `struct` module.

# \- \*\*Order validation:\*\* Checks order fields and rejects invalid binary order data.

# \- \*\*Matching engine:\*\* Limit-order matching with price priority, timestamp ordering, partial fills, and duplicate order-ID protection.

# \- \*\*Mmap-backed ring buffer:\*\* Fixed-capacity FIFO transport for serialized orders.

# \- \*\*Trade ledger:\*\* SQLite persistence for executed trades.

# \- \*\*Latency measurements:\*\* Records matching duration in nanoseconds.

# \- \*\*Interactive dashboard:\*\* Streamlit dashboard showing order-book metrics, resting orders, executed trades, and latency samples.

# \- \*\*Automated tests:\*\* Pytest coverage for serialization, matching, buffering, and simulation integration.

# 

# \## Architecture

# 

# ```text

# Sample Orders

# &#x20;    |

# &#x20;    v

# Binary Order Format

# &#x20;    |

# &#x20;    v

# Mmap Ring Buffer

# &#x20;    |

# &#x20;    v

# Matching Engine

# &#x20;    |

# &#x20;    +------> Resting Order Book

# &#x20;    |

# &#x20;    v

# Executed Trades

# &#x20;    |

# &#x20;    v

# SQLite Trade Ledger

# 

# Simulation Results

# &#x20;    |

# &#x20;    v

# Streamlit Dashboard

# ```

# 

# \## Technology Stack

# 

# \- Python 3.13

# \- `struct` and `mmap`

# \- SQLite

# \- Streamlit

# \- Pandas

# \- Pytest

# 

# \## Setup

# 

# Create and activate a virtual environment.

# 

# \### Windows PowerShell

# 

# ```powershell

# python -m venv .venv

# .\\.venv\\Scripts\\Activate.ps1

# python -m pip install -e .

# python -m pip install streamlit pandas pytest

# ```

# 

# \## Run the simulation

# 

# ```powershell

# python -m chronosmatch

# ```

# 

# The sample simulation submits three orders and demonstrates two trades.

# 

# \## Launch the dashboard

# 

# ```powershell

# python -m streamlit run dashboard.py

# ```

# 

# Open the local URL printed by Streamlit, typically `http://localhost:8501`, and click \*\*Run simulation\*\*.

# 

# \## Run tests

# 

# ```powershell

# python -m pytest -q

# ```

# 

# \## Latency interpretation

# 

# The simulator measures elapsed time around the matching-engine call using `time.perf\_counter\_ns()`. These measurements represent matching-call duration for the sample workload, not end-to-end pipeline latency or a statistically rigorous performance benchmark.

# 

# \## Current limitations

# 

# This is an educational MVP, not a production trading system. The ring buffer is designed for single-process use without concurrent producer/consumer synchronization. The matching engine uses Python data structures and is not lock-free. The dashboard runs a sample simulation on demand rather than consuming a continuous live market feed.

# 

# Production deployment would require additional concurrency controls, risk checks, robust recovery, market-data integration, stress testing, and reproducible benchmarking.

# 

# \## Development branch

# 

# Development is performed on `devavarshita`. The `main` branch is kept separate.



