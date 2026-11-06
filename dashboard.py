
"""Local ChronosMatch monitoring dashboard.

Run with: python -m streamlit run dashboard.py
"""
from chronosmatch.simulator import run_simulation, generate_random_orders
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from chronosmatch.simulator import run_simulation


DB_PATH = Path("chronosmatch_dashboard.db")
RING_PATH = Path("chronosmatch_dashboard.ring")
AUDIT_COUNT = 1_000_000
AUDIT_CAPACITY = 8192


st.set_page_config(
    page_title="ChronosMatch",
    page_icon="📈",
    layout="wide",
)

st.title("ChronosMatch")
st.caption(
    "Zero-copy binary order pipeline · Matching engine · SQLite trade ledger"
)

# ---------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Simulation controls")
    st.write("Run the sample order flow through the matching engine.")

    run_clicked = st.button(
        "▶ Run simulation",
        type="primary",
        width="stretch",
    )

    run_audit = st.button(
        "Run 1,000,000-order IPC audit",
        width="stretch",
    )

    st.caption(
        "Simulation latency measures matching calls. "
        "The IPC audit measures a separate end-to-end workload."
    )


# ---------------------------------------------------------------------
# Existing simulation
# ---------------------------------------------------------------------

if run_clicked:
    # Start with fresh persistence files for each simulation.
    for path in (DB_PATH, RING_PATH):
        if path.exists():
            path.unlink()

    orders = generate_random_orders(count=100)

    with st.spinner("Processing 100 randomized orders..."):
        st.session_state["simulation_result"] = run_simulation(
            DB_PATH,
            RING_PATH,
            orders=orders,
        )


# ---------------------------------------------------------------------
# Million-order IPC benchmark
# ---------------------------------------------------------------------
st.divider()
st.header("Million-order performance benchmark")
st.caption(
    "Runs the IPC audit in a separate process. "
    "The audit's wall time includes process and IPC overhead."
)

if run_audit:
    # Clear the previous result so a failed run cannot look like
    # the newly requested benchmark succeeded.
    st.session_state.pop("ipc_audit_result", None)

    command = [
        sys.executable,
        "-m",
        "chronosmatch.ipc_audit",
        "--count",
        str(AUDIT_COUNT),
        "--capacity",
        str(AUDIT_CAPACITY),
    ]

    started = time.perf_counter()

    try:
        with st.spinner(
            f"Auditing {AUDIT_COUNT:,} orders. Please wait..."
        ):
            audit = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
                cwd=str(Path(__file__).resolve().parent),
            )

        elapsed = time.perf_counter() - started

        st.session_state["ipc_audit_result"] = {
            "output": audit.stdout,
            "errors": audit.stderr,
            "returncode": audit.returncode,
            "elapsed": elapsed,
            "count": AUDIT_COUNT,
        }

    except subprocess.TimeoutExpired:
        st.error("IPC audit timed out after 15 minutes.")
    except OSError as exc:
        st.error(f"Could not start the IPC audit: {exc}")


if "ipc_audit_result" in st.session_state:
    audit_result = st.session_state["ipc_audit_result"]

    count = audit_result["count"]
    elapsed = audit_result["elapsed"]
    returncode = audit_result["returncode"]

    # The requested count is not necessarily the verified count.
    # Display it as the requested workload, and retain the audit's
    # actual verification output below.
    throughput = count / elapsed if elapsed > 0 else 0
    amortized_us = elapsed * 1_000_000 / count

    if returncode == 0:
        st.success("IPC audit process exited successfully.")
    else:
        st.error(f"IPC audit failed with exit code {returncode}.")

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Orders requested", f"{count:,}")
    metric2.metric("Audit wall time", f"{elapsed:.3f} s")
    metric3.metric("Requested-count throughput", f"{throughput:,.0f}/s")

    st.metric(
        "Amortized audit time per requested order",
        f"{amortized_us:.2f} µs",
        help=(
            "Audit wall time divided by requested orders. "
            "This is not individual matching latency."
        ),
    )

    st.subheader("Audit output and verification")
    st.code(
        audit_result["output"] or "(No standard output)",
        language="text",
    )

    if audit_result["errors"]:
        with st.expander("Audit error output"):
            st.code(audit_result["errors"], language="text")

    st.caption(
        "Treat the audit as verified only if its output confirms "
        "the expected count, FIFO/checksum checks, and successful exit."
    )


