import re, time, feedparser, pandas as pd, streamlit as st
from datetime import datetime
from dateutil import parser as dparser

st.set_page_config(page_title="London Opportunities (≥£60k)", page_icon="💼", layout="wide")
st.title("💼 London Opportunities — Legal • Human Rights • Climate • Policy (≥£60k)")
st.caption("Zero-install, browser-only. Paste more feeds anytime in the sidebar.")

# --- Settings / filters ---
DEFAULT_FEEDS = [
    # Policy/advocacy roles (W4MP):
    "https://www.w4mpjobs.org/SearchJobsRSS.aspx",
    # You can add more public feeds later (uni/think-tank/NGO job boards, department RSS, etc.)
]

COURSE_FELLOWSHIP_FEEDS = [
    # Add public feeds for courses / calls for papers / fellowships here
    # (example placeholders; edit in GitHub later)
    # "https://www.example.com/calls/rss",
]

SALARY_PATTERN = re.compile(r"£\s?(\d{2,3}[,]?\d{3})", re.IGNORECASE)
SPONSORSHIP_HINTS = ["visa", "sponsor", "sponsorship", "skilled worker", "tier 2", "work permit"]

FOCUS_TERMS = [
    # core focus for Jose
    "climate", "environment", "human rights", "international law",
    "policy", "litigation", "strategic litigation", "accountability",
    "research", "fellow", "lecturer", "counsel", "advisor", "adviser",
    "icj", "iacthr", "inter-american", "state responsibility", "due diligence"
]

MIN_SALARY = 60000  # £60k floor

# --- Sidebar controls ---
with st.sidebar:
    st.header("Filters")
    min_salary = st.number_input("Minimum salary (GBP)", min_value=0, value=MIN_SALARY, step=5000)
    focus = st.text_area("Keywords (ANY match)", value=", ".join(FOCUS_TERMS), height=80)
    extra_feeds = st.text_area("Add RSS feeds (one per line)", value="", height=110)
    st.markdown("**Tip:** you can paste uni/think-tank/NGO job RSS feeds here. No keys needed.")
    run = st.button("Search / Refresh")

def parse_when(x):
    for k in ("published", "updated"):
        if k in x:
            try:
                return dparser.parse(x[k])
            except Exception:
                pass
    return None

def salary_from_text(text):
    """Return the max salary number found in text, else None."""
    if not text:
        return None
    nums = [int(n.replace(",", "")) for n in SALARY_PATTERN.findall(text)]
    return max(nums) if nums else None

def any_focus(text, terms):
    t = (text or "").lower()
    return any(word.strip().lower() in t for word in terms if word.strip())

def has_sponsorship_hint(text):
    t = (text or "").lower()
    return any(h in t for h in SPONSORSHIP_HINTS)

def fetch_feed(url):
    try:
        return feedparser.parse(url)
    except Exception:
        return {"entries": []}

if run:
    feeds = list(DEFAULT_FEEDS)
    if extra_feeds.strip():
        feeds += [u.strip() for u in extra_feeds.splitlines() if u.strip()]

    rows = []
    for url in feeds:
        feed = fetch_feed(url)
        for e in feed.get("entries", []):
            title = e.get("title", "")
            link = e.get("link", "")
            summ = e.get("summary", "") or e.get("description", "")
            when = parse_when(e)
            src = feed.get("feed", {}).get("title", url)
            text_blob = f"{title}\n{summ}"
            sal = salary_from_text(text_blob)
            focus_hit = any_focus(text_blob, focus.split(",")) if focus else True
            if sal is not None and sal < min_salary:
                continue
            if not focus_hit:
                continue
            rows.append({
                "Date": when.isoformat() if when else "",
                "Title": title,
                "Source": src,
                "Salary(max)": sal,
                "Visa?": "✅" if has_sponsorship_hint(text_blob) else "",
                "Link": link
            })

    # Sort by date desc, then salary desc
    def sort_key(r):
        try:
            d = dparser.parse(r["Date"]) if r["Date"] else datetime.min
        except Exception:
            d = datetime.min
        return (d, r.get("Salary(max)") or 0)

    rows.sort(key=sort_key, reverse=True)
    df = pd.DataFrame(rows)

    st.subheader("Jobs (filtered to ≥ min salary & keywords)")
    if df.empty:
        st.info("No matches yet. Try lowering the salary floor or adding more feeds.")
    else:
        st.dataframe(df, use_container_width=True)
        st.write("🔗 Click links in the table to open postings.")
        st.caption("Visa flag is heuristic based on common keywords; verify in the ad/org site.")

    # Courses / CFPs / Fellowships area
    st.subheader("Courses • Calls for Papers • Fellowships")
    c_rows = []
    for url in COURSE_FELLOWSHIP_FEEDS:
        feed = fetch_feed(url)
        for e in feed.get("entries", []):
            title = e.get("title", "")
            link = e.get("link", "")
            summ = e.get("summary", "")
            when = parse_when(e)
            c_rows.append({
                "Date": when.isoformat() if when else "",
                "Title": title,
                "Source": feed.get("feed", {}).get("title", url),
                "Link": link
            })
    if c_rows:
        c_rows.sort(key=lambda r: r["Date"], reverse=True)
        st.dataframe(pd.DataFrame(c_rows), use_container_width=True)
    else:
        st.info("Add public RSS feeds for courses/CFPs/fellowships in the code (or paste above).")
else:
    st.info("Set filters in the left sidebar, then click **Search / Refresh**.")
