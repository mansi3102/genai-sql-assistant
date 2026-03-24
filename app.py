"""
app.py  —  GenAI SQL Query Assistant  (Streamlit Web App)
Run:  streamlit run app.py
"""
import os, re, sqlite3, json, random, warnings
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from groq import Groq

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GenAI SQL Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
warnings.filterwarnings("ignore")

# ═════════════════════════════════════════════════════════════════════════════
#  DATABASE CREATION (auto-runs if DB missing)
# ═════════════════════════════════════════════════════════════════════════════
DB_PATH     = "ecommerce_india.db"
MEMORY_FILE = "ai_memory.json"

def _make_synthetic_db():
    random.seed(2024)
    RS = [("North","Delhi"),("North","Uttar Pradesh"),("North","Rajasthan"),
          ("North","Punjab"),("North","Haryana"),("South","Tamil Nadu"),
          ("South","Karnataka"),("South","Kerala"),("South","Telangana"),
          ("East","West Bengal"),("East","Odisha"),("East","Bihar"),
          ("East","Assam"),("West","Maharashtra"),("West","Gujarat"),
          ("West","Goa"),("Central","Madhya Pradesh"),("Central","Chhattisgarh")]
    SC = {"Delhi":["New Delhi","Dwarka","Rohini"],"Uttar Pradesh":["Lucknow","Kanpur","Noida"],
          "Rajasthan":["Jaipur","Jodhpur","Udaipur"],"Punjab":["Chandigarh","Ludhiana"],
          "Haryana":["Gurugram","Faridabad"],"Tamil Nadu":["Chennai","Coimbatore"],
          "Karnataka":["Bengaluru","Mysuru"],"Kerala":["Kochi","Thiruvananthapuram"],
          "Telangana":["Hyderabad","Warangal"],"West Bengal":["Kolkata","Howrah"],
          "Odisha":["Bhubaneswar","Cuttack"],"Bihar":["Patna","Gaya"],
          "Assam":["Guwahati","Silchar"],"Maharashtra":["Mumbai","Pune","Nagpur"],
          "Gujarat":["Ahmedabad","Surat","Vadodara"],"Goa":["Panaji","Margao"],
          "Madhya Pradesh":["Bhopal","Indore"],"Chhattisgarh":["Raipur","Bhilai"]}
    PD = {"Electronics":[("Smartphone",8000,85000),("Laptop",22000,130000),("Tablet",7000,55000),
                          ("Earphones",400,9000),("Smart TV",12000,90000),("Power Bank",600,5000)],
          "Fashion":[("Mens T-Shirt",199,1800),("Womens Kurta",349,3500),("Jeans",499,4500),
                      ("Saree",450,12000),("Sports Shoes",599,7000)],
          "Home & Kitchen":[("Mixer Grinder",1200,7000),("Pressure Cooker",700,5000),
                             ("Bedsheet Set",399,3500),("Air Purifier",4500,28000)],
          "Books":[("Fiction Novel",149,599),("Self-Help Book",199,799),("Textbook",299,1800)],
          "Sports & Fitness":[("Cricket Bat",400,6000),("Yoga Mat",299,2500),("Cycle",4500,28000)],
          "Beauty & Personal Care":[("Face Moisturiser",150,1800),("Shampoo",100,800),
                                     ("Perfume",250,3500)],
          "Toys & Games":[("Board Game",250,2500),("LEGO Set",450,6000)],
          "Groceries":[("Basmati Rice 5kg",299,599),("Cooking Oil 1L",120,350),("Tea 500g",120,550)],
          "Automotive":[("Car Seat Cover",499,4000),("Dash Cam",1500,8000)],
          "Health & Wellness":[("BP Monitor",900,6000),("Multivitamins",250,1800)]}
    PM  = ["UPI","Credit Card","Debit Card","Net Banking","Cash on Delivery","EMI","Digital Wallet"]
    PWt = [38,18,14,7,14,5,4]
    ST  = ["Delivered","Shipped","Processing","Cancelled","Returned"]
    SWt = [63,13,6,13,5]
    FN  = ["Aarav","Rahul","Priya","Sneha","Amit","Kavya","Arjun","Divya","Rohit","Anjali"]
    LN  = ["Sharma","Patel","Singh","Kumar","Gupta","Verma","Mehta","Nair","Reddy","Das"]
    BR  = ["Samsung","Apple","OnePlus","Nike","Himalaya","Prestige","Generic","Xiaomi"]

    cust_rows = []
    for i in range(1,501):
        region,state = random.choice(RS)
        city = random.choice(SC.get(state,[state]))
        cust_rows.append({"customer_id":i,"customer_name":f"{random.choice(FN)} {random.choice(LN)}",
            "gender":random.choice(["Male","Female"]),"age":random.randint(18,65),
            "city":city,"state":state,"region":region})

    prod_rows, pid = [], 1
    for cat,items in PD.items():
        for name,lo,hi in items:
            prod_rows.append({"product_id":pid,"product_name":name,"category":cat,
                "brand":random.choice(BR),"price_inr":round(random.uniform(lo,hi),2),
                "rating":round(random.uniform(3.1,5.0),1),"stock":random.randint(5,600)})
            pid+=1

    start = datetime(2024,1,1); span=(datetime(2024,12,31)-start).days
    ord_rows = []
    for oid in range(1,3001):
        c=random.choice(cust_rows); p=random.choice(prod_rows)
        qty=random.choices([1,2,3,4,5],weights=[50,25,13,7,5])[0]
        disc=random.choices([0,5,10,15,20,25,30],weights=[28,14,20,16,12,6,4])[0]
        total=round(p["price_inr"]*qty*(1-disc/100),2)
        odate=start+timedelta(days=random.randint(0,span))
        ord_rows.append({"order_id":oid,"customer_id":c["customer_id"],"product_id":p["product_id"],
            "product_name":p["product_name"],"category":p["category"],"brand":p["brand"],
            "quantity":qty,"unit_price_inr":p["price_inr"],"discount_pct":disc,
            "total_amount_inr":total,"payment_method":random.choices(PM,weights=PWt)[0],
            "order_status":random.choices(ST,weights=SWt)[0],
            "order_date":odate.strftime("%Y-%m-%d"),"order_month":odate.strftime("%Y-%m"),
            "order_year":odate.year,"order_month_num":odate.month,
            "customer_city":c["city"],"customer_state":c["state"],"customer_region":c["region"]})

    conn=sqlite3.connect(DB_PATH)
    pd.DataFrame(cust_rows).to_sql("customers",conn,if_exists="replace",index=False)
    pd.DataFrame(prod_rows).to_sql("products",conn,if_exists="replace",index=False)
    pd.DataFrame(ord_rows).to_sql("orders",conn,if_exists="replace",index=False)
    for col in ["customer_region","order_month","order_status","payment_method","category"]:
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON orders({col})")
    conn.commit(); conn.close()


