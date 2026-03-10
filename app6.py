import streamlit as st
import pandas as pd
import os

# 1. Cấu hình trang rộng
st.set_page_config(page_title="Hệ thống Trợ lý Kiểm định - THCS Tân Thuận", layout="wide", initial_sidebar_state="expanded")

# 2. CSS Tối ưu cơ bản
st.markdown("""
    <style>
    iframe { border-radius: 8px; background-color: white; border: 1px solid #eee; }
    .stSelectbox { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Đọc dữ liệu Excel
@st.cache_data
def load_data():
    file_path = "danh_muc_mc.xlsx"
    if os.path.exists(file_path):
        try:
            return pd.read_excel(file_path)
        except:
            return None
    return None

df = load_data()

# Khởi tạo bộ nhớ (Session State)
if "report_option" not in st.session_state:
    st.session_state.report_option = "Toàn bộ báo cáo tự đánh giá"
if "selected_mc_index" not in st.session_state:
    st.session_state.selected_mc_index = 0

# --- CỘT 1: SIDEBAR (TRỢ LÝ AI) ---
with st.sidebar:
    st.title("📂 CHƯƠNG TRÌNH HỖ TRỢ KIỂM ĐỊNH CHẤT LƯỢNG GIÁO DỤC - TRƯỜNG THCS TÂN THUẬN")
    st.write("---")
    st.subheader("💬 TRỢ LÝ AI - TRƯỜNG THCS TÂN THUẬN")
    # Link NotebookLM của bạn
    URL_NOTEBOOK_LM = "https://notebooklm.google.com/notebook/YOUR_NOTEBOOK_ID" 
    st.components.v1.iframe(URL_NOTEBOOK_LM, height=500, scrolling=True)

# --- CHIA 2 CỘT CÂN BẰNG 1:1 ---
col_left, col_right = st.columns([1, 1])

# --- CỬA SỔ TRÁI: BÁO CÁO TỰ ĐÁNH GIÁ ---
with col_left:
    st.subheader("📄 Báo cáo tự đánh giá")
    options_report = ["Toàn bộ báo cáo tự đánh giá", "Tiêu chuẩn 1", "Tiêu chuẩn 2", "Tiêu chuẩn 3", "Tiêu chuẩn 4", "Tiêu chuẩn 5"]
    
    # Đồng bộ với bộ nhớ để không nhảy trang
    cur_report_idx = options_report.index(st.session_state.report_option)
    sel_report = st.selectbox("Mời thầy cô chọn nội dung báo cáo cần xem:", options_report, index=cur_report_idx)
    st.session_state.report_option = sel_report
    
    REPORT_IDS = {
        "Toàn bộ báo cáo tự đánh giá": "15EKSMmyDCK94t_ID0pHfdHrDjTIqKNUx",
        "Tiêu chuẩn 1": "1PGLhrKUl9swE2TiKM__xIBl2ZzLeZ1K-",
        "Tiêu chuẩn 2": "1RutTLEKikugDnb5kq0c77IOtYYdBXlId",
        "Tiêu chuẩn 3": "ID_T3", "Tiêu chuẩn 4": "ID_T4", "Tiêu chuẩn 5": "ID_T5"
    }
    
    rid = REPORT_IDS.get(st.session_state.report_option)
    if rid and "ID_" not in rid:
        st.components.v1.iframe(f"https://drive.google.com/file/d/{rid}/preview", height=800, scrolling=True)

# --- CỬA SỔ PHẢI: NỘI DUNG MINH CHỨNG (DÙNG SELECTBOX ĐỂ ỔN ĐỊNH) ---
with col_right:
    st.subheader("🖼️ Nội dung minh chứng")
    
    if df is not None:
        # 1. Lọc tiêu chuẩn để danh sách gọn hơn
        tc_filter = st.selectbox("Lọc minh chứng theo:", ["Tất cả", "Tiêu chuẩn 1", "Tiêu chuẩn 2", "Tiêu chuẩn 3", "Tiêu chuẩn 4", "Tiêu chuẩn 5"])
        
        dff = df.copy()
        if tc_filter != "Tất cả":
            num = tc_filter.split()[-1]
            dff = dff[dff['MaMC'].astype(str).str.contains(f"H{num}", case=False, na=False)]
        
        # 2. Tạo danh sách mã để chọn
        list_mc = dff['MaMC'].tolist()
        
        if list_mc:
            selected_ma = st.selectbox("Mời thầy cô bấm vào đây để chọn Mã minh chứng:", list_mc)
            
            # Lấy link tương ứng với mã đã chọn
            row = dff[dff['MaMC'] == selected_ma].iloc[0]
            url = str(row['LinkDrive'])
            current_url = url.replace("/view", "/preview").split('?')[0] if "/view" in url else url
            
            # 3. Hiển thị nội dung File minh chứng
            st.components.v1.iframe(current_url, height=800, scrolling=True)
        else:
            st.warning("Không tìm thấy minh chứng phù hợp.")
    else:
        st.error("Không tìm thấy file danh_muc_mc.xlsx")