import streamlit as st
import requests

# =========================
# Configuration
# =========================
API = "http://localhost:8080"

st.set_page_config(page_title="Disaster RAG", layout="wide")

# =========================
# Dark Mode CSS
# =========================
st.markdown(
    """
<style>
.stApp {
    background-color: #0e1117;
    color: #e5e7eb;
}

.main-header {
    font-size: 3rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}

.subtitle {
    text-align: center;
    color: #9ca3af;
    font-size: 1.15rem;
    margin-bottom: 2.5rem;
}

.answer-box {
    background: rgba(102, 126, 234, 0.1);
    border-left: 5px solid #667eea;
    padding: 1.5rem;
    border-radius: 12px;
    line-height: 1.6;
}

.source-card {
    background: #1f2937;
    padding: 1.2rem;
    border-radius: 12px;
    margin: 0.75rem 0;
    border-left: 4px solid #10b981;
    border: 1px solid #374151;
}

.event-card {
    background: #1f2937;
    padding: 0.9rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    border-left: 4px solid #8b5cf6;
    border: 1px solid #374151;
    font-size: 0.85rem;
}

.severity-high { color: #f87171; font-weight: 700; }
.severity-medium { color: #fbbf24; font-weight: 700; }
.severity-low { color: #34d399; font-weight: 700; }

.conf-high { color: #34d399; font-weight: 700; }
.conf-mid { color: #fbbf24; font-weight: 700; }
.conf-low { color: #f87171; font-weight: 700; }

.text-muted { color: #9ca3af; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Header
# =========================
st.markdown('<h1 class="main-header">🌍 Disaster RAG</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Real-time disaster intelligence with Retrieval-Augmented Generation</p>',
    unsafe_allow_html=True,
)


# =========================
# API Helpers
# =========================
def query_rag(question, n_results, duration_hours):
    try:
        r = requests.post(
            f"{API}/query",
            json={
                "question": question,
                "n_results": n_results,
                "duration_hours": duration_hours,
            },
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_stats():
    try:
        return requests.get(f"{API}/stats").json()
    except Exception:
        return None


def get_latest_events(limit=5):
    try:
        return requests.get(f"{API}/latest?limit={limit}").json()
    except Exception:
        return {"events": []}


def confidence_class(score):
    if score >= 0.7:
        return "conf-high", "🟢"
    elif score >= 0.4:
        return "conf-mid", "🟠"
    return "conf-low", "🔴"


# =========================
# Load Stats
# =========================
stats = get_stats()
if not stats:
    st.error("❌ API offline. Run: uv run uvicorn src.api.main:app --port 8080")
    st.stop()

# =========================
# Layout
# =========================
col_main, col_side = st.columns([2.6, 1])

# ---------- Sidebar ----------
with col_side:
    st.markdown("### 📊 System Status")
    st.metric("Embedded Events", f"{stats.get('total_events', 0):,}")

    st.markdown("---")
    st.markdown("### 🔥 Latest Events")

    latest = get_latest_events()

    events = latest.get("events", [])

    if events:
        for e in events:
            meta = e.get("metadata", {})
            st.markdown(
                f"""
                <div class="event-card">
                    <strong>{meta.get("title", "Untitled")}</strong><br>
                    <span class="text-muted">
                        {meta.get("source", "Unknown")} •
                        {meta.get("timestamp", "")[:16].replace("T", " ")}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No recent events.")
# ---------- Main ----------
with col_main:
    st.markdown("### 💬 Disaster Intelligence")

    question = st.text_input(
        "Question",
        placeholder="e.g. Any recent earthquakes in Southeast Asia?",
        label_visibility="collapsed",
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        search = st.button("🔍 Search", type="primary", use_container_width=True)
    with c2:
        n_results = st.slider("Sources", 1, 10, 5)

    duration = st.slider("Previous hours", 1, 48, 24)

    if search and question:
        with st.spinner("Analyzing disasters..."):
            result = query_rag(question, n_results, duration)

        if "error" in result:
            st.error(result["error"])
        else:
            answer = result.get("answer", "")
            sources = result.get("sources", [])

            if answer:
                st.markdown("### 🧠 AI Summary")
                st.markdown(
                    f'<div class="answer-box">{answer}</div>',
                    unsafe_allow_html=True,
                )

            if sources:
                st.markdown(f"### 📚 Evidence ({len(sources)})")
                for s in sources:
                    m = s.get("metadata", {})
                    conf = s.get("confidence", 0)
                    conf_cls, icon = confidence_class(conf)
                    severity = m.get("severity", "low")

                    st.markdown(
                        f"""
                        <div class="source-card">
                            <strong>{m.get("title","Untitled Event")}</strong><br>
                            <span class="{conf_cls}">{icon} {conf:.0%}</span> •
                            <span class="severity-{severity}">{severity.upper()}</span> •
                            <span class="text-muted">{m.get("timestamp","")[:16]}</span><br>
                            <span style="color:#60a5fa">{m.get("source","Unknown")}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No matching disasters found.")

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown(
    """
<div style="text-align:center; color:#6b7280; font-size:0.85rem;">
Powered by Kafka • ChromaDB • Qwen-0.6B |
<a href="http://localhost:8080/docs">API</a> |
<a href="http://localhost:8090">Broker</a>
</div>
""",
    unsafe_allow_html=True,
)
