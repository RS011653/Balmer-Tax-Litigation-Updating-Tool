from __future__ import annotations

import uuid
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import bcrypt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import Client, create_client


# =========================================================
# SETTINGS
# =========================================================
@dataclass(frozen=True)
class Settings:
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_APP_PASSWORD: str
    ADMIN_EMAIL: str
    APP_VERSION: str


def get_settings() -> Settings:
    s = st.secrets
    return Settings(
        SUPABASE_URL=s["SUPABASE_URL"],
        SUPABASE_KEY=s["SUPABASE_KEY"],
        SUPABASE_BUCKET=s.get("SUPABASE_BUCKET", "litigation-documents"),
        SMTP_HOST=s.get("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(s.get("SMTP_PORT", 587)),
        SMTP_USER=s.get("SMTP_USER", ""),
        SMTP_APP_PASSWORD=s.get("SMTP_APP_PASSWORD", ""),
        ADMIN_EMAIL=s.get("ADMIN_EMAIL", "caraja.saha@gmail.com"),
        APP_VERSION=s.get("APP_VERSION", "4.2.0"),
    )


settings = get_settings()


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Balmer Lawrie Litigation Tool",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# STYLING
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
        background:
            radial-gradient(circle at top left, rgba(125,211,252,0.35), transparent 26%),
            radial-gradient(circle at top right, rgba(196,181,253,0.25), transparent 22%),
            linear-gradient(135deg, #f8fbff 0%, #eef4ff 40%, #e7efff 100%);
        color: #0f172a;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1450px;
    }

    header[data-testid="stHeader"] {
        background: rgba(255,255,255,0.72);
    }

    [data-testid="stDecoration"] {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 45%, #c7d2fe 100%) !important;
        border-right: 1px solid rgba(59,130,246,0.20);
    }

    [data-testid="stSidebar"] * {
        color: #1e3a8a !important;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

    .hero {
        border-radius: 28px;
        padding: 28px 32px;
        margin-bottom: 18px;
        background:
            radial-gradient(circle at 15% 18%, rgba(255,255,255,0.32), transparent 18%),
            linear-gradient(135deg, #2563eb 0%, #0ea5e9 42%, #8b5cf6 100%);
        box-shadow: 0 22px 60px rgba(37, 99, 235, 0.18);
        border: 1px solid rgba(255,255,255,0.30);
    }

    .hero h1 {
        margin: 0;
        color: white;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }

    .hero p {
        margin: 8px 0 0 0;
        color: rgba(255,255,255,0.95);
        font-size: 1rem;
    }

    .hero-badges {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 16px;
    }

    .badge {
        background: rgba(255,255,255,0.18);
        color: white;
        border: 1px solid rgba(255,255,255,0.28);
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.84rem;
        font-weight: 700;
    }

    .panel, div[data-testid="stForm"], div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(148,163,184,0.22);
        border-radius: 22px;
        box-shadow: 0 16px 40px rgba(15,23,42,0.08);
        backdrop-filter: blur(10px);
        color: #0f172a;
    }

    div[data-testid="stForm"] {
        padding: 1rem 1rem 0.65rem 1rem;
    }

    div[data-testid="stMetric"] {
        padding: 10px 14px;
    }

    .feature-card {
        min-height: 100%;
        border-radius: 24px;
        padding: 28px;
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,250,252,0.98));
        border: 1px solid rgba(148,163,184,0.22);
        box-shadow: 0 18px 44px rgba(15,23,42,0.08);
        color: #0f172a;
    }

    .feature-card h2 {
        color: #0f172a;
        margin: 0 0 10px 0;
        font-size: 1.55rem;
    }

    .feature-card p {
        color: #334155;
    }

    .feature-item {
        padding: 12px 14px;
        border-radius: 16px;
        background: #eff6ff;
        color: #1e3a8a;
        border: 1px solid #bfdbfe;
        font-size: 0.95rem;
        margin-top: 10px;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 46px;
        background: #ffffff;
        border-radius: 999px;
        padding: 0 18px;
        color: #0f172a !important;
        font-weight: 700;
        border: 1px solid rgba(148,163,184,0.28);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff7a18, #ff4d6d 55%, #d946ef) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
        box-shadow: 0 14px 34px rgba(236,72,153,0.24) !important;
    }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stDateInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid rgba(148,163,184,0.32) !important;
        border-radius: 14px !important;
    }

    .stButton > button, .stDownloadButton > button {
        border: 1px solid rgba(255,255,255,0.20) !important;
        color: #ffffff !important;
        background: linear-gradient(135deg, #ff7a18, #ff5a36 42%, #f43f5e 72%, #ec4899) !important;
        border-radius: 16px !important;
        padding: 0.78rem 1.15rem !important;
        font-weight: 800 !important;
        font-size: 0.98rem !important;
        box-shadow: 0 16px 40px rgba(244,63,94,0.24) !important;
        text-shadow: 0 1px 1px rgba(0,0,0,0.20);
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        filter: brightness(1.04);
        transform: translateY(-1px);
    }

    div[data-testid="stFileUploader"] section {
        background: #ffffff !important;
        border-radius: 18px !important;
        border: 1px solid rgba(148,163,184,0.28) !important;
    }

    .footer-note {
        text-align: center;
        color: #334155;
        font-size: 0.95rem;
        margin-top: 30px;
        padding-top: 14px;
        border-top: 1px solid rgba(148,163,184,0.30);
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SUPABASE
# =========================================================
@st.cache_resource
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


sb = get_supabase()


# =========================================================
# CONSTANTS
# =========================================================
LITIGATION_COLUMNS = [
    "division_name",
    "employee_id",
    "person_name",
    "tax_type",
    "disputed_demand",
    "financial_year",
    "disputed_forum",
    "last_hearing_date",
    "next_hearing_date",
    "current_status",
    "remarks",
]


# =========================================================
# HELPERS
# =========================================================
def render_footer() -> None:
    st.markdown(
        '<div class="footer-note">This app developed by Raja Saha, Sr Manager (Taxation), Balmer Lawrie &amp; Co Ltd</div>',
        unsafe_allow_html=True,
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def sanitize(text: Any) -> str:
    if text is None:
        return ""
    return str(text).replace("<", "").replace(">", "").strip()


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def normalize_date_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime("%Y-%m-%d")


def send_email(to_address: str, subject: str, html_body: str) -> bool:
    if not to_address or not settings.SMTP_USER or not settings.SMTP_APP_PASSWORD:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_address
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_address], msg.as_string())
        return True
    except Exception:
        return False


def notify_admin(action_type: str, table_name: str, target_id: str, details: dict | None = None) -> None:
    actor_name = st.session_state.get("employee_name", "Unknown User")
    actor_id = st.session_state.get("employee_id", "Unknown ID")
    actor_email = st.session_state.get("email", "No email")
    subject = f"Litigation Tool Update: {action_type} on {table_name}"

    detail_html = ""
    if details:
        rows = "".join(
            f"<tr><td style='padding:6px 10px;border:1px solid #ddd;'><b>{k}</b></td><td style='padding:6px 10px;border:1px solid #ddd;'>{v}</td></tr>"
            for k, v in details.items()
        )
        detail_html = f"<table style='border-collapse:collapse;margin-top:10px;'>{rows}</table>"

    html = f"""
    <div style="font-family:Arial,sans-serif;">
        <h3>Balmer Lawrie Litigation Tool Modification Alert</h3>
        <p><b>Action:</b> {action_type}</p>
        <p><b>Table:</b> {table_name}</p>
        <p><b>Target ID:</b> {target_id}</p>
        <p><b>Modified by:</b> {actor_name} ({actor_id})</p>
        <p><b>User Email:</b> {actor_email}</p>
        {detail_html}
    </div>
    """
    send_email(settings.ADMIN_EMAIL, subject, html)


def login(employee_id: str, password: str) -> tuple[bool, str]:
    employee_id = employee_id.strip()
    if not employee_id:
        return False, "Please enter Employee ID."

    res = sb.table("employees").select("*").eq("employee_id", employee_id).execute()
    if not res.data:
        return False, "Employee ID not found."

    user = res.data[0]
    if not user.get("is_active", True):
        return False, "Account is deactivated."

    if not verify_password(password, user.get("password_hash", "")):
        return False, "Incorrect password."

    st.session_state["authenticated"] = True
    st.session_state["employee_id"] = user.get("employee_id")
    st.session_state["employee_name"] = user.get("employee_name")
    st.session_state["role"] = user.get("role", "user")
    st.session_state["division"] = user.get("division")
    st.session_state["email"] = user.get("email")
    return True, "Login successful."


def logout() -> None:
    for key in ["authenticated", "employee_id", "employee_name", "role", "division", "email"]:
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def render_hero(title: str, subtitle: str) -> None:
    emp = st.session_state.get("employee_name", "Guest")
    role = st.session_state.get("role", "guest").title()

    st.markdown(
        f"""
        <div class="hero">
            <h1>⚖️ {title}</h1>
            <p>{subtitle}</p>
            <div class="hero-badges">
                <span class="badge">Version {settings.APP_VERSION}</span>
                <span class="badge">Role: {role}</span>
                <span class="badge">User: {sanitize(emp)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fetch_table(table_name: str, filters: dict | None = None) -> pd.DataFrame:
    query = sb.table(table_name).select("*")
    for key, value in (filters or {}).items():
        if value not in (None, ""):
            query = query.eq(key, value)
    return pd.DataFrame(query.execute().data or [])


def save_audit(action_type: str, target_table: str, target_id: str, details: dict | None = None) -> None:
    try:
        sb.table("audit_logs").insert(
            {
                "actor_employee_id": st.session_state.get("employee_id"),
                "actor_name": st.session_state.get("employee_name"),
                "action_type": action_type,
                "target_table": target_table,
                "target_id": str(target_id),
                "details": normalize_value(details or {}),
            }
        ).execute()
    except Exception:
        pass


def get_case_dataframe() -> pd.DataFrame:
    if is_admin():
        return fetch_table("litigation_master")
    return fetch_table("litigation_master", {"employee_id": st.session_state.get("employee_id")})


def case_label(row: pd.Series) -> str:
    return f"{row.get('id')} | {row.get('case_ref', '')} | {row.get('person_name', '')} | {row.get('tax_type', '')}"


def safe_records_from_df(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    if "Employee ID" in df.columns:
        df = df.rename(columns={"Employee ID": "employee_id"})

    for col in LITIGATION_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[LITIGATION_COLUMNS]
    df = df.astype(object).where(pd.notnull(df), None)

    records = []
    for _, row in df.iterrows():
        rec = {}
        for col in LITIGATION_COLUMNS:
            val = row.get(col)
            if col in ["last_hearing_date", "next_hearing_date"]:
                rec[col] = normalize_date_string(val)
            else:
                rec[col] = normalize_value(val)

        if not rec.get("current_status"):
            rec["current_status"] = "In Progress"

        records.append(rec)

    return records


def add_case_ref(records: list[dict]) -> list[dict]:
    out = []
    for row in records:
        r = dict(row)
        r["case_ref"] = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        if not r.get("current_status"):
            r["current_status"] = "In Progress"
        out.append(r)
    return out


def import_litigation_file(uploaded_file) -> tuple[bool, str]:
    try:
        df = pd.read_excel(uploaded_file)
        records = safe_records_from_df(df)
        records = add_case_ref(records)

        fallback_emp = st.session_state.get("employee_id")
        clean_records = []

        for row in records:
            clean_row = {k: normalize_value(v) for k, v in row.items()}
            clean_row["last_hearing_date"] = normalize_date_string(clean_row.get("last_hearing_date"))
            clean_row["next_hearing_date"] = normalize_date_string(clean_row.get("next_hearing_date"))
            if not clean_row.get("employee_id"):
                clean_row["employee_id"] = fallback_emp
            clean_records.append(clean_row)

        clean_records = [r for r in clean_records if any(v not in [None, ""] for v in r.values())]
        if not clean_records:
            return False, "No valid rows found in uploaded file."

        sb.table("litigation_master").insert(clean_records).execute()
        save_audit("import", "litigation_master", f"{len(clean_records)} rows", {"rows": len(clean_records)})
        notify_admin("import", "litigation_master", f"{len(clean_records)} rows", {"rows": len(clean_records)})
        return True, f"Imported {len(clean_records)} litigation rows successfully."
    except Exception as exc:
        return False, f"Import failed: {exc}"


def upload_supporting_document(case_id: Any, file_obj) -> tuple[bool, str]:
    if file_obj is None:
        return False, "Please select a file."
    try:
        path = f"{case_id}/{uuid.uuid4().hex}_{file_obj.name}"
        file_bytes = file_obj.getvalue()
        sb.storage.from_(settings.SUPABASE_BUCKET).upload(
            path,
            file_bytes,
            {"content-type": file_obj.type or "application/octet-stream"},
        )
        doc_payload = {
            "case_id": case_id,
            "uploaded_by": st.session_state.get("employee_id"),
            "file_name": file_obj.name,
            "storage_path": path,
            "file_size": len(file_bytes),
        }
        sb.table("documents").insert(doc_payload).execute()
        save_audit("upload", "documents", path, {"case_id": case_id, "file_name": file_obj.name})
        notify_admin("upload", "documents", path, {"case_id": case_id, "file_name": file_obj.name})
        return True, "Supporting paper uploaded successfully."
    except Exception as exc:
        return False, f"Upload failed: {exc}"


def get_download_link_from_storage(storage_path: str) -> str | None:
    try:
        res = sb.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(storage_path, 3600)
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signed_url")
        if hasattr(res, "get"):
            return res.get("signedURL") or res.get("signed_url")
        return None
    except Exception:
        return None


def delete_document(doc_row: dict) -> tuple[bool, str]:
    try:
        storage_path = doc_row.get("storage_path")
        doc_id = doc_row.get("id")
        if storage_path:
            try:
                sb.storage.from_(settings.SUPABASE_BUCKET).remove([storage_path])
            except Exception:
                pass

        sb.table("documents").delete().eq("id", doc_id).execute()
        save_audit("delete_document", "documents", doc_id, {"file_name": doc_row.get("file_name")})
        notify_admin("delete_document", "documents", str(doc_id), {"file_name": doc_row.get("file_name")})
        return True, "Document deleted successfully."
    except Exception as exc:
        return False, f"Delete failed: {exc}"


def can_delete_document(doc_row: dict) -> bool:
    if is_admin():
        return True
    return str(doc_row.get("uploaded_by", "")) == str(st.session_state.get("employee_id", ""))


# =========================================================
# LOGIN PAGE
# =========================================================
def render_login_page() -> None:
    render_hero(
        "Balmer Lawrie Latest Indirect Tax Litigation Updating Tool",
        "Documents are now downloadable and deletable by the right user permissions.",
    )

    col1, col2 = st.columns([1.1, 1], gap="large")

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <h2>Updated secure workflow.</h2>
                <p>This version adds a fixed developer footer and stronger document control.</p>
                <div class="feature-item">Footer credit line is displayed at the bottom of the app.</div>
                <div class="feature-item">Uploaded documents can be downloaded from the app.</div>
                <div class="feature-item">Admin can delete any uploaded document.</div>
                <div class="feature-item">User can delete only own uploaded documents.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        tab1, tab2, tab3 = st.tabs(["Login", "Forgot Password", "Change Password"])

        with tab1:
            with st.form("login_form"):
                emp_id = st.text_input("Employee ID")
                pw = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    ok, msg = login(emp_id, pw)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with tab2:
            with st.form("forgot_pw_form"):
                emp_id_fp = st.text_input("Employee ID for reset")
                submitted_fp = st.form_submit_button("Reset Password", use_container_width=True)
                if submitted_fp:
                    res = sb.table("employees").select("*").eq("employee_id", emp_id_fp.strip()).execute()
                    if not res.data:
                        st.error("Employee ID not found.")
                    else:
                        user = res.data[0]
                        email = user.get("email") or ""
                        if not email:
                            st.error("No email available for this user.")
                        else:
                            sb.table("employees").update(
                                {"password_hash": hash_password(email)}
                            ).eq("employee_id", emp_id_fp.strip()).execute()
                            st.success("Password reset to registered email ID.")
                            notify_admin("password_reset", "employees", emp_id_fp.strip(), {"reset_to_email": email})

        with tab3:
            with st.form("change_pw_form"):
                emp_id_ch = st.text_input("Employee ID")
                old_pw = st.text_input("Old Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                submitted_ch = st.form_submit_button("Change Password", use_container_width=True)
                if submitted_ch:
                    res = sb.table("employees").select("*").eq("employee_id", emp_id_ch.strip()).execute()
                    if not res.data:
                        st.error("Employee ID not found.")
                    else:
                        user = res.data[0]
                        if not verify_password(old_pw, user.get("password_hash", "")):
                            st.error("Old password incorrect.")
                        else:
                            sb.table("employees").update(
                                {"password_hash": hash_password(new_pw)}
                            ).eq("employee_id", emp_id_ch.strip()).execute()
                            st.success("Password changed successfully.")
                            notify_admin("password_change", "employees", emp_id_ch.strip(), {"changed_by": emp_id_ch.strip()})

    render_footer()


# =========================================================
# SIDEBAR
# =========================================================
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## ⚖️ Litigation Console")
        st.caption(f"{st.session_state.get('employee_name')} ({st.session_state.get('employee_id')})")

        options = ["Dashboard", "Litigation", "Documents", "Profile"]
        if is_admin():
            options.insert(3, "Admin")

        choice = st.radio("Navigate", options)

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

        return choice


# =========================================================
# DASHBOARD
# =========================================================
def render_dashboard() -> None:
    render_hero("Dashboard", "Live case portfolio by tax type, status, and user visibility.")

    df = get_case_dataframe()

    if df.empty:
        st.info("No litigation records found.")
        render_footer()
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cases", len(df))
    c2.metric("Tax Types", int(df.get("tax_type", pd.Series(dtype=str)).fillna("Unknown").nunique()))
    c3.metric("Next Hearings", int(df.get("next_hearing_date", pd.Series(dtype=object)).notna().sum()))
    c4.metric(
        "In Progress",
        int(df.get("current_status", pd.Series(dtype=str)).fillna("").str.contains("Progress", case=False).sum()),
    )

    left, right = st.columns(2)

    with left:
        tax = df.get("tax_type", pd.Series(dtype=str)).fillna("Unknown").value_counts().reset_index()
        tax.columns = ["tax_type", "cases"]
        fig = px.bar(
            tax,
            x="tax_type",
            y="cases",
            color="tax_type",
            color_discrete_sequence=["#38bdf8", "#22c55e", "#f97316", "#a855f7", "#ec4899"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#0f172a",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        stat = df.get("current_status", pd.Series(dtype=str)).fillna("Unknown").value_counts().reset_index()
        stat.columns = ["current_status", "cases"]
        fig2 = px.pie(
            stat,
            names="current_status",
            values="cases",
            hole=0.56,
            color_discrete_sequence=["#60a5fa", "#fb7185", "#34d399", "#f59e0b", "#c084fc"],
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#0f172a",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)
    render_footer()


# =========================================================
# LITIGATION
# =========================================================
def render_litigation() -> None:
    render_hero(
        "Litigation Register",
        "Users can edit records and manage their own uploaded documents, while admin can manage all documents.",
    )

    df = get_case_dataframe()

    tab_names = ["Browse & Edit", "Add Record", "Import Excel", "Supporting Papers"]
    if is_admin():
        tab_names.append("Admin Delete")

    tabs = st.tabs(tab_names)

    with tabs[0]:
        if df.empty:
            st.info("No litigation records available.")
        else:
            q = st.text_input("Search litigation")
            work = df.copy()
            if q:
                mask = work.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False))
                work = work[mask.any(axis=1)]

            st.dataframe(work, use_container_width=True, hide_index=True)

            editable_options = [case_label(row) for _, row in work.iterrows()]
            selected_label = st.selectbox("Select case to edit", editable_options)
            selected_row = work[work.apply(lambda x: case_label(x) == selected_label, axis=1)].iloc[0].to_dict()

            st.markdown("### Edit selected case")
            with st.form("edit_litigation_form"):
                c1, c2, c3 = st.columns(3)
                division_name = c1.text_input("Division Name", value=selected_row.get("division_name") or "")
                employee_id = c2.text_input(
                    "Employee ID",
                    value=str(selected_row.get("employee_id") or ""),
                    disabled=not is_admin(),
                )
                person_name = c3.text_input("Person Name", value=selected_row.get("person_name") or "")

                d1, d2, d3 = st.columns(3)
                tax_type = d1.text_input("Tax Type", value=selected_row.get("tax_type") or "")
                disputed_demand = d2.text_input("Disputed Demand", value=selected_row.get("disputed_demand") or "")
                financial_year = d3.text_input("Financial Year", value=selected_row.get("financial_year") or "")

                e1, e2, e3 = st.columns(3)
                disputed_forum = e1.text_input("Disputed Forum", value=selected_row.get("disputed_forum") or "")
                last_hearing_date = e2.text_input(
                    "Last Hearing Date (YYYY-MM-DD)",
                    value=str(selected_row.get("last_hearing_date") or ""),
                )
                next_hearing_date = e3.text_input(
                    "Next Hearing Date (YYYY-MM-DD)",
                    value=str(selected_row.get("next_hearing_date") or ""),
                )

                current_status = st.text_input("Current Status", value=selected_row.get("current_status") or "In Progress")
                remarks = st.text_area("Remarks", value=selected_row.get("remarks") or "")

                submitted_edit = st.form_submit_button("Update Litigation Record", use_container_width=True)
                if submitted_edit:
                    payload = {
                        "division_name": sanitize(division_name) or None,
                        "employee_id": sanitize(employee_id) or st.session_state.get("employee_id"),
                        "person_name": sanitize(person_name) or None,
                        "tax_type": sanitize(tax_type) or None,
                        "disputed_demand": sanitize(disputed_demand) or None,
                        "financial_year": sanitize(financial_year) or None,
                        "disputed_forum": sanitize(disputed_forum) or None,
                        "last_hearing_date": normalize_date_string(last_hearing_date),
                        "next_hearing_date": normalize_date_string(next_hearing_date),
                        "current_status": sanitize(current_status) or "In Progress",
                        "remarks": sanitize(remarks) or None,
                    }

                    sb.table("litigation_master").update(payload).eq("id", selected_row["id"]).execute()
                    save_audit("update", "litigation_master", selected_row["id"], payload)
                    notify_admin("update", "litigation_master", str(selected_row["id"]), payload)
                    st.success("Litigation record updated successfully.")
                    st.rerun()

    with tabs[1]:
        with st.form("add_litigation_form"):
            c1, c2, c3 = st.columns(3)
            division_name = c1.text_input("Division Name")
            employee_id = c2.text_input(
                "Employee ID",
                value=st.session_state.get("employee_id", "") if not is_admin() else "",
            )
            person_name = c3.text_input("Person Name")

            d1, d2, d3 = st.columns(3)
            tax_type = d1.text_input("Tax Type")
            disputed_demand = d2.text_input("Disputed Demand")
            financial_year = d3.text_input("Financial Year")

            e1, e2, e3 = st.columns(3)
            disputed_forum = e1.text_input("Disputed Forum")
            last_hearing_date = e2.text_input("Last Hearing Date (YYYY-MM-DD or blank)")
            next_hearing_date = e3.text_input("Next Hearing Date (YYYY-MM-DD or blank)")

            current_status = st.text_input("Current Status", value="In Progress")
            remarks = st.text_area("Remarks")

            submitted = st.form_submit_button("Save Litigation Record", use_container_width=True)

            if submitted:
                payload = {
                    "case_ref": f"CASE-{uuid.uuid4().hex[:8].upper()}",
                    "employee_id": sanitize(employee_id) or st.session_state.get("employee_id"),
                    "division_name": sanitize(division_name) or None,
                    "person_name": sanitize(person_name) or None,
                    "tax_type": sanitize(tax_type) or None,
                    "disputed_demand": sanitize(disputed_demand) or None,
                    "financial_year": sanitize(financial_year) or None,
                    "disputed_forum": sanitize(disputed_forum) or None,
                    "last_hearing_date": normalize_date_string(last_hearing_date),
                    "next_hearing_date": normalize_date_string(next_hearing_date),
                    "current_status": sanitize(current_status) or "In Progress",
                    "remarks": sanitize(remarks) or None,
                }

                sb.table("litigation_master").insert(payload).execute()
                save_audit("insert", "litigation_master", payload["case_ref"], payload)
                notify_admin("insert", "litigation_master", payload["case_ref"], payload)
                st.success("Litigation record saved.")
                st.rerun()

    with tabs[2]:
        upl = st.file_uploader("Upload litigation Excel", type=["xlsx", "xls"])
        if upl is not None and st.button("Import Litigation File", use_container_width=True):
            ok, msg = import_litigation_file(upl)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        st.caption("Excel dates are converted to YYYY-MM-DD before Supabase insert.")

    with tabs[3]:
        if df.empty:
            st.info("No litigation cases available for supporting paper upload.")
        else:
            attach_options = [case_label(row) for _, row in df.iterrows()]
            attach_label = st.selectbox("Select case for supporting papers", attach_options, key="attach_case")
            attach_row = df[df.apply(lambda x: case_label(x) == attach_label, axis=1)].iloc[0].to_dict()

            upload_file = st.file_uploader("Upload supporting paper", key="supporting_paper_upload")
            if st.button("Upload Supporting Paper", use_container_width=True):
                ok, msg = upload_supporting_document(attach_row["id"], upload_file)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            docs = fetch_table("documents", {"case_id": attach_row["id"]})
            st.markdown("### Existing supporting papers")
            if docs.empty:
                st.info("No supporting papers uploaded for this case.")
            else:
                docs = docs.copy()
                docs["download_link"] = docs["storage_path"].apply(get_download_link_from_storage)

                for _, doc in docs.iterrows():
                    st.markdown(f"#### {doc.get('file_name')}")
                    c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
                    c1.write(f"Uploaded by: {doc.get('uploaded_by')}")
                    c2.write(f"Size: {doc.get('file_size')}")
                    download_link = doc.get("download_link")
                    if download_link:
                        c3.markdown(f"[Download File]({download_link})")
                    else:
                        c3.write("Download link unavailable")

                    if can_delete_document(doc.to_dict()):
                        if c4.button("Delete File", key=f"delete_doc_{doc.get('id')}"):
                            ok, msg = delete_document(doc.to_dict())
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    if is_admin():
        with tabs[4]:
            if df.empty:
                st.info("No cases available for delete.")
            else:
                delete_options = [case_label(row) for _, row in df.iterrows()]
                single_delete_label = st.selectbox("Delete single case", delete_options, key="single_delete_case")
                if st.button("Delete Selected Case", use_container_width=True):
                    single_row = df[df.apply(lambda x: case_label(x) == single_delete_label, axis=1)].iloc[0].to_dict()
                    sb.table("litigation_master").delete().eq("id", single_row["id"]).execute()
                    save_audit("delete", "litigation_master", single_row["id"])
                    notify_admin("delete", "litigation_master", str(single_row["id"]), {"case_ref": single_row.get("case_ref")})
                    st.success("Selected case deleted.")
                    st.rerun()

                multi_delete_labels = st.multiselect("Delete multiple cases", delete_options)
                if st.button("Delete Multiple Cases", use_container_width=True):
                    ids_to_delete = []
                    for lbl in multi_delete_labels:
                        row = df[df.apply(lambda x: case_label(x) == lbl, axis=1)].iloc[0].to_dict()
                        ids_to_delete.append(row["id"])

                    if not ids_to_delete:
                        st.warning("Please select cases for bulk delete.")
                    else:
                        for cid in ids_to_delete:
                            sb.table("litigation_master").delete().eq("id", cid).execute()
                            save_audit("bulk_delete", "litigation_master", cid)
                        notify_admin("bulk_delete", "litigation_master", ",".join(map(str, ids_to_delete)), {"count": len(ids_to_delete)})
                        st.success(f"Deleted {len(ids_to_delete)} cases.")
                        st.rerun()

    render_footer()


# =========================================================
# DOCUMENTS
# =========================================================
def render_documents() -> None:
    render_hero("Documents", "Download uploaded papers and delete them according to user permissions.")

    df = get_case_dataframe()
    if df.empty:
        st.info("No litigation cases available for document view.")
        render_footer()
        return

    case_map = {
        f"{r.get('case_ref', r['id'])} | {r.get('person_name', '')}": r["id"]
        for _, r in df.iterrows()
    }

    selected = st.selectbox("Select case", list(case_map.keys()))
    case_id = case_map[selected]

    file = st.file_uploader("Upload attachment", key="documents_upload_page")
    if file is not None and st.button("Upload Document", use_container_width=True):
        ok, msg = upload_supporting_document(case_id, file)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    docs = fetch_table("documents", {"case_id": case_id})
    if docs.empty:
        st.info("No documents uploaded for this case.")
    else:
        docs = docs.copy()
        docs["download_link"] = docs["storage_path"].apply(get_download_link_from_storage)

        for _, doc in docs.iterrows():
            st.markdown(f"### {doc.get('file_name')}")
            c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
            c1.write(f"Uploaded by: {doc.get('uploaded_by')}")
            c2.write(f"Size: {doc.get('file_size')}")
            if doc.get("download_link"):
                c3.markdown(f"[Download File]({doc.get('download_link')})")
            else:
                c3.write("Download link unavailable")

            if can_delete_document(doc.to_dict()):
                if c4.button("Delete File", key=f"documents_page_delete_{doc.get('id')}"):
                    ok, msg = delete_document(doc.to_dict())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    render_footer()


# =========================================================
# ADMIN
# =========================================================
def render_admin() -> None:
    if not is_admin():
        st.warning("Admin access only.")
        render_footer()
        return

    render_hero("Admin Control", "Manage employee master and audit visibility.")

    tab1, tab2 = st.tabs(["Employees", "Audit Logs"])

    with tab1:
        emp_df = fetch_table("employees")
        st.dataframe(emp_df, use_container_width=True, hide_index=True)

    with tab2:
        audit_df = fetch_table("audit_logs")
        if audit_df.empty:
            st.info("No audit logs found.")
        else:
            st.dataframe(audit_df, use_container_width=True, hide_index=True)

    render_footer()


# =========================================================
# PROFILE
# =========================================================
def render_profile() -> None:
    render_hero("Profile", "View your logged-in account details.")
    st.write(
        {
            "employee_id": st.session_state.get("employee_id"),
            "employee_name": st.session_state.get("employee_name"),
            "division": st.session_state.get("division"),
            "email": st.session_state.get("email"),
            "role": st.session_state.get("role"),
        }
    )
    render_footer()


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    if not is_authenticated():
        render_login_page()
        return

    page = render_sidebar()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Litigation":
        render_litigation()
    elif page == "Documents":
        render_documents()
    elif page == "Admin":
        render_admin()
    else:
        render_profile()


if __name__ == "__main__":
    main()