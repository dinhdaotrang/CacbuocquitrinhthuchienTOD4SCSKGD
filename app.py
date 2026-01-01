import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import os
from pathlib import Path
import json
from io import BytesIO

# Import additional features
try:
    from features import (
        render_timeline_chart, render_process_flow, render_additional_charts,
        render_file_management, render_ai_assistant, render_step_checklist, init_checklist_status,
        render_step_templates, render_substep_templates, render_completed_file_upload, get_status_label,
        save_checklist_status
    )
    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Quy trình TOD4 - SCS",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .step-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .step-number {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .step-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .sub-step {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .info-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .step-button-completed {
        background-color: #4CAF50 !important;
        color: white !important;
        border: 2px solid #4CAF50 !important;
    }
    .step-button-in-progress {
        background-color: #FFC107 !important;
        color: #000 !important;
        border: 2px solid #FFC107 !important;
    }
    .step-button-not-started {
        background-color: #FFFFFF !important;
        color: #333 !important;
        border: 2px solid #ddd !important;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and process CSV data"""
    try:
        # Read CSV with proper encoding and skip header rows
        df = pd.read_csv('TOD4_TIẾN ĐỘ VÀ CÁC BƯỚC THỰC HIỆN CV REV2.csv', 
                        encoding='utf-8', skiprows=6)
        
        # Take only first 7 columns (the rest are empty)
        df = df.iloc[:, :7].copy()
        
        # Clean column names
        df.columns = ['STT', 'NoiDung', 'DonViThucHien', 'CanCu', 
                     'ThoiGian', 'CanCuTienDo', 'GhiChu']
        
        # Remove empty rows and rows where STT is NaN
        df = df[df['STT'].notna()].copy()
        df = df[df['STT'].astype(str).str.strip() != ''].copy()
        
        # Extract step number and level
        def parse_step(stt):
            if pd.isna(stt):
                return None, None, None
            
            stt_str = str(stt).strip().upper()
            if 'BƯỚC' in stt_str:
                match = re.search(r'BƯỚC\s*(\d+)', stt_str)
                if match:
                    return int(match.group(1)), 'step', None
            elif stt_str.startswith('B'):
                # Extract step number and sub-step
                match = re.match(r'B(\d+)(?:\.(\d+))?(?:\.(\d+))?', stt_str)
                if match:
                    step_num = int(match.group(1))
                    sub1 = int(match.group(2)) if match.group(2) else None
                    sub2 = int(match.group(3)) if match.group(3) else None
                    level = 'sub' + str(len([x for x in [sub1, sub2] if x is not None]))
                    return step_num, level, (sub1, sub2)
            
            return None, None, None
        
        parsed = df['STT'].apply(parse_step)
        df['StepNum'] = parsed.apply(lambda x: x[0] if x else None)
        df['Level'] = parsed.apply(lambda x: x[1] if x else None)
        df['SubStep'] = parsed.apply(lambda x: x[2] if x else None)
        
        return df
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {str(e)}")
        return None

@st.cache_data
def process_steps(df):
    """Process data into structured steps"""
    steps = {}
    current_step = None
    
    for idx, row in df.iterrows():
        step_num = row['StepNum']
        level = row['Level']
        
        if level == 'step' and step_num:
            current_step = step_num
            title = str(row['NoiDung']).strip() if pd.notna(row['NoiDung']) else f"BƯỚC {step_num}"
            # Clean title - remove newlines
            title = ' '.join(title.split())
            steps[current_step] = {
                'title': title,
                'can_cu': str(row['CanCu']).strip() if pd.notna(row['CanCu']) else '',
                'can_cu_tien_do': str(row['CanCuTienDo']).strip() if pd.notna(row['CanCuTienDo']) else '',
                'substeps': []
            }
        elif level and step_num == current_step and current_step:
            content = str(row['NoiDung']).strip() if pd.notna(row['NoiDung']) else ''
            content = ' '.join(content.split())  # Clean content
            
            substep_info = {
                'code': str(row['STT']).strip(),
                'content': content,
                'don_vi': str(row['DonViThucHien']).strip() if pd.notna(row['DonViThucHien']) else '',
                'can_cu': str(row['CanCu']).strip() if pd.notna(row['CanCu']) else '',
                'thoi_gian': str(row['ThoiGian']).strip() if pd.notna(row['ThoiGian']) else '',
                'can_cu_tien_do': str(row['CanCuTienDo']).strip() if pd.notna(row['CanCuTienDo']) else '',
                'ghi_chu': str(row['GhiChu']).strip() if pd.notna(row['GhiChu']) else '',
                'level': level
            }
            steps[current_step]['substeps'].append(substep_info)
    
    return steps

def extract_days(text):
    """Extract number of days from text"""
    if pd.isna(text) or not text:
        return 0
    
    text = str(text).lower()
    # Look for patterns like "28 ngày", "15 ngày", "07 ngày làm việc"
    matches = re.findall(r'(\d+)\s*ngày', text)
    if matches:
        return int(matches[0])
    return 0

def calculate_total_days(steps):
    """Calculate total days for each step"""
    step_days = {}
    for step_num, step_data in steps.items():
        total = 0
        for substep in step_data['substeps']:
            days = extract_days(substep['thoi_gian'])
            total += days
        step_days[step_num] = total
    return step_days

def render_overview(steps, step_days):
    """Render overview page"""
    st.markdown('<div class="main-header">📋 TỔNG QUAN QUY TRÌNH</div>', unsafe_allow_html=True)
    
    # Project title
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 2rem;">
        <h2 style="color: #1f77b4; margin: 0;">TRÌNH TỰ PHÊ DUYỆT DỰ ÁN VÀ LỰA CHỌN NHÀ ĐẦU TƯ</h2>
        <p style="color: #666; margin: 0.5rem 0 0 0;">Thực hiện dự án đầu tư có sử dụng đất (TOD4, SCS)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Tổng số bước", len(steps))
    
    with col2:
        total_substeps = sum(len(s['substeps']) for s in steps.values())
        st.metric("Tổng số công việc", total_substeps)
    
    st.markdown("---")
    
    # Timeline visualization
    st.subheader("📊 Biểu đồ tiến độ theo bước")
    
    step_names = [f"Bước {i}" for i in sorted(steps.keys())]
    days_list = [step_days.get(i, 0) for i in sorted(steps.keys())]
    
    fig = px.bar(
        x=step_names,
        y=days_list,
        labels={'x': 'Các bước', 'y': 'Thời gian (ngày)'},
        color=days_list,
        color_continuous_scale='Blues',
        text=days_list,
        category_orders={'x': step_names}  # Ensure order
    )
    fig.update_traces(texttemplate='%{text} ngày', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45,
        margin=dict(b=100),
        xaxis=dict(categoryorder='array', categoryarray=step_names)  # Force order
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Additional visualizations if features available
    if FEATURES_AVAILABLE:
        render_timeline_chart(steps, step_days)
        st.markdown("---")
        render_process_flow(steps)
        st.markdown("---")
        render_additional_charts(steps, step_days)
        st.markdown("---")

def render_step_detail(steps, step_num):
    """Render detailed view of a specific step"""
    if step_num not in steps:
        st.error(f"Không tìm thấy Bước {step_num}")
        return
    
    step_data = steps[step_num]
    
    st.markdown(f'<div class="main-header">BƯỚC {step_num}: {step_data["title"]}</div>', unsafe_allow_html=True)
    
    # Step info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Collect all legal bases from substeps
        all_can_cu = set()
        all_can_cu_tien_do = set()
        
        # Add step-level basis
        if step_data['can_cu']:
            all_can_cu.add(step_data['can_cu'])
        if step_data['can_cu_tien_do']:
            all_can_cu_tien_do.add(step_data['can_cu_tien_do'])
        
        # Add substep-level bases
        for substep in step_data['substeps']:
            if substep['can_cu']:
                all_can_cu.add(substep['can_cu'])
            if substep['can_cu_tien_do']:
                all_can_cu_tien_do.add(substep['can_cu_tien_do'])
        
        # Display legal bases section
        st.markdown("### 📜 Căn cứ pháp lý")
        if all_can_cu:
            for idx, can_cu in enumerate(sorted(all_can_cu), 1):
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 5px; margin: 0.5rem 0; border-left: 4px solid #2196f3;">
                    <strong>{idx}.</strong> {can_cu}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Chưa có căn cứ pháp lý được ghi nhận")
        
        st.markdown("---")
        
        st.markdown("### 📅 Căn cứ tiến độ")
        if all_can_cu_tien_do:
            for idx, can_cu_td in enumerate(sorted(all_can_cu_tien_do), 1):
                st.markdown(f"""
                <div style="background: #fff3e0; padding: 0.8rem; border-radius: 5px; margin: 0.5rem 0; border-left: 4px solid #ff9800;">
                    <strong>{idx}.</strong> {can_cu_td}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Chưa có căn cứ tiến độ được ghi nhận")
    
    with col2:
        st.markdown("### 📊 Thống kê")
        st.metric("Số công việc", len(step_data['substeps']))
        total_days = sum(extract_days(s['thoi_gian']) for s in step_data['substeps'])
        if total_days > 0:
            st.metric("Tổng thời gian", f"{total_days} ngày")
        
        # Summary of legal bases
        st.markdown("---")
        st.markdown("### 📋 Tóm tắt căn cứ")
        st.write(f"**Căn cứ pháp lý:** {len(all_can_cu)} căn cứ")
        st.write(f"**Căn cứ tiến độ:** {len(all_can_cu_tien_do)} căn cứ")
    
    st.markdown("---")
    
    # Integrated Substeps with Checklist
    st.subheader("📋 Chi tiết công việc & Checklist")
    
    # Initialize checklist status for step
    if FEATURES_AVAILABLE:
        if 'step_status' not in st.session_state:
            st.session_state['step_status'] = {}
        if step_num not in st.session_state['step_status']:
            st.session_state['step_status'][step_num] = {
                'status': 'not_started',
                'notes': ''
            }
        
        if 'substep_status' not in st.session_state:
            st.session_state['substep_status'] = {}
        for substep in step_data['substeps']:
            substep_key = f"{step_num}_{substep['code']}"
            if substep_key not in st.session_state['substep_status']:
                st.session_state['substep_status'][substep_key] = {
                    'status': 'not_started',
                    'notes': ''
                }
        
        # Step-level status
        step_status = st.session_state['step_status'][step_num]
        col_step1, col_step2 = st.columns([3, 1])
        with col_step1:
            status = st.selectbox(
                f"Trạng thái Bước {step_num}",
                options=['not_started', 'in_progress', 'completed'],
                format_func=get_status_label,
                index=['not_started', 'in_progress', 'completed'].index(step_status['status']),
                key=f"step_status_{step_num}"
            )
            st.session_state['step_status'][step_num]['status'] = status
            # Save to file
            save_checklist_status()
        with col_step2:
            st.write(f"**Trạng thái:** {get_status_label(status)}")
        
        # Show completed file upload for step if completed
        if status == 'completed':
            render_completed_file_upload(step_num)
        
        st.markdown("---")
    
    # Substeps with integrated checklist
    for idx, substep in enumerate(step_data['substeps'], 1):
        with st.container():
            st.markdown(f"""
            <div class="sub-step">
                <h4 style="color: #667eea; margin-bottom: 0.5rem;">
                    {substep['code']}: {substep['content']}
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Details in columns
            col1, col2 = st.columns(2)
            
            with col1:
                if substep['don_vi']:
                    st.write(f"**🏢 Đơn vị thực hiện:** {substep['don_vi']}")
                if substep['can_cu']:
                    st.write(f"**📜 Căn cứ:** {substep['can_cu']}")
            
            with col2:
                if substep['thoi_gian']:
                    st.write(f"**⏱️ Thời gian:** {substep['thoi_gian']}")
                if substep['can_cu_tien_do']:
                    st.write(f"**📅 Căn cứ tiến độ:** {substep['can_cu_tien_do']}")
            
            if substep['ghi_chu']:
                st.info(f"**💡 Ghi chú:** {substep['ghi_chu']}")
            
            # Checklist & Status for this substep
            if FEATURES_AVAILABLE:
                substep_key = f"{step_num}_{substep['code']}"
                substep_status = st.session_state['substep_status'][substep_key]
                
                col_status1, col_status2 = st.columns([3, 1])
                with col_status1:
                    substep_status_val = st.selectbox(
                        f"Trạng thái {substep['code']}",
                        options=['not_started', 'in_progress', 'completed'],
                        format_func=get_status_label,
                        index=['not_started', 'in_progress', 'completed'].index(substep_status['status']),
                        key=f"substep_status_{substep_key}"
                    )
                    st.session_state['substep_status'][substep_key]['status'] = substep_status_val
                    # Save to file
                    save_checklist_status()
                with col_status2:
                    st.write(f"**Trạng thái:** {get_status_label(substep_status_val)}")
                
                # Show template file upload for each substep
                st.markdown("<div style='margin-left: 1rem; padding: 0.5rem; background: #e3f2fd; border-radius: 5px; margin-top: 0.5rem; margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
                render_substep_templates(step_num, substep['code'])
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Show completed file upload if substep is completed
                if substep_status_val == 'completed':
                    st.markdown("<div style='margin-left: 1rem; padding: 0.5rem; background: #f8f9fa; border-radius: 5px; margin-top: 0.5rem; margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
                    render_completed_file_upload(step_num, substep['code'], substep['content'])
                    st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
    
    # Step templates section
    if FEATURES_AVAILABLE:
        render_step_templates(step_num)

def render_progress_table(steps, step_days):
    """Render detailed progress table page"""
    st.markdown('<div class="main-header">📋 BẢNG TIẾN ĐỘ TỔNG QUÁT</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 2rem;">
        <p style="color: #666; margin: 0;">Bảng tổng hợp tiến độ thực hiện các bước trong quy trình</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter and search options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Tìm kiếm trong bảng", "", key="table_search")
    with col2:
        show_full = st.checkbox("Hiển thị đầy đủ nội dung", value=False)
    
    # Create progress table data
    progress_data = []
    cumulative_days = 0
    
    for step_num in sorted(steps.keys()):
        step_data = steps[step_num]
        days = step_days.get(step_num, 0)
        num_substeps = len(step_data['substeps'])
        cumulative_days += days
        
        # Get main responsible unit (first substep with don_vi if available)
        main_don_vi = ""
        for substep in step_data['substeps']:
            if substep['don_vi']:
                main_don_vi = substep['don_vi']
                break
        
        # Collect all legal bases from step and substeps
        all_can_cu = set()
        all_can_cu_tien_do = set()
        
        # Add step-level basis
        if step_data['can_cu']:
            all_can_cu.add(step_data['can_cu'])
        if step_data['can_cu_tien_do']:
            all_can_cu_tien_do.add(step_data['can_cu_tien_do'])
        
        # Add substep-level bases
        for substep in step_data['substeps']:
            if substep['can_cu']:
                all_can_cu.add(substep['can_cu'])
            if substep['can_cu_tien_do']:
                all_can_cu_tien_do.add(substep['can_cu_tien_do'])
        
        # Format displays
        title_display = step_data['title'] if show_full else (step_data['title'][:100] + ('...' if len(step_data['title']) > 100 else ''))
        don_vi_display = main_don_vi if show_full else (main_don_vi[:60] + ('...' if len(main_don_vi) > 60 else '') if main_don_vi else '-')
        
        # Format legal bases - join all with separator
        can_cu_full = '; '.join(sorted(all_can_cu)) if all_can_cu else '-'
        can_cu_display = can_cu_full if show_full else (can_cu_full[:100] + ('...' if len(can_cu_full) > 100 else ''))
        
        # Format progress bases - join all with separator
        can_cu_tien_do_full = '; '.join(sorted(all_can_cu_tien_do)) if all_can_cu_tien_do else '-'
        can_cu_tien_do_display = can_cu_tien_do_full if show_full else (can_cu_tien_do_full[:100] + ('...' if len(can_cu_tien_do_full) > 100 else ''))
        
        row_data = {
            'STT': f"BƯỚC {step_num}",
            'Nội dung công việc': title_display,
            'Số công việc': num_substeps,
            'Thời gian (ngày)': days if days > 0 else '-',
            'Thời gian tích lũy (ngày)': cumulative_days,
            'Đơn vị thực hiện chính': don_vi_display if main_don_vi else '-',
            'Căn cứ pháp lý': can_cu_display,
            'Căn cứ tiến độ': can_cu_tien_do_display
        }
        
        # Apply search filter
        if search_term:
            search_lower = search_term.lower()
            if (search_lower in row_data['Nội dung công việc'].lower() or 
                search_lower in row_data['Đơn vị thực hiện chính'].lower() or
                search_lower in row_data['Căn cứ pháp lý'].lower() or
                search_lower in row_data['Căn cứ tiến độ'].lower()):
                progress_data.append(row_data)
        else:
            progress_data.append(row_data)
    
    if progress_data:
        df_progress = pd.DataFrame(progress_data)
        
        # Style the dataframe
        st.dataframe(
            df_progress,
            use_container_width=True,
            hide_index=True,
            height=700,
            column_config={
                "STT": st.column_config.TextColumn("STT", width="small"),
                "Nội dung công việc": st.column_config.TextColumn("Nội dung công việc", width="large"),
                "Số công việc": st.column_config.NumberColumn("Số công việc", width="small", format="%d"),
                "Thời gian (ngày)": st.column_config.TextColumn("Thời gian (ngày)", width="medium"),
                "Thời gian tích lũy (ngày)": st.column_config.NumberColumn("Thời gian tích lũy", width="medium", format="%d"),
                "Đơn vị thực hiện chính": st.column_config.TextColumn("Đơn vị thực hiện chính", width="medium"),
                "Căn cứ pháp lý": st.column_config.TextColumn("Căn cứ pháp lý", width="large"),
                "Căn cứ tiến độ": st.column_config.TextColumn("Căn cứ tiến độ", width="large")
            }
        )
    else:
        st.warning("Không tìm thấy kết quả phù hợp với từ khóa tìm kiếm.")

def main():
    """Main application"""
    # Load data
    df = load_data()
    if df is None:
        st.error("Không thể tải dữ liệu. Vui lòng kiểm tra file CSV.")
        return
    
    # Process data
    steps = process_steps(df)
    step_days = calculate_total_days(steps)
    
    # Initialize checklist status (loads from file if available)
    if FEATURES_AVAILABLE:
        from features import init_checklist_status
        init_checklist_status(steps)
    
    # Initialize navigation state
    if 'navigation' not in st.session_state:
        st.session_state['navigation'] = "📊 Tổng quan"
    if 'last_page_selection' not in st.session_state:
        st.session_state['last_page_selection'] = st.session_state['navigation']
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/667eea/ffffff?text=TOD4+SCS", use_container_width=True)
        st.markdown("## 🧭 Điều hướng")
        
        page_options = ["📊 Tổng quan"]
        if FEATURES_AVAILABLE:
            page_options.extend(["📁 Tài liệu", "🤖 Trợ lý AI"])
        
        page = st.radio(
            "Chọn trang",
            page_options,
            key="navigation"
        )
        
        # If page changed, clear selected_step to show the selected page
        if page != st.session_state['last_page_selection']:
            st.session_state['last_page_selection'] = page
            if 'selected_step' in st.session_state:
                del st.session_state['selected_step']
        
        st.markdown("---")
        st.markdown("## 📌 Chọn bước cụ thể")
        
        # Initialize step status if needed
        if FEATURES_AVAILABLE:
            if 'step_status' not in st.session_state:
                st.session_state['step_status'] = {}
            for step_num in steps.keys():
                if step_num not in st.session_state['step_status']:
                    st.session_state['step_status'][step_num] = {
                        'status': 'not_started',
                        'notes': ''
                    }
            
            # Calculate and display overall progress
            from features import calculate_overall_progress
            overall_progress = calculate_overall_progress(steps)
            st.metric("📊 Hoàn thành tổng thể", f"{overall_progress}%")
            st.progress(overall_progress / 100)
            st.markdown("---")
        
        # Color legend
        st.markdown("""
        <div style="background: #f0f2f6; padding: 0.8rem; border-radius: 5px; margin-bottom: 1rem; font-size: 0.85rem;">
            <strong>Bảng màu trạng thái:</strong><br>
            <div style="display: flex; align-items: center; margin: 0.3rem 0;">
                <div style="width: 20px; height: 20px; background-color: #4CAF50; border-radius: 3px; margin-right: 0.5rem;"></div>
                <span>✅ Hoàn thành</span>
            </div>
            <div style="display: flex; align-items: center; margin: 0.3rem 0;">
                <div style="width: 20px; height: 20px; background-color: #FFC107; border-radius: 3px; margin-right: 0.5rem;"></div>
                <span>🔄 Đang thực hiện</span>
            </div>
            <div style="display: flex; align-items: center; margin: 0.3rem 0;">
                <div style="width: 20px; height: 20px; background-color: #FFFFFF; border: 1px solid #ddd; border-radius: 3px; margin-right: 0.5rem;"></div>
                <span>⏸️ Chưa thực hiện</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Step buttons with color coding using columns layout
        for step_num in sorted(steps.keys()):
            if FEATURES_AVAILABLE:
                step_status = st.session_state['step_status'].get(step_num, {'status': 'not_started'})
                status = step_status.get('status', 'not_started')
                
                # Determine colors
                if status == 'completed':
                    bg_color = "#4CAF50"
                    status_icon = "✅"
                    border_color = "#4CAF50"
                elif status == 'in_progress':
                    bg_color = "#FFC107"
                    status_icon = "🔄"
                    border_color = "#FFC107"
                else:
                    bg_color = "#FFFFFF"
                    status_icon = "⏸️"
                    border_color = "#ddd"
                
                # Use columns: small color indicator + button
                col_color, col_button = st.columns([0.12, 0.88])
                with col_color:
                    st.markdown(f'<div style="background-color: {bg_color}; height: 38px; border-radius: 0.25rem; margin-top: 0.25rem; border: 2px solid {border_color};"></div>', unsafe_allow_html=True)
                with col_button:
                    button_label = f"{status_icon} Bước {step_num}"
                    if st.button(button_label, key=f"nav_step_{step_num}", use_container_width=True):
                        st.session_state['selected_step'] = step_num
                        st.rerun()
            else:
                if st.button(f"Bước {step_num}", key=f"nav_step_{step_num}", use_container_width=True):
                    st.session_state['selected_step'] = step_num
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Thống kê")
        st.write(f"**Tổng số bước:** {len(steps)}")
        st.write(f"**Tổng công việc:** {sum(len(s['substeps']) for s in steps.values())}")
        st.write(f"**Tổng thời gian:** {sum(step_days.values())} ngày")
    
    # Main content
    # Show step detail only if selected_step exists (user clicked a step button)
    # Otherwise show the selected page
    if 'selected_step' in st.session_state and st.session_state['selected_step'] is not None:
        render_step_detail(steps, st.session_state['selected_step'])
    elif page == "📊 Tổng quan":
        render_overview(steps, step_days)
    elif page == "📁 Tài liệu" and FEATURES_AVAILABLE:
        render_file_management()
    elif page == "🤖 Trợ lý AI" and FEATURES_AVAILABLE:
        render_ai_assistant(steps)

if __name__ == "__main__":
    main()