# ---------------------------------------------------------------------
# Simulation results
# ---------------------------------------------------------------------
if "simulation_result" not in st.session_state:
    st.info(
        "Run the sample simulation from the sidebar to populate "
        "the order book, trade tape, and matching-latency sections."
    )
    st.stop()

result = st.session_state["simulation_result"]


# ---------------------------------------------------------------------
# Simulation metrics
# ---------------------------------------------------------------------
st.divider()
st.header("Simulation results")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Orders processed", f'{result["orders_processed"]:,}')
col2.metric("Trades executed", f'{result["trades_executed"]:,}')
col3.metric("Resting orders", f'{result["resting_order_count"]:,}')
col4.metric("Trades persisted", f'{result["trades_stored"]:,}')


# ---------------------------------------------------------------------
# Order book
# ---------------------------------------------------------------------
st.divider()
st.subheader("Order book")

bid_col, ask_col = st.columns(2)

bid_col.metric(
    "Best bid",
    result["best_bid"] if result["best_bid"] is not None else "—",
)
ask_col.metric(
    "Best ask",
    result["best_ask"] if result["best_ask"] is not None else "—",
)

resting_orders = result["resting_orders"]

if resting_orders:
    st.dataframe(
        pd.DataFrame(resting_orders),
        width="stretch",
        hide_index=True,
    )
else:
    st.write("No resting orders on the book.")


# ---------------------------------------------------------------------
# Trade tape
# ---------------------------------------------------------------------
st.divider()
st.subheader("Executed trades")

if DB_PATH.exists():
    with sqlite3.connect(DB_PATH) as connection:
        trades = pd.read_sql_query(
            """
            SELECT
                buy_order_id,
                sell_order_id,
                price_ticks,
                quantity,
                timestamp_ns
            FROM trades
            ORDER BY id
            """,
            connection,
        )

    if not trades.empty:
        st.dataframe(
            trades,
            width="stretch",
            hide_index=True,
        )
    else:
        st.write("No trades executed in this simulation.")
else:
    st.write("Trade ledger has not been created yet.")


# ---------------------------------------------------------------------
# Matching latency from the simulation
# ---------------------------------------------------------------------
st.divider()
st.subheader("Simulation matching latency")

latencies = result["latency_samples_ns"]

if latencies:
    latency_series = pd.Series(
        latencies,
        dtype="float64",
    )

    mean_ns = float(latency_series.mean())
    median_ns = float(latency_series.median())
    p95_ns = float(latency_series.quantile(0.95))
    p99_ns = float(latency_series.quantile(0.99))
    max_ns = float(latency_series.max())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Mean", f"{mean_ns:,.0f} ns")
    c2.metric("Median", f"{median_ns:,.0f} ns")
    c3.metric("P95", f"{p95_ns:,.0f} ns")
    c4.metric("P99", f"{p99_ns:,.0f} ns")
    c5.metric("Maximum", f"{max_ns:,.0f} ns")

    latency_df = pd.DataFrame(
        {
            "Order number": range(1, len(latencies) + 1),
            "Matching latency (ns)": latencies,
        }
    ).set_index("Order number")

    st.line_chart(latency_df, width="stretch")

    # A compact distribution view of the recorded latency samples.
    st.subheader("Matching latency distribution")
    st.bar_chart(
        latency_series.value_counts(
            bins=min(20, max(1, len(latency_series))),
            sort=False,
        ),
        width="stretch",
    )
else:
    st.info("No matching-latency samples were recorded by this simulation.")

st.caption(
    "Educational MVP. Simulation latency samples measure matching calls "
    "only. IPC audit wall time includes process and IPC overhead; "
    "the two measurements are not directly comparable."
)
