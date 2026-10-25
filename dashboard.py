
"""Local ChronosMatch monitoring dashboard.

Run with: streamlit run dashboard.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from chronosmatch.simulator import run_simulation


DB_PATH = Path("chronosmatch_dashboard.db")
RING_PATH = Path("chronosmatch_dashboard.ring")


st.set_page_config(
    page_title="ChronosMatch",
    page_icon="📈",
    layout="wide",
)

st.title("ChronosMatch")
st.caption("Zero-copy binary order pipeline · Matching engine · SQLite trade ledger")

with st.sidebar:
    st.header("Simulation controls")
    st.write("Run the sample order flow through the engine.")
    run_clicked = st.button(
        "▶ Run simulation",
        type="primary",
        use_container_width=True,
    )
    st.caption("This demo measures matching time, not end-to-end latency.")

if run_clicked:
    # Start each dashboard run with fresh persistence files.
    for path in (DB_PATH, RING_PATH):
        if path.exists():
            path.unlink()

    with st.spinner("Processing orders..."):
        st.session_state["simulation_result"] = run_simulation(
            DB_PATH,
            RING_PATH,
        )

if "simulation_result" not in st.session_state:
    st.info("Click **Run simulation** to populate the dashboard.")
    st.stop()

result = st.session_state["simulation_result"]

# Main metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Orders processed", result["orders_processed"])
col2.metric("Trades executed", result["trades_executed"])
col3.metric("Resting orders", result["resting_order_count"])
col4.metric("Trades persisted", result["trades_stored"])

st.divider()

# Order book summary
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
        use_container_width=True,
        hide_index=True,
    )
else:
    st.write("No resting orders on the book.")

st.divider()

# Trade tape
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
        st.dataframe(trades, use_container_width=True, hide_index=True)
    else:
        st.write("No trades executed in this run.")
else:
    st.write("Trade ledger has not been created yet.")

st.divider()

# Matching latency
st.subheader("Matching latency")

latencies = result["latency_samples_ns"]
latency_col1, latency_col2 = st.columns(2)
latency_col1.metric("Mean latency", f'{result["latency_mean_ns"]:,} ns')
latency_col2.metric("Maximum latency", f'{result["latency_max_ns"]:,} ns')

if latencies:
    latency_df = pd.DataFrame({
        "Order number": range(1, len(latencies) + 1),
        "Latency (ns)": latencies,
    }).set_index("Order number")
    st.line_chart(latency_df)

st.caption(
    "Educational MVP: Python matching engine with an mmap-backed "
    "single-process ring buffer. Latency samples cover matching only."
)
