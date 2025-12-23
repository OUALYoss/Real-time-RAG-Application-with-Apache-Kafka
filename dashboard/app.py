import streamlit as st
import requests

API = "http://localhost:8081"

st.set_page_config(page_title="Disaster RAG", layout="wide")

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .answer-box {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .source-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #11998e;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .severity-high { color: #c62828; font-weight: 600; }
    .severity-medium { color: #ef6c00; font-weight: 600; }
    .severity-low { color: #2e7d32; font-weight: 600; }
    .example-query {
        background: #f5f5f5;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        font-size: 0.9rem;
        color: black;
    }
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="main-header"> Disaster RAG</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Ask questions about real-time disaster events</p>',
    unsafe_allow_html=True,
)


def query_rag(question: str, n_results: int = 5):
    try:
        resp = requests.post(
            f"{API}/query",
            json={"question": question, "n_results": n_results},
            timeout=30,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def get_stats():
    try:
        return requests.get(f"{API}/stats", timeout=5).json()
    except Exception:
        return None


stats = get_stats()
if not stats:
    st.error("❌ API offline. Run: `uv run uvicorn src.api.main:app --port 8080`")
    st.stop()

col_main, col_side = st.columns([3, 1])

with col_side:
    st.markdown("### 📊 Stats")
    st.metric("Total Events", stats.get("total_events", 0))

    st.markdown("**Sources**")
    for src, count in stats.get("by_source", {}).items():
        st.write(f"• {src}: {count}")

    st.markdown("**Types**")
    for typ, count in stats.get("by_type", {}).items():
        st.write(f"• {typ}: {count}")

with col_main:
    st.markdown("### 💬 Ask a Question")

    st.markdown(
        """
    <div style="margin-bottom: 1rem;">
        <span class="example-query">Recent earthquakes in California?</span>
        <span class="example-query">Any floods in Asia?</span>
        <span class="example-query">Current wildfire alerts?</span>
        <span class="example-query">Severe weather warnings?</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Your question",
        placeholder="e.g., What are the recent earthquakes above magnitude 4?",
        label_visibility="collapsed",
    )

    col_btn, col_slider = st.columns([1, 2])
    with col_btn:
        search = st.button("🔍 Search", type="primary", use_container_width=True)
    with col_slider:
        n_results = st.slider("Sources to use", 1, 10, 5)

    if search and question:
        with st.spinner("Searching..."):
<<<<<<< HEAD
            try:
                r = requests.post(f"{API}/query", json={"question": question})
                data = r.json()
                st.success("Answer:")
                st.write(data["answer"])
                st.caption(f"Sources: {len(data['sources'])} events")
                for event in data["sources"]:
                    st.markdown(
                        f"- **Source:** {event['metadata'].get('source', 'N/A')}"
                    )
                    st.markdown(
                        f"**Time:** {event['metadata'].get('timestamp', 'N/A')}"
                    )
                    st.write(event["document"])
                    st.write(event["metadata"])
                # st.write(data["events"])
            except Exception:
                st.error("API not available. Run: uvicorn src.api.main:app")
=======
            result = query_rag(question, n_results)
>>>>>>> d2f6fdc (version 1)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.markdown("### 📝 Answer")
            st.markdown(
                f"""
            <div class="answer-box">
                {result.get("answer", "No answer")}
            </div>
            """,
                unsafe_allow_html=True,
            )

            sources = result.get("sources", [])
            if sources:
                st.markdown(f"### 📚 Sources ({len(sources)})")
                for src in sources:
                    meta = src.get("metadata", {})
                    severity = meta.get("severity", "low")
                    st.markdown(
                        f"""
                    <div class="source-card">
                        <strong>{meta.get("title", src.get("document", "")[:100])}</strong><br>
                        <span style="color: #666;">
                            {meta.get("source", "Unknown")}
                            <span class="severity-{severity}">{severity.upper()}</span>
                            {meta.get("timestamp", "")[:19]}
                        </span>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    <a href="http://localhost:8080/docs" target="_blank">API Docs</a> •
    <a href="http://localhost:8090" target="_blank">Kafka UI</a> •
    Real-time RAG with Apache Kafka
</div>
""",
    unsafe_allow_html=True,
)
