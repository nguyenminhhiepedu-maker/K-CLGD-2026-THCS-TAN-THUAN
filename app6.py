import streamlit as st
import pandas as pd
import os
import requests
from pypdf import PdfReader
from io import BytesIO

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="Kiểm định Tân Thuận", layout="wide")

# ==========================================
# API KEY (HuggingFace)
# ==========================================
def get_api_key():
    try:
        return st.secrets["HF_API_KEY"]
    except:
        return os.getenv("HF_API_KEY")

HF_API_KEY = get_api_key()

# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>
iframe { border-radius: 10px; border: 1px solid #ddd; }
h3 { color: #1E3A8A; font-weight: bold; }
.stInfo { background-color:#f0f7ff; border-left:5px solid #1E3A8A;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD EXCEL
# ==========================================
@st.cache_data
def load_data():
    file = "danh_muc_mc.xlsx"
    if os.path.exists(file):
        return pd.read_excel(file)
    return None

df = load_data()

# ==========================================
# READ PDF
# ==========================================
def read_pdf_from_drive(file_id):
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        res = requests.get(url, timeout=10)

        pdf = PdfReader(BytesIO(res.content))

        text = ""
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                text += t

        return text[:3000]

    except:
        return ""

# ==========================================
# HUGGINGFACE CHATBOT
# ==========================================
def ask_huggingface(prompt):

    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 300}
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    try:
        return response.json()[0]["generated_text"]
    except:
        return "Không thể trả lời (lỗi AI)"

# ==========================================
# SIDEBAR AI
# ==========================================
with st.sidebar:

    st.title("📂 QUẢN LÝ KIỂM ĐỊNH")
    st.info("Trường THCS Tân Thuận")

    st.write("---")
    st.subheader("💬 TRỢ LÝ AI")

    if not HF_API_KEY:
        st.error("❌ Chưa cấu hình HF_API_KEY")

    question = st.text_input("Thầy cô cần hỏi gì?")

    if question and HF_API_KEY:

        with st.spinner("Đang xử lý..."):

            try:

                # ===== Excel =====
                context_excel = ""

                if df is not None:
                    for _, row in df.iterrows():
                        context_excel += f"{row.get('MaMC','')} - {row.get('LinkDrive','')}\n"

                # ===== PDF =====
                REPORT_ID = "15EKSMmyDCK94t_ID0pHfdHrDjTIqKNUx"

                pdf_text = read_pdf_from_drive(REPORT_ID)

                context = f"""
Dữ liệu minh chứng:
{context_excel}

Nội dung báo cáo:
{pdf_text}

Câu hỏi: {question}

Trả lời dựa trên dữ liệu trên.
Nếu không có thông tin, trả lời:
"Không tìm thấy trong dữ liệu nhà trường"
"""

                answer = ask_huggingface(context)

                st.info(answer)

            except:
                st.error("❌ Lỗi chatbot")

# ==========================================
# GIAO DIỆN
# ==========================================
col1, col2 = st.columns(2)

# ==========================================
# CỘT TRÁI: BÁO CÁO
# ==========================================
with col1:

    st.markdown("### 📄 BÁO CÁO TỰ ĐÁNH GIÁ")

    REPORT_IDS = {
        "Toàn bộ báo cáo": "15EKSMmyDCK94t_ID0pHfdHrDjTIqKNUx",
        "Tiêu chuẩn 1": "1PGLhrKUl9swE2TiKM__xIBl2ZzLeZ1K-",
        "Tiêu chuẩn 2": "1RutTLEKikugDnb5kq0c77IOtYYdBXlId"
    }

    sel = st.selectbox(
        "Chọn báo cáo:",
        list(REPORT_IDS.keys())
    )

    file_id = REPORT_IDS[sel]

    url = f"https://drive.google.com/file/d/{file_id}/preview"

    st.components.v1.iframe(url, height=800)

# ==========================================
# CỘT PHẢI: MINH CHỨNG
# ==========================================
with col2:

    st.markdown("### 🖼️ NỘI DUNG MINH CHỨNG")

    if df is not None:

        try:

            # =========================
            # TÌM THEO TIÊU CHÍ
            # =========================
            search_tc = st.text_input(
                "🔎 Nhập tiêu chí (ví dụ: 2.3)"
            )

            codes = df["MaMC"].dropna().astype(str).tolist()

            if search_tc:
                codes = [
                    c for c in codes
                    if search_tc in c
                ]

            if len(codes) == 0:

                st.warning("Không tìm thấy minh chứng")

            else:

                selected = st.selectbox(
                    "Chọn mã minh chứng:",
                    codes
                )

                row = df[
                    df["MaMC"] == selected
                ].iloc[0]

                link = str(row["LinkDrive"])

                if "/view" in link:
                    link = link.replace(
                        "/view",
                        "/preview"
                    ).split("?")[0]

                st.components.v1.iframe(
                    link,
                    height=800
                )

        except:
            st.error("Lỗi minh chứng")

    else:

        st.warning("Chưa có file Excel")