# ═════════════════════════════════════════════════════════════════════════════
#  4-LAYER SCHEMA + RULES + EXAMPLES
# ═════════════════════════════════════════════════════════════════════════════

SYNTH_SCHEMA = """
DATABASE: Indian E-Commerce (SQLite) | Period: 2024-01-01 to 2024-12-31

TABLE: customers — One row per customer
  customer_id, customer_name, gender (Male/Female), age (18-65),
  city, state, region (North|South|East|West|Central)

TABLE: products — One row per product
  product_id, product_name, category, brand, price_inr, rating (1-5), stock

TABLE: orders — One row per purchase
  order_id, customer_id, product_id, product_name, category, brand,
  quantity (1-5), unit_price_inr, discount_pct (0/5/10/15/20/25/30),
  total_amount_inr  <- FINAL amount paid (use for revenue/spending),
  payment_method (UPI|Credit Card|Debit Card|Net Banking|Cash on Delivery|EMI|Digital Wallet),
  order_status (Delivered|Shipped|Processing|Cancelled|Returned),
  order_date (YYYY-MM-DD), order_month (YYYY-MM), order_year (int), order_month_num (1-12),
  customer_city, customer_state, customer_region (North|South|East|West|Central)
"""

BUSINESS_RULES = """
DATE: Never use YEAR() or MONTH(). Use order_year and order_month_num columns.
      order_month = '2024-12' means December. Last month = '2024-12'.
      Q1 = order_month_num IN (1,2,3). Q4 = order_month_num IN (10,11,12).
MONEY: Revenue = SUM(total_amount_inr). Always ROUND to 0 decimals.
GEOGRAPHY: Use customer_region, customer_state, customer_city from orders table.
ALIASES: Use clear names like revenue_inr, order_count, avg_order_inr.
LIMIT: Always add LIMIT 20 unless question implies fewer results.
PCT: ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM orders),1) for percentages.
"""

