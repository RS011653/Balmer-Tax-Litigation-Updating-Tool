"""
Balmer Lawrie Latest Indirect Tax Litigation Updating Tool
Single-file Streamlit application - v2.0.0
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Any

import bcrypt
import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client, Client


# ---------------------------------------------------------------------------
# CONFIG / SETTINGS (from Streamlit secrets)
# ---------------------------------------------------------------------------

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
        SMTP_USER=s["SMTP_USER"],
        SMTP_APP_PASSWORD=s["SMTP_APP_PASSWORD"],
        ADMIN_EMAIL=s.get("ADMIN_EMAIL", "caraja.saha@gmail.com"),
        APP_VERSION=s.get("APP_VERSION", "2.0.0"),
    )


settings = get_settings()


# ---------------------------------------------------------------------------
# SUPABASE CLIENT
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


sb = get_supabase()


# ---------------------------------------------------------------------------
# SECURITY / AUTH UTILITIES
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def sanitize(text: Any) -> str:
    if text is None:
        return ""
    return str(text).replace("<", "").replace(">", "").strip()


def send_email(to_address: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via Gmail SMTP app password. Never crashes the app."""
    if not to_address:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = "BL Indirect Tax Updates"
        msg["To"] = to_address
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_APP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_address], msg.as_string())
        return True
    except Exception as exc:
        st.warning(f"Email send failed to {to_address}: {exc}")
        return False


def login(employee_id: str, password: str) -> tuple[bool, str]:
    if not employee_id:
        return False, "Please enter Employee ID."
    res = sb.table("employees").select("*").eq("employee_id", employee_id).execute()
    if not res.data:
        return False, "Employee ID not found."

    user = res.data[0]
    if not user.get("is_active", True):
        return False, "Account is deactivated. Contact administrator."
    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    st.session_state["authenticated"] = True
    st.session_state["employee_id"] = user["employee_id"]
    st.session_state["employee_name"] = user["employee_name"]
    st.session_state["role"] = user["role"]
    st.session_state["division"] = user.get("division")
    st.session_state["email"] = user.get("email")
    return True, "Login successful."


def logout() -> None:
    for key in ("authenticated", "employee_id", "employee_name", "role", "division", "email"):
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


