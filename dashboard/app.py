import streamlit as st
import requests

API = "http://localhost:8080"

st.title("Disaster Monitor")

question = st.text_input("Question:", placeholder="Recent earthquakes in California?")

if st.button("Search"):
    if question:
        with st.spinner("Searching..."):
            try:
                r = requests.post(f"{API}/query", json={"question": question})
                data = r.json()
                st.success("Answer:")
                st.write(data["answer"])
                st.caption(f"Sources: {len(data['sources'])} events")
            except Exception:
                st.error("API not available. Run: uvicorn src.api.main:app")

try:
    stats = requests.get(f"{API}/stats").json()
    st.sidebar.metric("Events", stats["total_events"])
except Exception:
    st.sidebar.warning("API offline")
