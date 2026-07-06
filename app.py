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
        ADMIN_EMAIL=s.get("ADMIN_EMAIL", "saha.r@balmerlawrie.com"),
        APP_VERSION=s.get("APP_VERSION", "4.3.0"),
    )


settings = get_settings()

st.set_page_config(page_title="Balmer Lawrie Litigation Tool", page_icon="⚖️", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg,#f8fbff 0%,#eef4ff 40%,#e7efff 100%);}
    .block-container {max-width: 1450px; padding-top: 1rem !important;}
    .hero {border-radius:24px;padding:24px 28px;margin-bottom:18px;background:linear-gradient(135deg,#2563eb 0%,#0ea5e9 42%,#8b5cf6 100%);color:white;}
    .footer-note {text-align:center;color:#334155;font-size:.95rem;margin-top:30px;padding-top:14px;border-top:1px solid rgba(148,163,184,.30);font-weight:600;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


sb = get_supabase()

LITIGATION_COLUMNS = [
    "division_name", "employee_id", "person_name", "tax_type", "disputed_demand",
    "financial_year", "disputed_forum", "last_hearing_date", "next_hearing_date",
    "current_status", "remarks",
]

EMPLOYEE_COLUMNS = ["employee_id", "employee_name", "email", "division", "role", "is_active"]


def render_footer() -> None:
    st.markdown('<div class="footer-note">This app developed by Raja Saha, Sr Manager Taxation, Balmer Lawrie &amp; Co Ltd</div>', unsafe_allow_html=True)


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
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


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
    detail_rows = "".join(
        f"<tr><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;width:38%;'>{sanitize(k).replace('_', ' ').title()}</td><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(v)}</td></tr>"
        for k, v in (details or {"update": "A modification has been recorded successfully."}).items()
    )
    html = f"""
    <div style='margin:0;padding:32px 18px;background:linear-gradient(135deg,#eff6ff 0%,#f8fafc 45%,#fff7ed 100%);font-family:Segoe UI,Arial,sans-serif;'>
      <div style='max-width:780px;margin:0 auto;background:#ffffff;border-radius:24px;overflow:hidden;border:1px solid #dbeafe;box-shadow:0 20px 60px rgba(15,23,42,0.10);'>
        <div style='padding:30px 34px;background:linear-gradient(135deg,#1d4ed8 0%,#0284c7 45%,#7c3aed 100%);color:#ffffff;'>
          <div style='font-size:12px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;opacity:0.92;'>Balmer Lawrie</div>
          <h1 style='margin:10px 0 8px 0;font-size:30px;line-height:1.2;font-weight:800;'>BL Indirect Tax Updates</h1>
          <p style='margin:0;font-size:15px;line-height:1.7;opacity:0.96;'>This is an automated notification for a completed change in the litigation management application.</p>
        </div>
        <div style='padding:30px 34px;'>
          <div style='padding:20px 22px;border-radius:18px;background:linear-gradient(135deg,#eff6ff 0%,#fdf4ff 100%);border:1px solid #dbeafe;margin-bottom:22px;'>
            <div style='font-size:13px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;color:#64748b;'>Modification Summary</div>
            <div style='margin-top:8px;font-size:24px;font-weight:800;color:#0f172a;'>{action_title}</div>
          </div>
          <table style='width:100%;border-collapse:separate;border-spacing:0;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;margin-bottom:22px;'>
            <tr><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;width:38%;'>Module</td><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(table_name).replace('_',' ').title()}</td></tr>
            <tr><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#334155;font-weight:700;background:#f8fafc;'>Reference ID</td><td style='padding:12px 16px;border-bottom:1px solid #e2e8f0;color:#0f172a;background:#ffffff;'>{sanitize(target_id)}</td></tr>
            <tr><td style='padding:12px 16px;color:#334155;font-weight:700;background:#f8fafc;'>Updated By</td><td style='padding:12px 16px;color:#0f172a;background:#ffffff;'>{sanitize(actor_name)} ({sanitize(actor_id)})</td></tr>
          </table>
          <div style='font-size:17px;font-weight:800;color:#0f172a;margin:0 0 12px 0;'>Modification Details</div>
          <table style='width:100%;border-collapse:separate;border-spacing:0;border:1px solid #e2e8f0;border-radius:18px;overflow:hidden;'>{detail_rows}</table>
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
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <p>Version {settings.APP_VERSION} | Role: {role} | User: {sanitize(emp)}</p>
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
                "details": details or {},
            }
        ).execute()
    except Exception:
        pass


def get_case_dataframe() -> pd.DataFrame:
    if is_admin():
        return fetch_table("litigation_master")
    return fetch_table("litigation_master", {"employee_id": st.session_state.get("employee_id")})


def upload_supporting_document(case_id: Any, file_obj) -> tuple[bool, str]:
    if file_obj is None:
        return False, "Please select a file."
    try:
        path = f"{case_id}/{uuid.uuid4().hex}_{file_obj.name}"
        file_bytes = file_obj.getvalue()
        sb.storage.from_(settings.SUPABASE_BUCKET).upload(path, file_bytes, {"content-type": file_obj.type or "application/octet-stream"})
        doc_payload = {
            "case_id": case_id,
            "uploaded_by": st.session_state.get("employee_id"),
            "file_name": file_obj.name,
            "storage_path": path,
            "file_size": len(file_bytes),
        }
        sb.table("documents").insert(doc_payload).execute()
        save_audit("upload_document", "documents", str(case_id), {"file_name": file_obj.name})
        notify_admin("upload_document", "documents", str(case_id), {"file_name": file_obj.name})
        return True, "Supporting paper uploaded successfully."
    except Exception as exc:
        return False, f"Upload failed: {exc}"


def get_download_link_from_storage(storage_path: str) -> str | None:
    try:
        res = sb.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(storage_path, 3600)
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signed_url")
        return None
    except Exception:
        return None


def can_delete_document(doc_row: dict) -> bool:
    if is_admin():
        return True
    return str(doc_row.get("uploaded_by")) == str(st.session_state.get("employee_id"))


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
        save_audit("delete_document", "documents", str(doc_id), {"file_name": doc_row.get("file_name")})
        notify_admin("delete_document", "documents", str(doc_id), {"file_name": doc_row.get("file_name")})
        return True, "Document deleted successfully."
    except Exception as exc:
        return False, f"Delete failed: {exc}"


def render_login_page() -> None:
    render_hero("Balmer Lawrie Latest Indirect Tax Litigation Updating Tool", "Secure document upload, download and deletion with role-based permissions.")
    tab1, tab2 = st.tabs(["Login", "Change Password"])
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
        with st.form("change_pw_form"):
            emp_id_ch = st.text_input("Employee ID ")
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
                        sb.table("employees").update({"password_hash": hash_password(new_pw)}).eq("employee_id", emp_id_ch.strip()).execute()
                        st.success("Password changed successfully.")
    render_footer()


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("### Litigation Console")
        st.caption(f"{st.session_state.get('employee_name')} ({st.session_state.get('employee_id')})")
        options = ["Dashboard", "Documents", "Profile"]
        choice = st.radio("Navigate", options)
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
    return choice


def render_dashboard() -> None:
    render_hero("Dashboard", "Live case portfolio overview.")
    df = get_case_dataframe()
    st.dataframe(df, use_container_width=True, hide_index=True)
    render_footer()


def render_documents() -> None:
    render_hero("Documents", "Upload additional attachments, download uploaded papers and delete them according to user permissions.")
    cases = get_case_dataframe()
    if cases.empty:
        st.info("No cases available.")
        render_footer()
        return

    cases = cases.copy()
    if "case_ref" not in cases.columns:
        cases["case_ref"] = cases.get("id", pd.Series(dtype=str)).astype(str)
    if "person_name" not in cases.columns:
        cases["person_name"] = ""

    case_options = {
        f"{row.get('case_ref')} | {row.get('person_name', '')}": row.get("id")
        for _, row in cases.iterrows()
    }
    selected_label = st.selectbox("Select case", list(case_options.keys()))
    selected_case_id = case_options[selected_label]

    uploaded_file = st.file_uploader("Upload attachment", type=None)
    if st.button("Upload Document", use_container_width=True):
        ok, msg = upload_supporting_document(selected_case_id, uploaded_file)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    docs_df = fetch_table("documents", {"case_id": selected_case_id})
    if docs_df.empty:
        st.info("No documents uploaded for this case.")
        render_footer()
        return

    docs_df = docs_df.sort_values(by="id", ascending=False) if "id" in docs_df.columns else docs_df
    for _, row in docs_df.iterrows():
        doc = row.to_dict()
        file_name = doc.get("file_name") or doc.get("filename") or "Unnamed file"
        uploaded_by = doc.get("uploaded_by", "Unknown")
        file_size = doc.get("file_size")
        size_text = f"{round((file_size or 0) / 1024 / 1024, 2)} MB" if file_size else "Size N/A"
        link = get_download_link_from_storage(doc.get("storage_path", ""))

        c1, c2, c3 = st.columns([5, 1.2, 1.2])
        with c1:
            st.markdown(f"**{sanitize(file_name)}**  ")
            st.caption(f"Uploaded by: {sanitize(uploaded_by)} | {size_text}")
        with c2:
            if link:
                st.markdown(f"[Download]({link})")
            else:
                st.caption("No link")
        with c3:
            if can_delete_document(doc):
                if st.button("Delete", key=f"del_{doc.get('id')}"):
                    ok, msg = delete_document(doc)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.caption("No delete access")
        st.markdown("---")
    render_footer()


def render_profile() -> None:
    render_hero("Profile", "Logged-in employee details.")
    st.write("Employee ID:", st.session_state.get("employee_id"))
    st.write("Employee Name:", st.session_state.get("employee_name"))
    st.write("Role:", st.session_state.get("role"))
    st.write("Division:", st.session_state.get("division"))
    st.write("Email:", st.session_state.get("email"))
    render_footer()


def main() -> None:
    if not is_authenticated():
        render_login_page()
        return
    page = render_sidebar()
    if page == "Dashboard":
        render_dashboard()
    elif page == "Documents":
        render_documents()
    else:
        render_profile()


if __name__ == "__main__":
    main()
