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
        APP_VERSION=s.get("APP_VERSION", "4.3.0"),
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
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1450px; }
    header[data-testid="stHeader"] { background: rgba(255,255,255,0.72); }
    div[data-testid="stDecoration"] { display: none !important; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 45%, #c7d2fe 100%) !important;
        border-right: 1px solid rgba(59,130,246,0.20);
    }
    div[data-testid="stSidebar"] * { color: #1e3a8a !important; }
    div[data-testid="stSidebarNav"] { display: none; }
    .hero {
        border-radius: 28px; padding: 28px 32px; margin-bottom: 18px;
        background:
            radial-gradient(circle at 15% 18%, rgba(255,255,255,0.32), transparent 18%),
            linear-gradient(135deg, #2563eb 0%, #0ea5e9 42%, #8b5cf6 100%);
        box-shadow: 0 22px 60px rgba(37, 99, 235, 0.18);
        border: 1px solid rgba(255,255,255,0.30);
    }
    .hero h1 { margin: 0; color: white; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.03em; }
    .hero p { margin: 8px 0 0 0; color: rgba(255,255,255,0.95); font-size: 1rem; }
    .hero-badges { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }
    .badge {
        background: rgba(255,255,255,0.18); color: white; border: 1px solid rgba(255,255,255,0.28);
        padding: 8px 12px; border-radius: 999px; font-size: 0.84rem; font-weight: 700;
    }
    .panel, div[data-testid="stForm"], div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.92); border: 1px solid rgba(148,163,184,0.22);
        border-radius: 22px; box-shadow: 0 16px 40px rgba(15,23,42,0.08); backdrop-filter: blur(10px);
        color: #0f172a;
    }
    div[data-testid="stForm"] { padding: 1rem 1rem 0.65rem 1rem; }
    div[data-testid="stMetric"] { padding: 10px 14px; }
    .feature-card {
        min-height: 100%; border-radius: 24px; padding: 28px;
        background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,250,252,0.98));
        border: 1px solid rgba(148,163,184,0.22); box-shadow: 0 18px 44px rgba(15,23,42,0.08); color: #0f172a;
    }
    .feature-card h2 { color: #0f172a; margin: 0 0 10px 0; font-size: 1.55rem; }
    .feature-card p { color: #334155; }
    .feature-item {
        padding: 12px 14px; border-radius: 16px; background: #eff6ff; color: #1e3a8a;
        border: 1px solid #bfdbfe; font-size: 0.95rem; margin-top: 10px; font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 46px; background: #ffffff; border-radius: 999px; padding: 0 18px;
        color: #0f172a !important; font-weight: 700; border: 1px solid rgba(148,163,184,0.28);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff7a18, #ff4d6d 55%, #d946ef) !important;
        color: #ffffff !important; border: 1px solid rgba(255,255,255,0.22) !important;
        box-shadow: 0 14px 34px rgba(236,72,153,0.24) !important;
    }
    .stTextInput div div input, .stTextArea textarea, .stDateInput input, .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] div, .stMultiSelect div[data-baseweb="select"] div {
        background: #ffffff !important; color: #0f172a !important; border: 1px solid rgba(148,163,184,0.32) !important;
        border-radius: 14px !important;
    }
    .stButton button, .stDownloadButton button {
        border: 1px solid rgba(255,255,255,0.20) !important; color: #ffffff !important;
        background: linear-gradient(135deg, #ff7a18, #ff5a36 42%, #f43f5e 72%, #ec4899) !important;
        border-radius: 16px !important; padding: 0.78rem 1.15rem !important; font-weight: 800 !important;
        font-size: 0.98rem !important; box-shadow: 0 16px 40px rgba(244,63,94,0.24) !important;
        text-shadow: 0 1px 1px rgba(0,0,0,0.20);
    }
    .stButton button:hover, .stDownloadButton button:hover { filter: brightness(1.04); transform: translateY(-1px); }
    div[data-testid="stFileUploader"] section {
        background: #ffffff !important; border-radius: 18px !important; border: 1px solid rgba(148,163,184,0.28) !important;
    }
    .footer-note {
        text-align: center; color: #334155; font-size: 0.95rem; margin-top: 30px; padding-top: 14px;
        border-top: 1px solid rgba(148,163,184,0.30); font-weight: 600;
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

EMPLOYEE_COLUMNS = [
    "employee_id",
    "employee_name",
    "email",
    "division",
    "role",
    "is_active",
]

EMPLOYEE_DATE_FIELDS: list[str] = []

# =========================================================
# HELPERS
# =========================================================
def render_footer() -> None:
    st.markdown(
        '<div class="footer-note">This app developed by Raja Saha, '
        'Sr Manager Taxation, Balmer Lawrie &amp; Co Ltd</div>',
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


def normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "y", "active"):
        return True
    if text in ("false", "0", "no", "n", "inactive"):
        return False
    return default


def send_email(to_address: str, subject: str, html_body: str, cc_addresses: list[str] | None = None) -> bool:
    if not to_address or not settings.SMTP_USER or not settings.SMTP_APP_PASSWORD:
        return False
    try:
        recipients = [to_address]
        clean_cc = []
        if cc_addresses:
            clean_cc = [str(addr).strip() for addr in cc_addresses if addr and str(addr).strip()]
            for addr in clean_cc:
                if addr not in recipients:
                    recipients.append(addr)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"BL Indirect Tax Update <{settings.SMTP_USER}>"
        msg["Reply-To"] = "saha.r@balmerlawrie.com"
        msg["To"] = to_address
        if clean_cc:
            msg["Cc"] = ", ".join(clean_cc)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_USER, recipients, msg.as_string())
        return True
    except Exception:
        return False


def notify_admin(action_type: str, table_name: str, target_id: str, details: dict | None = None) -> None:
    actor_name = st.session_state.get("employee_name", "Unknown User")
    actor_id = st.session_state.get("employee_id", "Unknown ID")
    actor_email = st.session_state.get("email", "")
    admin_email = "saha.r@balmerlawrie.com"
    subject = "BL Indirect Tax Updates"

    action_title = sanitize(action_type).replace("_", " ").title()
    detail_rows = ""
    if details:
        detail_rows = "".join(
            f"""
            <tr>
                <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;width:38%;'>{sanitize(k).replace('_', ' ').title()}</td>
                <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(v)}</td>
            </tr>
            """
            for k, v in details.items()
        )
    else:
        detail_rows = """
        <tr>
            <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;'>Update</td>
            <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>A modification has been recorded successfully.</td>
        </tr>
        """

    html = f"""
    <div style="margin:0;padding:32px 18px;background:linear-gradient(135deg,#eff6ff 0%,#f8fafc 45%,#fff7ed 100%);font-family:Segoe UI,Arial,sans-serif;">
        <div style="max-width:780px;margin:0 auto;background:#ffffff;border-radius:24px;overflow:hidden;border:1px solid #dbeafe;box-shadow:0 20px 60px rgba(15,23,42,0.10);">
            <div style="padding:30px 34px;background:linear-gradient(135deg,#1d4ed8 0%,#0284c7 45%,#7c3aed 100%);color:#ffffff;">
                <div style="font-size:12px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;opacity:0.92;">Balmer Lawrie</div>
                <h1 style="margin:10px 0 8px 0;font-size:30px;line-height:1.2;font-weight:800;">BL Indirect Tax Updates</h1>
                <p style="margin:0;font-size:15px;line-height:1.7;opacity:0.96;">This is an automated notification for a completed change in the litigation management application.</p>
            </div>

            <div style="padding:30px 34px;">
                <div style="padding:20px 22px;border-radius:18px;background:linear-gradient(135deg,#eff6ff 0%,#fdf4ff 100%);border:1px solid #dbeafe;margin-bottom:22px;">
                    <div style="font-size:13px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;color:#64748b;">Modification Summary</div>
                    <div style="margin-top:8px;font-size:24px;font-weight:800;color:#0f172a;">{action_title}</div>
                    <div style="margin-top:8px;font-size:14px;color:#475569;line-height:1.7;">Only the necessary modification details are shown below.</div>
                </div>

                <table style="width:100%;border-collapse:separate;border-spacing:0;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;margin-bottom:22px;">
                    <tr>
                        <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;width:38%;'>Module</td>
                        <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(table_name).replace('_', ' ').title()}</td>
                    </tr>
                    <tr>
                        <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;'>Reference ID</td>
                        <td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(target_id)}</td>
                    </tr>
                    <tr>
                        <td style='padding:12px 16px;color:#334155;font-weight:700;background:#f8fafc;'>Updated By</td>
                        <td style='padding:12px 16px;color:#0f172a;background:#ffffff;'>{sanitize(actor_name)} ({sanitize(actor_id)})</td>
                    </tr>
                </table>

                <div style="font-size:17px;font-weight:800;color:#0f172a;margin:0 0 12px 0;">Modification Details</div>
                <table style="width:100%;border-collapse:separate;border-spacing:0;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;">{detail_rows}</table>

                <div style="margin-top:24px;padding:16px 18px;border-radius:16px;background:#fffaf0;border:1px solid #fde68a;color:#7c2d12;font-size:13px;line-height:1.7;">
                    This email is an automated update from the BL Indirect Tax application. It contains only the necessary information related to the recent modification.
                </div>
            </div>
        </div>
    </div>
    """

    cc_list = [actor_email] if actor_email and actor_email.lower() != admin_email.lower() else []
    send_email(admin_email, subject, html, cc_addresses=cc_list)


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
    for key in ["authenticated", "
