import streamlit as st
import requests

API = "http://localhost:8081"

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
                for event in data["sources"]:
                    st.markdown(
                        f"- **Source:** {event['metadata'].get('source', 'N/A')} | **Time:** {event['metadata'].get('timestamp', 'N/A')}"
                    )
                    st.write(event["document"])
                    st.write(event["metadata"])
                # st.write(data["events"])
            except Exception:
                st.error("API not available. Run: uvicorn src.api.main:app")

try:
    stats = requests.get(f"{API}/stats").json()
    st.sidebar.metric("Events", stats["total_events"])
except Exception:
    st.sidebar.warning("API offline")