# ---------------------------------------------------------------------------
# PAGE CONFIG & THEME (colorful, no blank banner)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Balmer Lawrie Latest Indirect Tax Litigation Updating Tool",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; height: 0; }
    div[data-testid="stDecoration"] { display: none; }
    .block-container { padding-top: 1.2rem; }

    .gradient-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 45%, #7e22ce 100%);
        padding: 22px 26px; border-radius: 14px; color: white; margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }
    .gradient-header h1 { margin: 0; font-size: 24px; font-weight: 700; }
    .gradient-header p { margin: 4px 0 0 0; opacity: 0.9; font-size: 14px; }

    .metric-card {
        border-radius: 12px; padding: 16px 18px; margin-bottom: 10px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.14); color: white;
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-icon { font-size: 20px; margin-bottom: 4px; }
    .metric-value { font-size: 22px; font-weight: 800; }
    .metric-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; opacity: 0.92; }

    .card-orange { background: linear-gradient(135deg, #f97316, #fb7185); }
    .card-teal   { background: linear-gradient(135deg, #0891b2, #22d3ee); }
    .card-purple { background: linear-gradient(135deg, #7c3aed, #a855f7); }
    .card-green  { background: linear-gradient(135deg, #16a34a, #4ade80); }
    .card-pink   { background: linear-gradient(135deg, #db2777, #f472b6); }
    .card-blue   { background: linear-gradient(135deg, #1d4ed8, #3b82f6); }

    .app-footer {
        text-align: center; padding: 12px; margin-top: 30px; color: #64748b;
        font-size: 12px; border-top: 1px solid #e2e8f0;
    }

    .login-card {
        max-width: 420px; margin: 40px auto; padding: 36px; border-radius: 16px;
        background: white; box-shadow: 0 12px 32px rgba(0,0,0,0.18);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

CARD_COLORS = ["card-orange", "card-teal", "card-purple", "card-green", "card-pink", "card-blue"]


def render_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="gradient-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, icon: str, color_cls: str) -> None:
    st.markdown(
        f'<div class="metric-card {color_cls}">'
        f'<div class="metric-icon">{icon}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f'<div class="app-footer">Version {settings.APP_VERSION} | '
        f'Developed by Raja Saha, Sr Manager (Taxation), Balmer Lawrie &amp; Co Ltd.</div>',
        unsafe_allow_html=True,
    )


def notify_admin_of_user_change(actor_name: str, actor_id: str, subject: str, details_html: str) -> None:
    """Send email to the acting user and to admin whenever a NON-ADMIN makes a change."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = (
        f"<h3>{subject}</h3>"
        f"<p>Changed by: {actor_name} ({actor_id})</p>"
        f"<p>Time: {ts}</p>"
        f"{details_html}"
    )
    user_email = st.session_state.get("email")
    if user_email:
        send_email(user_email, subject, html)
    send_email(settings.ADMIN_EMAIL, subject, html)


# ---------------------------------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------------------------------

def render_login_page() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### ⚖️ Balmer Lawrie Latest Indirect Tax Litigation Updating Tool")
        st.caption("Secure access for authorized Balmer Lawrie personnel only.")

        tab_login, tab_forgot, tab_change = st.tabs(["Login", "Forgot Password", "Change Password"])

        with tab_login:
            with st.form("login_form"):
                emp_id = st.text_input("Employee ID")
                pwd = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                ok, msg = login(emp_id.strip(), pwd)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with tab_forgot:
            st.write("If you forget your password, it will be reset to your registered Email ID.")
            with st.form("forgot_form"):
                emp_id_fp = st.text_input("Employee ID", key="fp_id")
                submitted_fp = st.form_submit_button("Reset to Email ID", use_container_width=True)
            if submitted_fp:
                res = sb.table("employees").select("*").eq("employee_id", emp_id_fp.strip()).execute()
                if not res.data:
                    st.error("Employee ID not found.")
                else:
                    user = res.data[0]
                    email = user["email"]
                    new_hash = hash_password(email)
                    sb.table("employees").update({"password_hash": new_hash}).eq(
                        "employee_id", emp_id_fp.strip()
                    ).execute()
                    body = (
                        f"<p>Dear {user['employee_name']},</p>"
                        f"<p>Your password has been reset. Your new password is your registered Email ID:</p>"
                        f"<p><b>{email}</b></p>"
                        f"<p>Please login and change it from the Change Password tab.</p>"
                    )
                    send_email(email, "Password Reset to Email ID", body)
                    send_email(settings.ADMIN_EMAIL, "User Password Reset", body)
                    st.success("Password reset to Email ID and emailed to you & admin.")

        with tab_change:
            with st.form("change_pw_form"):
                emp_id_ch = st.text_input("Employee ID (for verification)")
                old_pw = st.text_input("Old Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                submitted_ch = st.form_submit_button("Change Password", use_container_width=True)
            if submitted_ch:
                res = sb.table("employees").select("*").eq("employee_id", emp_id_ch.strip()).execute()
                if not res.data:
                    st.error("Employee ID not found.")
                else:
                    user = res.data[0]
                    if not verify_password(old_pw, user["password_hash"]):
                        st.error("Old password incorrect.")
                    else:
                        new_hash = hash_password(new_pw)
                        sb.table("employees").update({"password_hash": new_hash}).eq(
                            "employee_id", emp_id_ch.strip()
                        ).execute()
                        body = (
                            f"<p>Dear {user['employee_name']},</p>"
                            f"<p>Your password has been changed successfully.</p>"
                            f"<p>New password: <b>{new_pw}</b></p>"
                        )
                        send_email(user["email"], "Password Changed", body)
                        send_email(settings.ADMIN_EMAIL, "User Password Changed", body)
                        st.success("Password changed and emailed to you & admin.")

        st.markdown("</div>", unsafe_allow_html=True)

    render_footer()


# ---------------------------------------------------------------------------
# SIDEBAR (only after login)
# ---------------------------------------------------------------------------

def render_sidebar() -> str:
    st.sidebar.markdown("### ⚖️ Litigation Tool")
    st.sidebar.markdown(
        f"**{st.session_state.get('employee_name', '')}**  \n"
        f"ID: {st.session_state.get('employee_id', '')}  \n"
        f"Role: {st.session_state.get('role', '').title()}"
    )
    st.sidebar.divider()
    pages = ["Dashboard", "Litigation Table"]
    if is_admin():
        pages.append("Employee Master")
    page = st.sidebar.radio("Navigate", pages, label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
        st.rerun()
    return page


# ---------------------------------------------------------------------------
# DATA HELPERS
# ---------------------------------------------------------------------------

def fetch_litigation_df() -> pd.DataFrame:
    res = sb.table("litigation_master").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty and not is_admin():
        emp_id = st.session_state.get("employee_id")
        df = df[df["employee_id"].astype(str) == str(emp_id)]
    return df


# ---------------------------------------------------------------------------
# DASHBOARD - Tax-type wise summary (number of cases + disputed demand)
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    render_header("📊 Litigation Dashboard", "Tax type-wise summary of ongoing litigation")

    df = fetch_litigation_df()
    if df.empty:
        st.info("No litigation records available for your view.")
        return

    df["disputed_demand"] = pd.to_numeric(df.get("disputed_demand", 0), errors="coerce").fillna(0)

    total_cases = len(df)
    total_demand = df["disputed_demand"].sum()
    pending_cases = len(df[df["current_status"].astype(str).str.lower().isin(["pending", "in progress"])])

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Total Cases", str(total_cases), "📁", "card-blue")
    with c2:
        metric_card("Pending / In Progress", str(pending_cases), "⏳", "card-orange")
    with c3:
        metric_card("Total Disputed Demand (Rs.)", f"{total_demand:,.0f}", "💰", "card-purple")

    st.divider()
    st.subheader("Tax Type-wise Summary")

    summary = df.groupby("tax_type").agg(
        Number_of_Cases=("case_ref", "count") if "case_ref" in df.columns else ("tax_type", "count"),
        Disputed_Demand=("disputed_demand", "sum"),
    ).reset_index().rename(columns={"tax_type": "Tax Type"})

    cols = st.columns(min(4, max(1, len(summary))))
    for i, row in summary.iterrows():
        with cols[i % len(cols)]:
            metric_card(
                f"{row['Tax Type']} — Cases",
                str(int(row["Number_of_Cases"])),
                "⚖️",
                CARD_COLORS[i % len(CARD_COLORS)],
            )

    fig1 = px.bar(
        summary, x="Tax Type", y="Number_of_Cases", color="Tax Type",
        color_discrete_sequence=px.colors.qualitative.Bold,
        title="Number of Cases by Tax Type",
    )
    fig2 = px.bar(
        summary, x="Tax Type", y="Disputed_Demand", color="Tax Type",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        title="Disputed Demand by Tax Type (Rs.)",
    )
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Summary Table")
    st.dataframe(summary, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# LITIGATION TABLE - View + Full Edit + Attach/Delete Documents + Admin Delete Case
# ---------------------------------------------------------------------------

def get_case_documents(case_id: int) -> pd.DataFrame:
    res = sb.table("documents").select("*").eq("case_id", case_id).execute()
    return pd.DataFrame(res.data)


def render_litigation_table() -> None:
    render_header("📋 Litigation Table", "View, edit, attach documents to your litigation records")

    df = fetch_litigation_df()
    if df.empty:
        st.info("No litigation records found for your account.")
    else:
        search = st.text_input("🔍 Search", placeholder="Search by person, forum, case ref, status, remarks...")
        view_df = df.copy()
        if search:
            mask = view_df.astype(str).apply(
                lambda r: r.str.contains(search, case=False, na=False)
            ).any(axis=1)
            view_df = view_df[mask]

        display_cols = [
            "case_ref", "employee_id", "division_name", "person_name", "tax_type",
            "disputed_demand", "financial_year", "disputed_forum",
            "last_hearing_date", "next_hearing_date", "current_status", "remarks",
        ]
        display_cols = [c for c in display_cols if c in view_df.columns]
        st.dataframe(view_df[display_cols], use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Edit Case / Attach Document")

        case_map = {
            f"{r.get('case_ref', r.get('id'))} — {r.get('person_name', '')}": r
            for _, r in df.iterrows()
        }
        selected_label = st.selectbox("Select Case", list(case_map.keys()))
        selected = case_map[selected_label]

        status_options = ["Pending", "In Progress", "Closed", "Appealed"]
        cur_status = selected.get("current_status", "Pending")
        status_idx = status_options.index(cur_status) if cur_status in status_options else 0

        with st.form("edit_case_form"):
            ec1, ec2 = st.columns(2)
            with ec1:
                new_division = st.text_input("Division Name", value=selected.get("division_name") or "")
                new_person = st.text_input("Person Name", value=selected.get("person_name") or "")
                new_tax_type = st.text_input("Tax Type", value=selected.get("tax_type") or "")
                new_fy = st.text_input("Financial Year", value=selected.get("financial_year") or "")
                new_forum = st.text_input("Disputed Forum", value=selected.get("disputed_forum") or "")
            with ec2:
                new_demand = st.number_input(
                    "Disputed Demand (Rs.)", min_value=0.0,
                    value=float(selected.get("disputed_demand") or 0), step=1000.0,
                )
                new_last = st.date_input("Last Hearing Date")
                new_next = st.date_input("Next Hearing Date")
                new_status = st.selectbox("Current Status", status_options, index=status_idx)
                new_remarks = st.text_area("Remarks", value=selected.get("remarks") or "")

            attachment = st.file_uploader(
                "Attach Supporting Document (any user can attach)",
                type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx"],
            )
            submitted = st.form_submit_button("Save Changes", use_container_width=True)

        if submitted:
            old_values = {k: selected.get(k) for k in [
                "division_name", "person_name", "tax_type", "financial_year",
                "disputed_forum", "disputed_demand", "last_hearing_date",
                "next_hearing_date", "current_status", "remarks",
            ]}
            new_values = {
                "division_name": sanitize(new_division),
                "person_name": sanitize(new_person),
                "tax_type": sanitize(new_tax_type),
                "financial_year": sanitize(new_fy),
                "disputed_forum": sanitize(new_forum),
                "disputed_demand": new_demand,
                "last_hearing_date": str(new_last) if new_last else None,
                "next_hearing_date": str(new_next) if new_next else None,
                "current_status": new_status,
                "remarks": sanitize(new_remarks),
            }
            sb.table("litigation_master").update(new_values).eq("id", selected["id"]).execute()

            if attachment is not None:
                path = f"{selected.get('case_ref', selected['id'])}/{uuid.uuid4().hex}_{attachment.name}"
                sb.storage.from_(settings.SUPABASE_BUCKET).upload(
                    path, attachment.getvalue(),
                    {"content-type": attachment.type or "application/octet-stream"},
                )
                sb.table("documents").insert({
                    "case_id": selected["id"],
                    "uploaded_by": st.session_state.get("employee_id"),
                    "file_name": attachment.name,
                    "storage_path": path,
                    "file_size": attachment.size,
                }).execute()

            rows_html = "".join(
                f"<tr><td>{k}</td><td>{old_values.get(k)}</td><td>{new_values.get(k)}</td></tr>"
                for k in new_values.keys()
            )
            details_html = (
                f"<p>Case: <b>{selected.get('case_ref', selected['id'])}</b></p>"
                f"<table border='1' cellpadding='6' cellspacing='0'>"
                f"<tr><th>Field</th><th>Old Value</th><th>New Value</th></tr>{rows_html}</table>"
            )

            if not is_admin():
                notify_admin_of_user_change(
                    st.session_state.get("employee_name"),
                    st.session_state.get("employee_id"),
                    f"Litigation Updated: {selected.get('case_ref', selected['id'])}",
                    details_html,
                )
            else:
                send_email(
                    settings.ADMIN_EMAIL,
                    f"[Admin Edit] Litigation Updated: {selected.get('case_ref', selected['id'])}",
                    details_html,
                )

            st.success("Case updated successfully.")
            st.rerun()

        # --- Attachments list + admin-only delete ---
        st.divider()
        st.subheader("Attachments")
        docs_df = get_case_documents(selected["id"])
        if docs_df.empty:
            st.caption("No documents attached to this case yet.")
        else:
            for _, doc in docs_df.iterrows():
                dcol1, dcol2, dcol3 = st.columns([4, 2, 1])
                with dcol1:
                    st.write(f"📎 {doc['file_name']}")
                with dcol2:
                    try:
                        signed = sb.storage.from_(settings.SUPABASE_BUCKET).create_signed_url(
                            doc["storage_path"], 3600
                        )
                        url = signed.get("signedURL") or signed.get("signedUrl")
                        if url:
                            st.markdown(f"[Download]({url})")
                    except Exception:
                        st.caption("Preview unavailable")
                with dcol3:
                    if is_admin():
                        if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}"):
                            sb.storage.from_(settings.SUPABASE_BUCKET).remove([doc["storage_path"]])
                            sb.table("documents").delete().eq("id", doc["id"]).execute()
                            st.success("Attachment deleted.")
                            st.rerun()

        # --- Admin-only: delete entire litigation case ---
        if is_admin():
            st.divider()
            st.subheader("⚠️ Admin: Delete This Litigation Case")
            confirm = st.checkbox(f"I confirm deletion of case {selected.get('case_ref', selected['id'])}", key="confirm_del_case")
            if st.button("Delete Case Permanently", type="primary", disabled=not confirm):
                sb.table("documents").delete().eq("case_id", selected["id"]).execute()
                sb.table("litigation_master").delete().eq("id", selected["id"]).execute()
                st.success("Litigation case deleted.")
                st.rerun()

    # --- Admin: bulk import litigation from Excel (with Employee ID mapping) ---
    if is_admin():
        st.divider()
        st.subheader("Admin: Bulk Import Litigation from Excel")
        st.caption("Excel columns: division_name, Employee ID, person_name, tax_type, disputed_demand, "
                   "financial_year, disputed_forum, last_hearing_date, next_hearing_date, current_status, remarks")
        uploaded = st.file_uploader("Upload Litigation Excel", type=["xlsx"], key="lit_bulk")
        if uploaded and st.button("Import Records", use_container_width=True):
            try:
                idf = pd.read_excel(uploaded)
                count = 0
                for _, row in idf.iterrows():
                    payload = {
                        "case_ref": str(row.get("case_ref") or f"CASE-{uuid.uuid4().hex[:8].upper()}"),
                        "employee_id": str(row.get("Employee ID", "")).strip(),
                        "division_name": str(row.get("division_name", "")),
                        "person_name": str(row.get("person_name", "")),
                        "tax_type": str(row.get("tax_type", "")),
                        "disputed_demand": pd.to_numeric(row.get("disputed_demand", 0), errors="coerce") or 0,
                        "financial_year": str(row.get("financial_year", "")),
                        "disputed_forum": str(row.get("disputed_forum", "")),
                        "last_hearing_date": str(row.get("last_hearing_date")) if pd.notna(row.get("last_hearing_date")) else None,
                        "next_hearing_date": str(row.get("next_hearing_date")) if pd.notna(row.get("next_hearing_date")) else None,
                        "current_status": str(row.get("current_status", "Pending")),
                        "remarks": str(row.get("remarks", "")),
                    }
                    sb.table("litigation_master").insert(payload).execute()
                    count += 1
                st.success(f"Imported {count} litigation records successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Import failed: {exc}")


# ---------------------------------------------------------------------------
# EMPLOYEE MASTER - Admin: add / modify / delete / bulk upload
# ---------------------------------------------------------------------------

def render_employee_master() -> None:
    render_header("👥 Employee Master", "Admin: manage user access to the tool")

    if not is_admin():
        st.error("Admin only.")
        return

    res = sb.table("employees").select("*").execute()
    df = pd.DataFrame(res.data)

    st.subheader("Current Employees")
    if not df.empty:
        cols = [c for c in ["employee_id", "employee_name", "email", "division", "role", "is_active"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No employees yet.")

    st.divider()
    st.subheader("➕ Add New Employee")
    with st.form("add_employee_form"):
        a1, a2 = st.columns(2)
        with a1:
            new_id = st.text_input("Employee ID")
            new_name = st.text_input("Employee Name")
            new_email = st.text_input("Email ID")
        with a2:
            new_division = st.text_input("Division")
            new_role = st.selectbox("Role", ["user", "admin"])
            new_active = st.checkbox("Active", value=True)
        add_submit = st.form_submit_button("Add Employee", use_container_width=True)

    if add_submit:
        if not new_id or not new_name or not new_email:
            st.error("Employee ID, Name and Email are required.")
        else:
            pw_hash = hash_password(new_id)
            sb.table("employees").insert({
                "employee_id": new_id.strip(),
                "employee_name": new_name.strip(),
                "email": new_email.strip(),
                "division": new_division.strip(),
                "role": new_role,
                "password_hash": pw_hash,
                "is_active": new_active,
            }).execute()
            body = (
                f"<p>Dear {new_name},</p>"
                f"<p>Your account has been created for the Balmer Lawrie Litigation Tool.</p>"
                f"<p>Default User ID: <b>{new_id}</b><br>Default Password: <b>{new_id}</b></p>"
            )
            send_email(new_email, "Litigation Tool Account Created", body)
            st.success(f"Employee {new_id} added and notified by email.")
            st.rerun()

    st.divider()
    st.subheader("✏️ Modify / 🗑️ Delete Employee")
    if not df.empty:
        emp_options = {f"{r['employee_id']} — {r['employee_name']}": r for _, r in df.iterrows()}
        sel_label = st.selectbox("Select Employee", list(emp_options.keys()))
        emp = emp_options[sel_label]

        with st.form("modify_employee_form"):
            m1, m2 = st.columns(2)
            with m1:
                mod_name = st.text_input("Employee Name", value=emp.get("employee_name") or "")
                mod_email = st.text_input("Email ID", value=emp.get("email") or "")
            with m2:
                mod_division = st.text_input("Division", value=emp.get("division") or "")
                mod_role = st.selectbox("Role", ["user", "admin"], index=0 if emp.get("role") == "user" else 1)
                mod_active = st.checkbox("Active", value=bool(emp.get("is_active", True)))
            mod_submit = st.form_submit_button("Save Changes", use_container_width=True)

        if mod_submit:
            sb.table("employees").update({
                "employee_name": mod_name.strip(),
                "email": mod_email.strip(),
                "division": mod_division.strip(),
                "role": mod_role,
                "is_active": mod_active,
            }).eq("employee_id", emp["employee_id"]).execute()
            st.success("Employee details updated.")
            st.rerun()

        st.markdown("###")
        confirm_del = st.checkbox(f"I confirm deletion of employee {emp['employee_id']}", key="confirm_del_emp")
        if st.button("Delete Employee Permanently", type="primary", disabled=not confirm_del):
            sb.table("employees").delete().eq("employee_id", emp["employee_id"]).execute()
            st.success("Employee deleted.")
            st.rerun()

    st.divider()
    st.subheader("📥 Bulk Upload Employees from Excel")
    st.caption("Excel columns required: Employee ID, Employee Name, Email ID, Division (optional)")
    uploaded = st.file_uploader("Upload Employee Master Excel", type=["xlsx"])
    if uploaded and st.button("Import Employees", use_container_width=True):
        try:
            idf = pd.read_excel(uploaded)
            count = 0
            for _, row in idf.iterrows():
                emp_id = str(row["Employee ID"]).strip()
                name = str(row["Employee Name"]).strip()
                email = str(row["Email ID"]).strip()
                division = str(row.get("Division", "")).strip()

                pw_hash = hash_password(emp_id)
                sb.table("employees").insert({
                    "employee_id": emp_id,
                    "employee_name": name,
                    "email": email,
                    "division": division,
                    "role": "user",
                    "password_hash": pw_hash,
                    "is_active": True,
                }).execute()

                body = (
                    f"<p>Dear {name},</p>"
                    f"<p>Your account has been created for the Balmer Lawrie Litigation Tool.</p>"
                    f"<p>Default User ID: <b>{emp_id}</b><br>Default Password: <b>{emp_id}</b></p>"
                )
                send_email(email, "Litigation Tool Account Created", body)
                count += 1
            st.success(f"Imported {count} employees and notified by email.")
            st.rerun()
        except Exception as exc:
            st.error(f"Employee import failed: {exc}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    if not is_authenticated():
        render_login_page()
        return

    page = render_sidebar()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Litigation Table":
        render_litigation_table()
    elif page == "Employee Master":
        render_employee_master()

    render_footer()


if __name__ == "__main__":
    main()