EXAMPLES = """
Q: Revenue by region
A: SELECT customer_region, COUNT(*) AS orders, ROUND(SUM(total_amount_inr),0) AS revenue_inr
   FROM orders GROUP BY customer_region ORDER BY revenue_inr DESC;

Q: Monthly trend
A: SELECT order_month, COUNT(*) AS orders, ROUND(SUM(total_amount_inr),0) AS revenue_inr
   FROM orders WHERE order_year=2024 GROUP BY order_month ORDER BY order_month;

Q: Payment method share
A: SELECT payment_method, COUNT(*) AS orders,
          ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM orders),1) AS pct
   FROM orders GROUP BY payment_method ORDER BY orders DESC;

Q: Top customers
A: SELECT c.customer_name, c.city, ROUND(SUM(o.total_amount_inr),0) AS spent_inr
   FROM orders o JOIN customers c ON o.customer_id=c.customer_id
   GROUP BY o.customer_id, c.customer_name, c.city ORDER BY spent_inr DESC LIMIT 10;

Q: Order status breakdown
A: SELECT order_status, COUNT(*) AS orders,
          ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM orders),1) AS pct
   FROM orders GROUP BY order_status ORDER BY orders DESC;
"""


# ═════════════════════════════════════════════════════════════════════════════
#  MEMORY (Layer 4)
# ═════════════════════════════════════════════════════════════════════════════
def _load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f: return json.load(f)
        except: pass
    return {"corrections":[],"successes":[]}

def _save_mem(m):
    with open(MEMORY_FILE,"w") as f: json.dump(m,f,indent=2)

def _mem_layer():
    m = _load_mem()
    c = m.get("corrections",[])
    if not c: return ""
    lines = ["Past corrections - never repeat:"]
    for x in c[-6:]:
        lines.append(f"Wrong: {x['bad_sql'][:80]}  Error: {x['error'][:60]}")
        lines.append(f"Fixed: {x['fixed_sql'][:80]}")
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
#  AI ENGINE
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def _client(key):
    return Groq(api_key=key)

def _clean(raw):
    return re.sub(r"```(?:sql)?","",raw,flags=re.IGNORECASE).strip().strip("`")

def discover_schema(db_path):
    lines = [f"DATABASE: {os.path.basename(db_path)} (SQLite)"]
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for (tbl,) in cur.fetchall():
                n = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {tbl}",conn).iloc[0,0]
                lines.append(f"TABLE: {tbl} ({n:,} rows)")
                cur.execute(f"PRAGMA table_info({tbl})")
                for col in cur.fetchall():
                    lines.append(f"  {col[1]} {col[2]}")
                    if "TEXT" in str(col[2]).upper():
                        try:
                            sv = pd.read_sql_query(
                                f"SELECT DISTINCT {col[1]} FROM {tbl} LIMIT 6",conn
                            ).iloc[:,0].tolist()
                            lines.append(f"    Values: {' | '.join(str(v) for v in sv)}")
                        except: pass
                lines.append("")
    except Exception as e:
        lines.append(f"Schema error: {e}")
    return "\n".join(lines)

def gen_sql(question, client, schema, rules, examples):
    mem = _mem_layer()
    prompt = "\n".join([
        "You are an expert SQLite SQL generator.",
        "Return ONLY raw SQL — no markdown, no backticks, no explanation.",
        "", schema, "", rules, "", examples,
        ("" if not mem else f"\n{mem}"),
        "",
        f"QUESTION: {question}",
        "SQL:",
    ])
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":"Output ONLY valid SQLite SQL."},
                      {"role":"user","content":prompt}],
            max_tokens=600, temperature=0.05)
        return _clean(r.choices[0].message.content), None
    except Exception as e: return None, str(e)

def fix_sql(question, bad, error, client):
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":(
                f"Fix this SQLite SQL.\nQUESTION: {question}\n"
                f"BROKEN:\n{bad}\nERROR: {error}\n"
                "Rules: No YEAR() or MONTH(). Valid SQLite. Return ONLY fixed SQL.\nFIXED SQL:"
            )}],
            max_tokens=400, temperature=0.05)
        fixed = _clean(r.choices[0].message.content)
        m = _load_mem()
        m["corrections"].append({"bad_sql":bad,"error":error,"fixed_sql":fixed,
                                  "question":question})
        m["corrections"] = m["corrections"][-25:]
        _save_mem(m)
        return fixed, None
    except Exception as e: return None, str(e)

def run_q(sql, db):
    try:
        with sqlite3.connect(db) as conn:
            return pd.read_sql_query(sql,conn), None
    except Exception as e: return None, str(e)

def get_insight(question, df, client):
    if df is None or df.empty: return ""
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":(
                "Write a 3-sentence plain-English business insight. "
                "Use specific numbers. Write for non-technical audience.\n\n"
                f"QUESTION: {question}\n\n"
                f"DATA ({len(df)} rows):\n{df.head(6).to_string(index=False)}\n\n"
                "Insight:"
            )}],
            max_tokens=160, temperature=0.4)
        return r.choices[0].message.content.strip()
    except: return ""


