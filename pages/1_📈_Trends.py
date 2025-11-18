import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import altair as alt
import time

# ---PAGE SETUP----
st.set_page_config(page_title="Google Trends Insights", layout="wide")


st.title("Trends Insights")
st.caption("Know what's trending")
st.divider()

st.write("Select a niche/keyword to view its search trends in India.")
niche = st.text_input("Enter a niche or keyword (e.g., women's fashion, sneakers, kurti, skincare):")

if st.button("Get Trends"):
    
    if not niche.strip():
        st.warning("Please enter a keyword.")
        st.stop()

    # -------------------------
    # fetch trends
    time.sleep(3)
    st.spinner("Getting you the latest trends information")
    pytrends = TrendReq(hl='en-US', tz=330)
    pytrends.build_payload([niche], timeframe='today 12-m', geo='IN')

   
    # Interest Over Time
   
    st.subheader("Interest Over Time")
    try:
        data = pytrends.interest_over_time()
        if data.empty:
            st.info("No trend data available for this keyword currently.")
        else:
            data = data.reset_index()
            chart = alt.Chart(data).mark_line().encode(
                x="date:T",
                y=f"{niche}:Q"
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching trend data: {e}")

    
    # Regional Interest
    st.subheader(f"Top States Searching for {niche}  ")

    try:
        time.sleep(2)
        region_df = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True)
        region_df = region_df.sort_values(by=niche, ascending=False).head(10)

        if not region_df.empty:
            st.bar_chart(region_df)
        else:
            st.info("No regional data found.")
    except Exception:
        st.info("Regional interest data unavailable.")

    # Related Queries
    st.subheader("Rising Related Queries")

    try:
        related = pytrends.related_queries()[niche]
        if related and 'rising' in related and related['rising'] is not None:
            st.table(related['rising'].head(10))
        else:
            st.info("No rising queries found.")
    except Exception:
        st.info("Related query data unavailable.")

    # Related Topics
    st.subheader("Related Topics")

    try:
        topics = pytrends.related_topics()[niche]["top"]
        if topics is not None:
            st.dataframe(topics.head(10))
        else:
            st.info("No related topics found.")
    except Exception:
        st.info("Related topic data unavailable right now.")


# ----------- FOOTER -----------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.metric("🔗 Built by", "Eternity AI")
