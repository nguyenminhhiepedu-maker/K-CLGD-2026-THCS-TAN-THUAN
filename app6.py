import streamlit as st
import pandas as pd
import os
from groq import Groq
import requests
from pypdf import PdfReader
from io import BytesIO

# ==========================================
# 1. CONFIG
# ==========================================
st.set_page_config(page_title="Kiểm định Tân Thuận", layout="wide")

# ==========================================
# 2. API KEY (LOCAL + CLOUD)
# ==========================================
def get_api_key():
    # ưu tiên Streamlit Cloud
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        pass

    # local
    return os.getenv("GROQ_API_KEY")

API_KEY = get_api_key()

client = None
if API_KEY:
    try:
        client = Groq(api_key=API_KEY)
    except:
        client = None

# ==========================================
# 3. CSS
# ==========================================
st.markdown("""
<style>
iframe { border-radius: 10px; border: 1px solid #ddd; }
h3 { color: #1E3A8A; font-weight: bold; }
.stInfo { background-color:#f0f7ff; border-left:5px solid #1E3A8A;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. LOAD EXCEL
# ==========================================
@st.cache_data
def load_data():
    file = "danh_muc_mc.xlsx"
    if os.path.exists(file):
        try:
            return pd.read_excel(file)
        except Exception as e:
            st.error(f"Lỗi đọc Excel: {e}")
    return None

df = load_data()

# ==========================================
# 5. READ PDF
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

        return text[:4000]
    except:
        return ""

# ==========================================
# 6. SIDEBAR AI
# ==========================================
with st.sidebar:

    st.title("📂 QUẢN LÝ KIỂM ĐỊNH")
    st.info("Trường THCS Tân Thuận")

    st.write("---")
    st.subheader("💬 TRỢ LÝ AI")

    if not API_KEY:
        st.error("❌ Chưa cấu hình GROQ_API_KEY")

    question = st.text_input("Thầy cô cần hỏi gì?")

    if question:

        if client is None:
            st.error("❌ AI chưa sẵn sàng")
        else:
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
MINH CHỨNG:
{context_excel}

BÁO CÁO:
{pdf_text}
"""

                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {
                                "role": "system",
                                "content": f"""
Bạn là trợ lý kiểm định.

CHỈ dùng dữ liệu dưới đây:
{context}

QUY TẮC:
- Không suy diễn
- Không dùng kiến thức ngoài
- Không có dữ liệu → trả lời: "Không tìm thấy trong dữ liệu nhà trường"
"""
                            },
                            {
                                "role": "user",
                                "content": question
                            }
                        ]
                    )

                    st.info(response.choices[0].message.content)

                except Exception as e:
                    st.error("❌ Lỗi AI")

# ==========================================
# 7. LAYOUT
# ==========================================
col1, col2 = st.columns(2)

# ==========================================
# 8. BÁO CÁO
# ==========================================
with col1:

    st.markdown("### 📄 BÁO CÁO TỰ ĐÁNH GIÁ")

    REPORT_IDS = {
        "Toàn bộ báo cáo": "15EKSMmyDCK94t_ID0pHfdHrDjTIqKNUx",
        "Tiêu chuẩn 1": "1PGLhrKUl9swE2TiKM__xIBl2ZzLeZ1K-",
        "Tiêu chuẩn 2": "1RutTLEKikugDnb5kq0c77IOtYYdBXlId"
    }

    sel = st.selectbox("Chọn báo cáo:", list(REPORT_IDS.keys()))
    file_id = REPORT_IDS[sel]

    url = f"https://drive.google.com/file/d/{file_id}/preview"
    st.components.v1.iframe(url, height=800)

# ==========================================
# 9. MINH CHỨNG
# ==========================================
with col2:

    st.markdown("### 🖼️ NỘI DUNG MINH CHỨNG")

    if df is not None:
        try:
            codes = df["MaMC"].dropna().unique().tolist()
            selected = st.selectbox("Chọn mã:", codes)

            row = df[df["MaMC"] == selected].iloc[0]
            link = str(row["LinkDrive"])

            if "/view" in link:
                link = link.replace("/view", "/preview").split("?")[0]

            st.components.v1.iframe(link, height=800)

        except Exception as e:
            st.error(f"Lỗi minh chứng: {e}")
    else:
        st.warning("Chưa có file Excel")