# ═════════════════════════════════════════════════════════════════════════════
#  SMART CHART ENGINE
# ═════════════════════════════════════════════════════════════════════════════
PALETTE = ["#3b82f6","#06d6a0","#f59e0b","#ef4444","#8b5cf6",
           "#ec4899","#10b981","#f97316","#6366f1","#14b8a6"]
BASE = dict(paper_bgcolor="#111827", plot_bgcolor="#0a0e1a",
            font=dict(color="#94a3b8",size=12), margin=dict(l=20,r=20,t=55,b=40),
            colorway=PALETTE,
            xaxis=dict(gridcolor="#1e293b",zerolinecolor="#1e293b"),
            yaxis=dict(gridcolor="#1e293b",zerolinecolor="#1e293b"))

def _lc(df):
    c = df.select_dtypes("object").columns.tolist(); return c[0] if c else None
def _vc(df):
    num = df.select_dtypes("number").columns.tolist()
    for kw in ["revenue","amount","total","inr","sales"]:
        for c in num:
            if kw in c.lower(): return c
    return num[0] if num else None

def smart_chart(df, question="", title="Results"):
    if df is None or df.empty: return None
    num  = df.select_dtypes("number").columns.tolist()
    text = df.select_dtypes("object").columns.tolist()
    if not num: return None
    q, lc, vc, rows = question.lower(), _lc(df), _vc(df), len(df)

    # Time series -> Line
    if lc and any(k in lc.lower() for k in ["month","date","year","quarter"]) and rows>2:
        fig = px.line(df.head(24),x=lc,y=num[0],title=title,markers=True,
                      color_discrete_sequence=PALETTE)
        fig.update_traces(line=dict(color="#3b82f6",width=3),marker=dict(size=8,color="#06d6a0"))
        fig.update_layout(**BASE); return fig

    # Percentage -> Donut
    if vc and (any(k in vc.lower() for k in ["pct","percent"]) or
               any(k in q for k in ["breakdown","percentage","share","distribution"])) and rows<=10:
        fig = px.pie(df.head(10),names=lc,values=vc,title=title,
                     color_discrete_sequence=PALETTE,hole=0.45)
        fig.update_traces(textinfo="label+percent",pull=[0.05]+[0]*(min(rows,10)-1))
        fig.update_layout(**BASE); return fig

    # Two text cols -> Grouped bar
    if len(text)>=2 and num and rows<=30:
        fig = px.bar(df.head(20),x=text[0],y=num[0],color=text[1],
                     title=title,barmode="group",color_discrete_sequence=PALETTE)
        fig.update_layout(**BASE); return fig

    # Many rows -> Horizontal bar
    if lc and vc and rows>8:
        pdf = df[[lc,vc]].dropna().head(15).sort_values(vc)
        fig = px.bar(pdf,y=lc,x=vc,orientation="h",title=title,
                     color=vc,color_continuous_scale=["#1e3a5f","#3b82f6","#06d6a0"],text=vc)
        fig.update_traces(texttemplate="%{text:,.0f}",textposition="outside",marker_line_width=0)
        fig.update_layout(**BASE,showlegend=False,coloraxis_showscale=False,
                          height=max(320,rows*38)); return fig

    # Default -> Vertical bar
    if lc and vc:
        pdf = df[[lc,vc]].dropna().head(15)
        fig = px.bar(pdf,x=lc,y=vc,title=title,
                     color=vc,color_continuous_scale=["#1e3a5f","#3b82f6","#06d6a0"],text=vc)
        fig.update_traces(texttemplate="%{text:,.0f}",textposition="outside",marker_line_width=0)
        fig.update_layout(**BASE,showlegend=False,coloraxis_showscale=False); return fig
    return None


# ═════════════════════════════════════════════════════════════════════════════
#  DB STATS
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data
def db_stats(db_path):
    if not os.path.exists(db_path): return None
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            out = {}
            for t in tables:
                out[t] = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {t}",conn).iloc[0,0]
        return out
    except: return None


