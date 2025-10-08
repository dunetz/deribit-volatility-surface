#!/usr/bin/env python3
"""
Streamlit app for Deribit volatility surface analysis.

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
from pathlib import Path

# Import our modules
from deribit_api import get_index_price, get_dvol_index, get_all_options_data, get_option_iv_data
from data_processing import clean_iv_data, separate_by_type, summarize_data
from surface_builder import create_simple_surface, create_rbf_surface, create_svi_surface
from metrics import calculate_surface_metrics
from snapshot import SurfaceSnapshot, SurfaceHistory
from visualizations import (plot_volatility_surface, plot_volatility_smile,
                           plot_term_structure, plot_heatmap, plot_greeks_surface_3d,
                           plot_surface_comparison, plot_difference_surface,
                           plot_metrics_timeseries)
from greeks import calculate_greeks_from_surface

# Page config
st.set_page_config(
    page_title="Deribit Volatility Surface",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">📈 Deribit Volatility Surface Analysis</p>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Configuration")

# Mode selection
mode = st.sidebar.radio(
    "Select Mode",
    ["Build Current Surface", "Analyze Historical Data"],
    help="Choose whether to build a new surface or analyze historical snapshots"
)

if mode == "Build Current Surface":
    st.sidebar.subheader("Surface Settings")

    currency = st.sidebar.selectbox(
        "Currency",
        ["BTC", "ETH"],
        help="Select cryptocurrency"
    )

    method = st.sidebar.selectbox(
        "Interpolation Method",
        ["rbf", "simple", "svi"],
        help="Surface construction method"
    )

    # Check if running on Streamlit Cloud
    is_cloud = os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_SERVER_HEADLESS')

    if is_cloud:
        st.sidebar.warning("⚠️ Snapshot saving disabled on Streamlit Cloud (ephemeral storage)")
        save_snapshot = False
        save_raw = False
    else:
        save_snapshot = st.sidebar.checkbox(
            "Save Snapshot",
            value=False,
            help="Save this snapshot to disk for historical analysis"
        )

        save_raw = st.sidebar.checkbox(
            "Save Raw Data",
            value=False,
            disabled=not save_snapshot,
            help="Save raw options data (requires Save Snapshot)"
        )

    # Build button
    if st.sidebar.button("🚀 Build Surface", type="primary"):
        with st.spinner(f"Fetching {currency} options data..."):
            try:
                # Get market data
                underlying_price = get_index_price(currency)
                dvol = get_dvol_index(currency)

                st.sidebar.success(f"Current {currency} price: ${underlying_price:,.2f}")
                if dvol:
                    st.sidebar.info(f"DVOL: {dvol:.2f}%")

                # Get options data
                instruments = get_all_options_data(currency)
                df = get_option_iv_data(instruments, underlying_price)

                # Clean data
                df = clean_iv_data(df)
                calls, puts = separate_by_type(df)

                # Calculate metrics
                metrics = calculate_surface_metrics(df, underlying_price)

                # Build surface
                st.sidebar.info(f"Building surface using {method.upper()} method...")

                if method == 'simple':
                    log_m_mesh, tte_mesh, iv_surf = create_simple_surface(calls, method='cubic')
                    svi_params = None
                elif method == 'rbf':
                    log_m_mesh, tte_mesh, iv_surf = create_rbf_surface(calls)
                    svi_params = None
                elif method == 'svi':
                    log_m_mesh, tte_mesh, iv_surf, svi_params = create_svi_surface(calls)

                # Calculate Greeks from smoothed surface
                st.sidebar.info("Calculating Greeks from smoothed IV surface...")
                try:
                    df = calculate_greeks_from_surface(
                        df, log_m_mesh, tte_mesh, iv_surf,
                        underlying_price, risk_free_rate=0.0
                    )
                    st.sidebar.success("Greeks calculated successfully")
                except Exception as e:
                    st.sidebar.warning(f"Warning: Error calculating Greeks: {e}")

                # Create snapshot
                snapshot = SurfaceSnapshot(
                    timestamp=datetime.now(),
                    currency=currency,
                    underlying_price=underlying_price,
                    dvol=dvol,
                    surface_data=(log_m_mesh, tte_mesh, iv_surf),
                    raw_options=df,
                    metrics=metrics
                )

                # Save if requested
                if save_snapshot:
                    history = SurfaceHistory()
                    history.save_snapshot(snapshot, save_raw=save_raw)
                    st.sidebar.success("Snapshot saved!")

                # Store in session state
                st.session_state['snapshot'] = snapshot
                st.session_state['df'] = df
                st.session_state['calls'] = calls
                st.session_state['puts'] = puts
                st.session_state['metrics'] = metrics

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

    # Display results if available
    if 'snapshot' in st.session_state:
        snapshot = st.session_state['snapshot']
        df = st.session_state['df']
        calls = st.session_state['calls']
        metrics = st.session_state['metrics']

        # Summary metrics
        st.header("📊 Market Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Underlying Price", f"${snapshot.underlying_price:,.2f}")
        with col2:
            if snapshot.dvol:
                st.metric("DVOL", f"{snapshot.dvol:.2f}%")
            else:
                st.metric("DVOL", "N/A")
        with col3:
            st.metric("Total Options", len(df))
        with col4:
            st.metric("Mean IV", f"{metrics['iv_mean']*100:.2f}%")

        # Key metrics
        st.header("🔑 Key Metrics")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("ATM Implied Volatility")
            atm_data = []
            for tenor in [7, 30, 60, 90, 180]:
                key = f'atm_iv_{tenor}d'
                if key in metrics and not pd.isna(metrics[key]):
                    atm_data.append({
                        'Tenor': f'{tenor}d',
                        'IV (%)': f"{metrics[key]*100:.2f}"
                    })
            if atm_data:
                st.dataframe(pd.DataFrame(atm_data), hide_index=True, use_container_width=True)

        with col2:
            st.subheader("Other Metrics")
            other_metrics = []
            if 'skew_25d' in metrics and not pd.isna(metrics['skew_25d']):
                other_metrics.append({'Metric': '25-Delta Skew', 'Value': f"{metrics['skew_25d']*100:.2f}pp"})
            if 'term_structure_slope' in metrics and not pd.isna(metrics['term_structure_slope']):
                other_metrics.append({'Metric': 'Term Structure Slope', 'Value': f"{metrics['term_structure_slope']*100:.2f}pp"})
            other_metrics.append({'Metric': 'IV Std Dev', 'Value': f"{metrics['iv_std']*100:.2f}pp"})
            if other_metrics:
                st.dataframe(pd.DataFrame(other_metrics), hide_index=True, use_container_width=True)

        # Visualizations
        st.header("📈 Volatility Surface Visualizations")

        # 3D Surface
        st.subheader(f"{snapshot.currency} Implied Volatility Surface ({method.upper()})")
        log_m_mesh, tte_mesh, iv_surf = snapshot.surface_data
        fig, _ = plot_volatility_surface(
            log_m_mesh, tte_mesh, iv_surf,
            snapshot.underlying_price,
            f'{snapshot.currency} Implied Volatility Surface ({method.upper()})'
        )
        st.pyplot(fig)

        # Heatmap
        st.subheader("Volatility Heatmap")
        fig, _ = plot_heatmap(log_m_mesh, tte_mesh, iv_surf, snapshot.underlying_price)
        st.pyplot(fig)

        # Smile and Term Structure
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Volatility Smile")
            fig, _ = plot_volatility_smile(calls)
            st.pyplot(fig)

        with col2:
            st.subheader("Term Structure")
            fig, _ = plot_term_structure(calls)
            st.pyplot(fig)

        # Greeks if available - prefer calculated Greeks (bs_*) over Deribit data
        greek_mapping = {
            'Delta': 'bs_delta' if 'bs_delta' in df.columns else 'delta',
            'Gamma': 'bs_gamma' if 'bs_gamma' in df.columns else 'gamma',
            'Vega': 'bs_vega' if 'bs_vega' in df.columns else 'vega'
        }

        available_greeks = [name for name, col in greek_mapping.items() if col in df.columns and df[col].notna().any()]

        if available_greeks:
            st.header("🎯 Greeks Surfaces")
            if any('bs_' in greek_mapping[name] for name in available_greeks):
                st.info("ℹ️ Greeks calculated from smoothed Black-Scholes model using interpolated IV surface")

            greek_tabs = st.tabs(available_greeks)

            for idx, greek_name in enumerate(available_greeks):
                with greek_tabs[idx]:
                    greek_col = greek_mapping[greek_name]
                    fig, _ = plot_greeks_surface_3d(df, snapshot.underlying_price, greek=greek_col)
                    st.pyplot(fig)

elif mode == "Analyze Historical Data":
    st.sidebar.subheader("Historical Analysis")

    analysis_type = st.sidebar.selectbox(
        "Analysis Type",
        ["List Snapshots", "Visualize Snapshot", "Compare Surfaces", "Metrics Time Series"],
        help="Select type of historical analysis"
    )

    currency_filter = st.sidebar.selectbox(
        "Filter by Currency",
        ["All", "BTC", "ETH"],
        help="Filter snapshots by currency"
    )

    # Load snapshots
    history = SurfaceHistory()
    currency_arg = None if currency_filter == "All" else currency_filter
    snapshots = history.load_all_snapshots(currency=currency_arg)

    if not snapshots:
        st.warning("No historical snapshots found. Build and save a surface first.")
        st.stop()

    if analysis_type == "List Snapshots":
        st.header("📋 Historical Snapshots")

        # Create dataframe
        snapshot_data = []
        for snap in snapshots:
            snapshot_data.append({
                'Timestamp': snap.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Currency': snap.currency,
                'Price': f"${snap.underlying_price:,.2f}",
                'DVOL': f"{snap.dvol:.2f}%" if snap.dvol else "N/A"
            })

        df_snapshots = pd.DataFrame(snapshot_data)
        st.dataframe(df_snapshots, use_container_width=True, hide_index=True)

        st.info(f"Total snapshots: {len(snapshots)}")

    elif analysis_type == "Visualize Snapshot":
        st.header("🔍 Visualize Historical Snapshot")

        # Select snapshot
        snapshot_labels = [f"{s.timestamp.strftime('%Y-%m-%d %H:%M')} ({s.currency})" for s in snapshots]
        snap_idx = st.selectbox("Select Snapshot", range(len(snapshots)),
                                format_func=lambda x: snapshot_labels[x])
        snapshot = snapshots[snap_idx]

        # Load raw data if available
        history.load_raw_data(snapshot)

        # Display snapshot info
        st.subheader("📊 Snapshot Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Timestamp", snapshot.timestamp.strftime('%Y-%m-%d %H:%M'))
        with col2:
            st.metric("Currency", snapshot.currency)
        with col3:
            st.metric("Price", f"${snapshot.underlying_price:,.2f}")
        with col4:
            if snapshot.dvol:
                st.metric("DVOL", f"{snapshot.dvol:.2f}%")
            else:
                st.metric("DVOL", "N/A")

        # Show metrics if available
        if snapshot.metrics:
            st.subheader("🔑 Key Metrics")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**ATM Implied Volatility**")
                atm_data = []
                for tenor in [7, 30, 60, 90, 180]:
                    key = f'atm_iv_{tenor}d'
                    if key in snapshot.metrics and not pd.isna(snapshot.metrics[key]):
                        atm_data.append({
                            'Tenor': f'{tenor}d',
                            'IV (%)': f"{snapshot.metrics[key]*100:.2f}"
                        })
                if atm_data:
                    st.dataframe(pd.DataFrame(atm_data), hide_index=True, use_container_width=True)

            with col2:
                st.markdown("**Other Metrics**")
                other_metrics = []
                if 'skew_25d' in snapshot.metrics and not pd.isna(snapshot.metrics['skew_25d']):
                    other_metrics.append({'Metric': '25-Delta Skew', 'Value': f"{snapshot.metrics['skew_25d']*100:.2f}pp"})
                if 'term_structure_slope' in snapshot.metrics and not pd.isna(snapshot.metrics['term_structure_slope']):
                    other_metrics.append({'Metric': 'Term Structure Slope', 'Value': f"{snapshot.metrics['term_structure_slope']*100:.2f}pp"})
                if 'iv_std' in snapshot.metrics:
                    other_metrics.append({'Metric': 'IV Std Dev', 'Value': f"{snapshot.metrics['iv_std']*100:.2f}pp"})
                if other_metrics:
                    st.dataframe(pd.DataFrame(other_metrics), hide_index=True, use_container_width=True)

        # Visualizations
        st.header("📈 Volatility Surface Visualizations")

        # 3D Surface
        if snapshot.surface_data:
            st.subheader(f"{snapshot.currency} Implied Volatility Surface")
            log_m_mesh, tte_mesh, iv_surf = snapshot.surface_data
            fig, _ = plot_volatility_surface(
                log_m_mesh, tte_mesh, iv_surf,
                snapshot.underlying_price,
                f'{snapshot.currency} Implied Volatility Surface - {snapshot.timestamp.strftime("%Y-%m-%d %H:%M")}'
            )
            st.pyplot(fig)

            # Heatmap
            st.subheader("Volatility Heatmap")
            fig, _ = plot_heatmap(log_m_mesh, tte_mesh, iv_surf, snapshot.underlying_price)
            st.pyplot(fig)

        # Smile and Term Structure if raw data available
        if snapshot.raw_options is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Volatility Smile")
                fig, _ = plot_volatility_smile(snapshot.raw_options)
                st.pyplot(fig)

            with col2:
                st.subheader("Term Structure")
                fig, _ = plot_term_structure(snapshot.raw_options)
                st.pyplot(fig)

            # Greeks if available - prefer calculated Greeks (bs_*) over Deribit data
            df = snapshot.raw_options
            greek_mapping = {
                'Delta': 'bs_delta' if 'bs_delta' in df.columns else 'delta',
                'Gamma': 'bs_gamma' if 'bs_gamma' in df.columns else 'gamma',
                'Vega': 'bs_vega' if 'bs_vega' in df.columns else 'vega'
            }

            available_greeks = [name for name, col in greek_mapping.items() if col in df.columns and df[col].notna().any()]

            if available_greeks:
                st.header("🎯 Greeks Surfaces")
                if any('bs_' in greek_mapping[name] for name in available_greeks):
                    st.info("ℹ️ Greeks calculated from smoothed Black-Scholes model using interpolated IV surface")

                greek_tabs = st.tabs(available_greeks)

                for idx, greek_name in enumerate(available_greeks):
                    with greek_tabs[idx]:
                        greek_col = greek_mapping[greek_name]
                        fig, _ = plot_greeks_surface_3d(df, snapshot.underlying_price, greek=greek_col)
                        st.pyplot(fig)
        else:
            st.info("ℹ️ Raw options data not available. Only surface-based plots are shown. To see smile, term structure, and Greeks, save snapshots with 'Save Raw Data' enabled.")

    elif analysis_type == "Compare Surfaces":
        st.header("🔄 Surface Comparison")

        if len(snapshots) < 2:
            st.warning("Need at least 2 snapshots for comparison")
            st.stop()

        col1, col2 = st.columns(2)

        snapshot_labels = [f"{s.timestamp.strftime('%Y-%m-%d %H:%M')} ({s.currency})" for s in snapshots]

        with col1:
            snap1_idx = st.selectbox("Select First Snapshot", range(len(snapshots)),
                                     format_func=lambda x: snapshot_labels[x])

        with col2:
            snap2_idx = st.selectbox("Select Second Snapshot", range(len(snapshots)),
                                     index=min(1, len(snapshots)-1),
                                     format_func=lambda x: snapshot_labels[x])

        snap1 = snapshots[snap1_idx]
        snap2 = snapshots[snap2_idx]

        # Price change
        price_change = ((snap2.underlying_price / snap1.underlying_price) - 1) * 100
        st.metric(
            "Price Change",
            f"${snap2.underlying_price:,.2f}",
            f"{price_change:+.2f}%",
            delta_color="normal"
        )

        # Comparison visualization
        st.subheader("Surface Comparison")
        fig = plot_surface_comparison(snap1, snap2,
                                      title1=snap1.timestamp.strftime('%Y-%m-%d'),
                                      title2=snap2.timestamp.strftime('%Y-%m-%d'))
        st.pyplot(fig)

        # Difference surface
        st.subheader("Surface Difference (IV Change)")
        fig = plot_difference_surface(snap1, snap2)
        st.pyplot(fig)

        # Metrics comparison
        st.subheader("Metrics Comparison")
        metrics_comp = []
        for key in snap1.metrics:
            if key in snap2.metrics:
                val1 = snap1.metrics[key]
                val2 = snap2.metrics[key]
                if val1 is not None and val2 is not None and not pd.isna(val1) and not pd.isna(val2):
                    change = (val2 - val1) * 100
                    metrics_comp.append({
                        'Metric': key,
                        'Before': f"{val1*100:.2f}%",
                        'After': f"{val2*100:.2f}%",
                        'Change': f"{change:+.2f}pp"
                    })

        if metrics_comp:
            st.dataframe(pd.DataFrame(metrics_comp), use_container_width=True, hide_index=True)

    elif analysis_type == "Metrics Time Series":
        st.header("📊 Metrics Time Series")

        if len(snapshots) < 2:
            st.warning("Need at least 2 snapshots for time series analysis")
            st.stop()

        fig = plot_metrics_timeseries(history)
        st.pyplot(fig)

        # Show data table
        if st.checkbox("Show Data Table"):
            ts_df = history.get_metrics_timeseries()
            st.dataframe(ts_df, use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This app analyzes cryptocurrency implied volatility surfaces using Deribit options data.

**Features:**
- Real-time surface construction
- Multiple interpolation methods
- Historical analysis
- Greeks visualization
""")
