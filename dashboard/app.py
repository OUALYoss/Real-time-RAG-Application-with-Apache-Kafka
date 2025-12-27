import streamlit as st
import requests

API = "http://localhost:8081"   # 8080

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


def query_rag(question: str, n_results: int = 5, previous_hours: int = None):
    try:
        resp = requests.post(
            f"{API}/query",
            json={"question": question, "n_results": n_results, 
                  "duration_hours": previous_hours},
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

    col_btn, col_controls = st.columns([2, 4])

    with col_btn:
        search = st.button("🔍 Search", type="primary", use_container_width=True)

    with col_controls:
        n_results = st.slider("Sources to use", 1, 10, 5)

        previous_hours = st.slider(
            "Previous hours",
            min_value=1,
            max_value=48,
            value=24,
            help="Search only events from the last N hours",
        )

    if search and question:
        with st.spinner("Searching..."):
            result = query_rag(question, n_results, previous_hours)

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

            st.write(sources)

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
                            {meta.get("timestamp", "")}
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
import streamlit as st
import requests

API = "http://localhost:8080"

st.set_page_config(page_title="Disaster RAG", layout="wide")

# High-quality dark mode custom CSS
st.markdown(
    """
<style>
    /* Global dark theme adjustments */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        text-align: center;
        color: #9ca3af;
        margin-bottom: 2.5rem;
        font-size: 1.2rem;
    }
    
    /* Card components with dark mode support */
    .answer-box {
        background: rgba(102, 126, 234, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        color: #e5e7eb;
        line-height: 1.6;
    }
    
    .source-card {
        background: #1f2937;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        border: 1px solid #374151;
        border-left: 4px solid #10b981;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s;
    }
    
    .source-card:hover {
        transform: translateY(-2px);
        background: #252f3f;
    }
    
    .news-card {
        background: #111827;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.6rem 0;
        border: 1px solid #1f2937;
        border-left: 4px solid #f59e0b;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .event-card {
        background: #1f2937;
        padding: 0.85rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #374151;
        border-left: 4px solid #8b5cf6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        font-size: 0.9rem;
    }
    
    /* Confidence and severity colors */
    .confidence-high { color: #34d399; font-weight: 700; }
    .confidence-medium { color: #fbbf24; font-weight: 700; }
    .confidence-low { color: #f87171; font-weight: 700; }
    
    .severity-high { color: #f87171; font-weight: 700; }
    .severity-medium { color: #fbbf24; font-weight: 700; }
    .severity-low { color: #34d399; font-weight: 700; }
    
    .stats-card {
        background: #1f2937;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #374151;
        margin-bottom: 2rem;
    }
    
    /* Text overrides */
    h1, h2, h3 { color: #f3f4f6 !important; }
    strong { color: #ffffff !important; }
    .text-muted { color: #9ca3af !important; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<h1 class="main-header">&#127757; Disaster RAG</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Real-time disaster monitoring with AI-powered insights</p>',
    unsafe_allow_html=True,
)


def query_rag(question: str, n_results: int = 5, fetch_fresh: bool = False, duration_hours: int = None):
    try:
        resp = requests.post(
            f"{API}/query",
            json={
                "question": question,
                "n_results": n_results,
                "fetch_fresh": fetch_fresh,
                "duration_hours": duration_hours,
            },
            timeout=300,
        )
        return resp.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def get_stats():
    try:
        return requests.get(f"{API}/stats", timeout=5).json()
    except Exception:
        return None


def get_latest_events(limit=5):
    try:
        return requests.get(f"{API}/latest?limit={limit}", timeout=5).json()
    except Exception:
        return {"events": []}


def get_confidence_class(confidence):
    """Return CSS class based on confidence score"""
    if confidence >= 0.7:
        return "confidence-high", "&#128154;"
    elif confidence >= 0.4:
        return "confidence-medium", "&#128155;"
    else:
        return "confidence-low", "&#128308;"


stats = get_stats()
if not stats:
    st.error("&#10060; API offline. Run: `uv run uvicorn src.api.main:app --port 8080`")
    st.stop()

# Main layout
col_main, col_side = st.columns([2.5, 1])

with col_side:
    st.markdown("### &#128202; System Status")

    chroma_count = stats.get("chroma_db_count", 0)
    st.metric("Embedded Events", f"{chroma_count:,}")

    if chroma_count == 0:
        st.warning("&#9888; ChromaDB is empty. Ingesting historical data...")

    st.markdown("---")
    st.markdown("### &#128293; Latest Arrivals")

    latest = get_latest_events(limit=5)
    if latest.get("events"):
        for event in latest["events"]:
            meta = event.get("metadata", {})
            source = meta.get("source", "Unknown")
            title = meta.get("title", event.get("document", "")[:60])

            st.markdown(
                f"""
            <div class="event-card">
                <strong style="font-size: 0.9rem;">{title}</strong><br>
                <span class="text-muted" style="font-size: 0.8rem;">
                    {source}    &bull;    {meta.get("timestamp", "")[:16].replace('T', ' ')}
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No events in database yet.")

with col_main:
    st.markdown("### &#128172; Disaster Intel")

    question = st.text_input(
        "Question",
        placeholder="e.g., Any recent earthquakes in Southeast Asia?",
        label_visibility="collapsed",
    )

    col_btn, col_slider, col_fresh = st.columns([1, 2, 1.2])
    with col_btn:
        search = st.button("&#128269; Search", type="primary", use_container_width=True)
    with col_slider:
        n_results = st.slider("Sources to analyze", 1, 10, 5)
    with col_fresh:
        fetch_fresh = st.checkbox(
            "&#128260; Fetch Live", value=True, help="Fetch real-time API data"
        )

    previous_hours = st.slider(
        "Previous hours",
        min_value=1,
        max_value=48,
        value=24,
        help="Search only events from the last N hours",
    )

    if search and question:
        if not question.strip():
            st.warning("Please enter a question!")
        else:
            with st.spinner("&#128269; RAG Analysis in progress..."):
                result = query_rag(question, n_results, fetch_fresh, previous_hours)

            if not result or "error" in result:
                st.error(f"Analysis failed: {result.get('error', 'Unknown error') if result else 'No response'}")
            else:
                # Answer section
                sources = result.get("sources", [])
                answer = result.get("answer", "")

                # Check for negative answers
                is_negative = any(
                    phrase in answer.lower()
                    for phrase in [
                        "no official",
                        "no specific",
                        "do not have",
                        "no data was found",
                    ]
                )

                if answer and (sources or not is_negative):
                    st.markdown("### &#128221; AI Summary")
                    st.markdown(
                        f"""
                    <div class="answer-box">
                        {answer}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Sources section
                fresh_count = result.get("fresh_data_count", 0)

                if sources:
                    st.markdown(
                        f"### &#128218; Evidence Sources ({len(sources)}) {f'<span style=\\"font-size: 0.8rem; color: #60a5fa;\\">&#9889; {fresh_count} live items</span>' if fresh_count > 0 else ''}",
                        unsafe_allow_html=True,
                    )
                    for src in sources:
                        meta = src.get("metadata", {})
                        similarity = src.get("confidence", 0)

                        # Apply intuitive confidence mapping
                        display_conf = min(
                            1.0, max(0.1, (similarity - 0.15) / 0.65 + 0.25)
                        )

                        conf_class, conf_icon = get_confidence_class(display_conf)
                        severity = meta.get("severity", "low")
                        is_fresh = src.get("fresh", False)

                        # Clean up timestamp for display
                        raw_ts = (
                            meta.get("timestamp", "").replace("T", " ").replace("Z", "")
                        )
                        display_ts = raw_ts[:16] if len(raw_ts) >= 16 else raw_ts

                        st.markdown(
                            f"""
                        <div class="source-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <strong style="font-size: 1.1rem;">{meta.get("title", "Untitled Event")}</strong>
                                <span class="{conf_class}" style="font-size: 0.9rem;">{conf_icon} {display_conf:.0%} {'&#9889;' if is_fresh else ''}</span>
                            </div>
                            <div style="font-size: 0.9rem; margin-top: 0.4rem;">
                                <span style="color: #60a5fa; font-weight: 600;">{meta.get("source", "Unknown")}</span>    &bull;   
                                <span class="severity-{severity}">{severity.upper()}</span>    &bull;   
                                <span class="text-muted">{display_ts} UTC</span>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No matching disasters found in the database or live APIs.")

                # News articles section
                news_articles = result.get("news_articles", [])
                if news_articles:
                    st.markdown(f"### &#128240; Breaking News Coverage")
                    for article in news_articles:
                        st.markdown(
                            f"""
                        <div class="news-card">
                            <strong style="color: #fbbf24 !important;">{article.get("title", "Untitled News")}</strong><br>
                            <span class="text-muted" style="font-size: 0.85rem;">
                                &#127760; {article.get("domain", "Source")}    &bull;    {article.get("seendate", "")[:19].replace('T', ' ')}
                            </span>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #6b7280; font-size: 0.85rem; padding-bottom: 2rem;">
    Powered by Kafka, ChromaDB &amp; Qwen-0.6B    &bull;    
    <a href="http://localhost:8080/docs" style="color: #6b7280; text-decoration: none;">API</a>    &bull;    
    <a href="http://localhost:8090" style="color: #6b7280; text-decoration: none;">Broker</a>
</div>
""",
    unsafe_allow_html=True,
)