# ═════════════════════════════════════════════════════════════════════════════
#  CSS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
:root{--bg:#080d18;--card:#0f1827;--card2:#162032;--border:#1a2840;
      --accent:#3b82f6;--teal:#06d6a0;--text:#e2e8f0;--muted:#64748b;}
.stApp{background:var(--bg);font-family:'DM Sans',sans-serif;color:var(--text);}
.stApp>header{background:transparent!important;}
section[data-testid="stSidebar"]{background:var(--card)!important;border-right:1px solid var(--border);}
#MainMenu,footer{visibility:hidden;}
div[data-testid="stButton"]>button{background:var(--card2)!important;color:#94a3b8!important;
  border:1px solid var(--border)!important;border-radius:8px!important;font-size:.78rem!important;
  transition:all .18s!important;white-space:normal!important;height:auto!important;
  line-height:1.4!important;text-align:left!important;}
div[data-testid="stButton"]>button:hover{background:rgba(59,130,246,.1)!important;
  border-color:rgba(59,130,246,.5)!important;color:#93c5fd!important;}
div[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;
  color:white!important;border:none!important;font-weight:600!important;
  box-shadow:0 4px 20px rgba(37,99,235,.35)!important;}
div[data-testid="stTextArea"] textarea,div[data-testid="stTextInput"] input{
  background:var(--card2)!important;border:1px solid var(--border)!important;
  border-radius:10px!important;color:var(--text)!important;}
div[data-testid="metric-container"]{background:var(--card2)!important;
  border:1px solid var(--border)!important;border-radius:10px!important;padding:14px!important;}
div[data-testid="metric-container"] label{color:var(--muted)!important;font-size:.75rem!important;}
div[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:10px!important;overflow:hidden!important;}
hr{border-color:var(--border)!important;}
.sql-blk{background:#0d1117;border:1px solid #21262d;border-radius:12px;
  padding:18px 22px;font-family:'Space Mono',monospace;font-size:.8rem;color:#e6edf3;
  white-space:pre-wrap;line-height:1.8;overflow-x:auto;margin:8px 0;}
.ins-card{background:linear-gradient(135deg,rgba(6,214,160,.07),rgba(59,130,246,.07));
  border:1px solid rgba(6,214,160,.2);border-radius:12px;padding:16px 20px;margin:10px 0;}
.ins-lbl{font-size:.68rem;font-family:'Space Mono',monospace;color:#06d6a0;
  letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;}
.ins-txt{color:#cbd5e1;font-size:.92rem;line-height:1.7;}
.sec-lbl{font-family:'Space Mono',monospace;font-size:.62rem;letter-spacing:2.5px;
  color:var(--muted);text-transform:uppercase;margin-bottom:8px;}
.alert-ok{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);
  color:#6ee7b7;border-radius:8px;padding:10px 14px;margin:6px 0;}
.alert-err{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
  color:#fca5a5;border-radius:8px;padding:10px 14px;margin:6px 0;}
.alert-warn{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);
  color:#fcd34d;border-radius:8px;padding:10px 14px;margin:6px 0;}
.alert-info{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.3);
  color:#93c5fd;border-radius:8px;padding:10px 14px;margin:6px 0;}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════
for k,v in {"question":"","history":[],"db_path":DB_PATH,"is_user_db":False,
             "db_label":"Synthetic Indian E-Commerce"}.items():
    if k not in st.session_state: st.session_state[k]=v

# ═════════════════════════════════════════════════════════════════════════════
#  AUTO-CREATE DB
# ═════════════════════════════════════════════════════════════════════════════
if not os.path.exists(DB_PATH):
    with st.spinner("Creating demo database for the first time…"):
        _make_synthetic_db()

# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🤖 SQL Assistant")
    st.caption("4-Layer AI Engine · Powered by Groq")
    st.divider()

    st.markdown('<div class="sec-lbl">🔑 Groq API Key</div>',unsafe_allow_html=True)
    api_key = st.text_input("key",type="password",placeholder="gsk_...",
                             label_visibility="collapsed")
    if api_key and api_key.startswith("gsk_"):
        st.markdown('<div class="alert-ok" style="font-size:.8rem;">✅ Connected</div>',unsafe_allow_html=True)
    elif api_key:
        st.markdown('<div class="alert-warn" style="font-size:.8rem;">⚠️ Should start with gsk_</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-info" style="font-size:.8rem;">Get free key: <a href="https://console.groq.com" target="_blank" style="color:#60a5fa">console.groq.com</a></div>',unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sec-lbl">🗄️ Database</div>',unsafe_allow_html=True)
    db_mode = st.radio("db",["Synthetic Demo","Upload CSV/Excel","My SQLite DB"],
                        label_visibility="collapsed")

    if db_mode == "Synthetic Demo":
        st.session_state.update({"db_path":DB_PATH,"is_user_db":False,
                                  "db_label":"Synthetic Indian E-Commerce"})
        stats = db_stats(DB_PATH)
        if stats:
            for t,n in stats.items():
                st.caption(f"• {t}: {n:,} rows")

    elif db_mode == "Upload CSV/Excel":
        up = st.file_uploader("file",type=["csv","xlsx","xls"],label_visibility="collapsed")
        if up:
            try:
                df_up = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                import tempfile
                tmp = os.path.join(tempfile.mkdtemp(),"user.db")
                tbl = os.path.splitext(up.name)[0].lower().replace(" ","_")
                with sqlite3.connect(tmp) as conn:
                    df_up.to_sql(tbl,conn,if_exists="replace",index=False)
                st.session_state.update({"db_path":tmp,"is_user_db":True,"db_label":up.name})
                st.markdown(f'<div class="alert-ok" style="font-size:.8rem;">✅ {up.name} loaded<br>{len(df_up):,} rows · {len(df_up.columns)} cols</div>',unsafe_allow_html=True)
                st.dataframe(df_up.head(3),use_container_width=True)
            except Exception as e:
                st.markdown(f'<div class="alert-err" style="font-size:.8rem;">❌ {e}</div>',unsafe_allow_html=True)

    else:
        sqlite_p = st.text_input("path",placeholder="C:\\path\\to\\db.db",
                                  label_visibility="collapsed")
        if sqlite_p and os.path.exists(sqlite_p):
            st.session_state.update({"db_path":sqlite_p,"is_user_db":True,
                                      "db_label":os.path.basename(sqlite_p)})
            st.markdown('<div class="alert-ok" style="font-size:.8rem;">✅ Connected</div>',unsafe_allow_html=True)
        elif sqlite_p:
            st.markdown('<div class="alert-err" style="font-size:.8rem;">❌ File not found</div>',unsafe_allow_html=True)

    st.divider()
    mem = _load_mem()
    st.markdown(f"""<div style="font-size:.78rem;color:var(--muted)">
        🧠 <b style="color:var(--text)">AI Memory (Layer 4)</b><br>
        Corrections: <b style="color:#06d6a0">{len(mem['corrections'])}</b> &nbsp;|&nbsp;
        Successes: <b style="color:#3b82f6">{len(mem['successes'])}</b>
    </div>""",unsafe_allow_html=True)

    st.divider()
    with st.expander("⚙️ How the 4-Layer Engine works"):
        for n,t,d in [
            ("1","Schema Descriptions","Column meanings, value ranges, relationships"),
            ("2","Business Rules","Date handling, metric definitions, SQLite limits"),
            ("3","Example Patterns","12 proven Q→SQL pairs to learn from"),
            ("4","Self-Learned Memory","Past error fixes saved to disk — AI improves"),
        ]:
            st.markdown(f"**Layer {n} — {t}**  \n{d}")

    with st.expander("📋 Active Schema"):
        db = st.session_state["db_path"]
        if st.session_state["is_user_db"] and os.path.exists(db):
            st.code(discover_schema(db),language="text")
        else:
            st.code(SYNTH_SCHEMA,language="text")

# ═════════════════════════════════════════════════════════════════════════════
#  SAMPLE QUESTIONS
# ═════════════════════════════════════════════════════════════════════════════
SAMPLES = [
    "Which regions in India spend the most on online orders?",
    "What are the top 5 product categories by total revenue?",
    "Show monthly revenue trend for all of 2024",
    "Which payment method is most popular and its share?",
    "Top 10 customers by total spending with their city",
    "What percentage of orders were delivered vs cancelled?",
    "Show revenue breakdown by region and product category",
    "Which states have the most Cash on Delivery orders?",
    "How many male vs female customers and their avg spend?",
    "Which discount level drives the highest revenue?",
    "Best-selling products in the Electronics category",
    "What is the average order value per region?",
    "Which brands have the highest average product rating?",
    "Show order status breakdown for Q4 2024",
    "Compare UPI vs Credit Card orders by region",
    "Top 5 states by number of delivered orders",
    "Average customer age by product category",
    "Which product categories have the most returns?",
    "Show top 10 cities by number of orders placed",
    "Total revenue and orders per quarter in 2024",
]

# ═════════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ═════════════════════════════════════════════════════════════════════════════

# Hero
st.markdown("""
<div style="background:linear-gradient(135deg,#0a1628,#1a3560,#0a1628);
            border:1px solid #1a3560;border-radius:16px;padding:36px 42px;margin-bottom:24px">
  <span style="background:rgba(59,130,246,.12);color:#60a5fa;border:1px solid rgba(59,130,246,.25);
               border-radius:20px;padding:3px 14px;font-size:.72rem;font-family:monospace;
               letter-spacing:1px">4-LAYER AI ENGINE · OPEN SOURCE · FREE</span>
  <h1 style="font-size:2.5rem;font-weight:800;color:#f1f5f9;margin:14px 0 8px;line-height:1.15">
    Ask your database anything<br><span style="color:#3b82f6">in plain English.</span>
  </h1>
  <p style="color:#64748b;font-size:.98rem;margin:0;max-width:580px;line-height:1.7">
    Every question is grounded in 4 layers of context — schema descriptions, business rules,
    example patterns, and self-learned corrections — so answers are
    <b style="color:#e2e8f0">trustworthy</b>, not just plausible-looking.
  </p>
</div>
""",unsafe_allow_html=True)

# How it works strip
c1,c2,c3,c4 = st.columns(4)
for col,icon,title,desc in [
    (c1,"✍️","1. Ask","Type any question in plain English"),
    (c2,"🧠","2. Generate","4-Layer AI writes precise SQL"),
    (c3,"⚡","3. Execute","Runs on your database instantly"),
    (c4,"📊","4. Explore","Table + Smart Chart + Insight"),
]:
    col.markdown(f"""
    <div style="background:#111827;border:1px solid #1e293b;border-radius:10px;
                padding:16px;text-align:center;">
        <div style="font-size:1.4rem">{icon}</div>
        <div style="font-weight:700;color:#e2e8f0;font-size:.88rem;margin:4px 0">{title}</div>
        <div style="color:#64748b;font-size:.75rem;line-height:1.4">{desc}</div>
    </div>""",unsafe_allow_html=True)

st.markdown("<br>",unsafe_allow_html=True)

# Tabs
tab_ask, tab_history, tab_explore = st.tabs([
    "🔍 Ask a Question",
    f"📜 History ({len(st.session_state['history'])})",
    "🗄️ Explore Database",
])

# ─────────────────────────────────────────────────────────────────────────────
with tab_ask:
    # DB indicator
    st.markdown(f"""
    <div style="font-size:.8rem;color:#64748b;margin-bottom:10px">
    📂 Database: <b style="color:#e2e8f0">{st.session_state['db_label']}</b>
    </div>""",unsafe_allow_html=True)

    st.markdown('<div class="sec-lbl">Quick-start samples</div>',unsafe_allow_html=True)
    cols = st.columns(4)
    for i,q in enumerate(SAMPLES):
        if cols[i%4].button(q,key=f"sq{i}",use_container_width=True):
            st.session_state["question"]=q; st.rerun()

    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown('<div class="sec-lbl">Your question</div>',unsafe_allow_html=True)
    question = st.text_area("q",value=st.session_state.get("question",""),height=90,
                             label_visibility="collapsed",
                             placeholder="e.g. Which regions in India spent the most on online orders in Q4 2024?")

    bc1,bc2,_ = st.columns([2.2,1,4])
    go  = bc1.button("🚀 Generate SQL & Get Answer",type="primary",use_container_width=True)
    clr = bc2.button("✕ Clear",use_container_width=True)
    if clr: st.session_state["question"]=""; st.rerun()

    if go:
        if not api_key:
            st.markdown('<div class="alert-err">❌ Enter your Groq API key in the sidebar.</div>',unsafe_allow_html=True)
            st.stop()
        if not question.strip():
            st.markdown('<div class="alert-warn">⚠️ Enter a question or click a sample above.</div>',unsafe_allow_html=True)
            st.stop()

        db     = st.session_state["db_path"]
        is_usr = st.session_state["is_user_db"]
        schema = discover_schema(db) if is_usr else SYNTH_SCHEMA
        rules  = BUSINESS_RULES if not is_usr else (
            BUSINESS_RULES + "\nNote: This is a user-supplied database. Adapt column names from schema.")
        examples = EXAMPLES if not is_usr else ""

        with st.spinner("🧠 4-Layer AI is writing your SQL…"):
            try:
                client = _client(api_key)
                sql,err = gen_sql(question, client, schema, rules, examples)
            except Exception as e:
                sql,err = None,str(e)

        if err or not sql:
            st.markdown(f'<div class="alert-err">❌ AI error: {err}</div>',unsafe_allow_html=True)
            st.stop()

        st.divider()
        retry=False
        escaped = sql.replace("<","&lt;").replace(">","&gt;")
        st.markdown("**🤖 AI-Generated SQL** (written by Groq Llama 3.1 · 4-layer context · zero SQL needed)")
        st.markdown(f'<div class="sql-blk">{escaped}</div>',unsafe_allow_html=True)

        with st.spinner("⚡ Executing…"):
            df,exec_err = run_q(sql,db)

        if exec_err:
            with st.spinner("⚡ Auto-correcting SQL error (Layer 4)…"):
                fixed,fix_err = fix_sql(question,sql,exec_err,client)
                retry=True
            if fix_err or not fixed:
                st.markdown(f'<div class="alert-err">❌ SQL error: {exec_err}</div>',unsafe_allow_html=True)
                st.stop()
            sql=fixed; escaped=sql.replace("<","&lt;").replace(">","&gt;")
            st.markdown("**⚡ Auto-corrected SQL:**")
            st.markdown(f'<div class="sql-blk">{escaped}</div>',unsafe_allow_html=True)
            st.markdown('<div class="alert-warn">The first SQL had an error. AI auto-corrected it and saved the fix to memory.</div>',unsafe_allow_html=True)
            df,exec_err2 = run_q(sql,db)
            if exec_err2:
                st.markdown(f'<div class="alert-err">❌ {exec_err2}</div>',unsafe_allow_html=True)
                st.stop()

        if df is None or df.empty:
            st.markdown('<div class="alert-warn">⚠️ Query returned no rows. Try a broader question.</div>',unsafe_allow_html=True)
            st.stop()

        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Rows",f"{len(df):,}")
        m2.metric("Columns",len(df.columns))
        m3.metric("Auto-corrected","Yes ⚡" if retry else "No ✅")
        m4.metric("Model","Llama 3.1 8B")

        st.markdown('<div class="sec-lbl" style="margin-top:14px">Query Results</div>',unsafe_allow_html=True)
        st.dataframe(df,use_container_width=True,height=min(420,80+len(df)*36))
        st.download_button("📥 Download CSV",df.to_csv(index=False).encode(),"result.csv","text/csv")

        fig = smart_chart(df,question,question[:60]+("…" if len(question)>60 else ""))
        if fig is not None:
            st.markdown('<div class="sec-lbl" style="margin-top:16px">Smart Chart</div>',unsafe_allow_html=True)
            num = df.select_dtypes("number").columns.tolist()
            txt = df.select_dtypes("object").columns.tolist()
            if num and txt:
                st.caption(f"{len(df)} rows · {num[0].replace('_',' ').title()} by {txt[0].replace('_',' ').title()}")
            st.plotly_chart(fig,use_container_width=True)

        with st.spinner("Generating business insight…"):
            insight = get_insight(question,df,client)
        if insight:
            st.markdown(f"""
            <div class="ins-card">
              <div class="ins-lbl">📌 Business Insight</div>
              <div class="ins-txt">{insight}</div>
            </div>""",unsafe_allow_html=True)

        m = _load_mem()
        m["successes"].append({"question":question,"sql":sql})
        m["successes"]=m["successes"][-50:]
        _save_mem(m)

        st.session_state["history"].insert(0,{"question":question,"sql":sql,
            "rows":len(df),"insight":insight,"retried":retry})
        st.session_state["history"]=st.session_state["history"][:30]

# ─────────────────────────────────────────────────────────────────────────────
with tab_history:
    h = st.session_state["history"]
    if not h:
        st.markdown('<div class="alert-info">No queries yet — ask your first question above!</div>',unsafe_allow_html=True)
    else:
        if st.button("🗑 Clear History"): st.session_state["history"]=[]; st.rerun()
        for i,item in enumerate(h):
            label = f"Q{i+1}: {item['question'][:70]}… ({item['rows']} rows)"
            if item.get("retried"): label += " ⚡"
            with st.expander(label):
                escaped = item["sql"].replace("<","&lt;").replace(">","&gt;")
                st.markdown(f'<div class="sql-blk">{escaped}</div>',unsafe_allow_html=True)
                if item.get("insight"):
                    st.markdown(f'<div class="ins-card"><div class="ins-lbl">Insight</div><div class="ins-txt">{item["insight"]}</div></div>',unsafe_allow_html=True)
                if st.button(f"Re-run",key=f"r{i}"):
                    st.session_state["question"]=item["question"]; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
with tab_explore:
    db = st.session_state["db_path"]
    if not os.path.exists(db):
        st.error("Database not found")
    else:
        stats = db_stats(db)
        if stats:
            cols2 = st.columns(min(len(stats),4))
            for i,(t,n) in enumerate(stats.items()):
                cols2[i%4].metric(t.title(),f"{n:,}")
        st.divider()
        try:
            with sqlite3.connect(db) as conn:
                cur=conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables=[r[0] for r in cur.fetchall()]
            sel = st.selectbox("Browse table:",tables)
            if sel:
                n_rows = st.slider("Rows to show:",5,50,10)
                with sqlite3.connect(db) as conn:
                    samp=pd.read_sql_query(f"SELECT * FROM {sel} LIMIT {n_rows}",conn)
                st.dataframe(samp,use_container_width=True)
        except Exception as e: st.error(str(e))

# Footer
st.markdown("<br><hr>",unsafe_allow_html=True)
st.markdown("""
<div style="display:flex;justify-content:space-between;font-size:.72rem;color:#1e3a5f;flex-wrap:wrap;gap:8px">
  <span>GenAI SQL Assistant · 4-Layer AI Engine · Open Source</span>
  <span>Groq Llama 3.1 · SQLite · Streamlit · Python</span>
</div>""",unsafe_allow_html=True)
