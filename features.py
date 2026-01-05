"""
Additional features for TOD4 SCS Process Management App
Includes: Visualization, File Management, Checklist, AI Assistant
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import os
import hashlib
import uuid

# Optional imports
try:
    import openai
    from dotenv import load_dotenv
    OPENAI_AVAILABLE = True
    load_dotenv()
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx2python import docx2python
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ==================== HELPER FUNCTIONS ====================

def sanitize_key(key_string):
    """Sanitize a string to be used as a Streamlit widget key
    Uses hash to ensure uniqueness and avoid duplicate key errors"""
    # Use full hash to ensure key is always unique and valid
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"key_{key_hash}"

# ==================== VISUALIZATION FUNCTIONS ====================

def render_timeline_chart(steps, step_days):
    """Render timeline Gantt chart showing steps over time"""
    st.subheader("📅 Biểu đồ Timeline - Tiến độ theo thời gian")
    
    # Calculate cumulative timeline
    timeline_data = []
    cumulative_days = 0
    
    for step_num in sorted(steps.keys()):
        step_data = steps[step_num]
        days = step_days.get(step_num, 0)
        
        timeline_data.append({
            'Bước': f"Bước {step_num}",
            'Nội dung': step_data['title'][:50] + ('...' if len(step_data['title']) > 50 else ''),
            'Bắt đầu (ngày)': cumulative_days,
            'Kết thúc (ngày)': cumulative_days + days,
            'Thời gian (ngày)': days
        })
        cumulative_days += days
    
    df_timeline = pd.DataFrame(timeline_data)
    
    # Create Gantt chart
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3[:len(timeline_data)]
    
    for idx, row in df_timeline.iterrows():
        fig.add_trace(go.Bar(
            name=row['Bước'],
            base=row['Bắt đầu (ngày)'],
            x=[row['Thời gian (ngày)']],
            y=[row['Bước']],
            orientation='h',
            marker_color=colors[idx],
            text=f"{row['Thời gian (ngày)']} ngày",
            textposition='inside',
            hovertemplate=f"<b>{row['Bước']}</b><br>" +
                         f"Nội dung: {row['Nội dung']}<br>" +
                         f"Thời gian: {row['Thời gian (ngày)']} ngày<extra></extra>"
        ))
    
    # Sort y-axis to show steps in order (Bước 1 to Bước 9)
    step_order = [f"Bước {i}" for i in sorted(steps.keys())]
    
    fig.update_layout(
        title='Timeline thực hiện các bước trong quy trình',
        xaxis_title='Thời gian tích lũy (ngày)',
        yaxis_title='Các bước',
        height=500,
        barmode='overlay',
        showlegend=False,
        hovermode='closest',
        yaxis=dict(
            categoryorder='array',
            categoryarray=step_order
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display timeline table
    with st.expander("📋 Xem chi tiết timeline"):
        st.dataframe(df_timeline, use_container_width=True, hide_index=True)

def render_process_flow(steps):
    """Render process flow diagram"""
    st.subheader("🔄 Biểu đồ luồng quy trình (Process Flow)")
    
    # Create flow data
    step_list = sorted(steps.keys())
    flow_data = []
    
    for i, step_num in enumerate(step_list):
        step_data = steps[step_num]
        flow_data.append({
            'Bước': step_num,
            'Tên bước': f"Bước {step_num}",
            'Nội dung': step_data['title'][:40] + ('...' if len(step_data['title']) > 40 else ''),
            'Vị trí X': i,
            'Vị trí Y': 0
        })
    
    df_flow = pd.DataFrame(flow_data)
    
    # Create flow diagram using scatter plot with annotations
    fig = go.Figure()
    
    # Add nodes (steps)
    fig.add_trace(go.Scatter(
        x=df_flow['Vị trí X'],
        y=df_flow['Vị trí Y'],
        mode='markers+text',
        marker=dict(
            size=100,
            color=px.colors.qualitative.Set2[:len(df_flow)],
            line=dict(width=2, color='white')
        ),
        text=df_flow['Tên bước'],
        textposition='middle center',
        textfont=dict(size=12, color='white', family='Arial Black'),
        name='Các bước',
        hovertemplate='<b>%{text}</b><br>%{customdata}<extra></extra>',
        customdata=df_flow['Nội dung']
    ))
    
    # Add arrows between steps
    for i in range(len(df_flow) - 1):
        fig.add_annotation(
            x=df_flow.loc[i+1, 'Vị trí X'] - 0.3,
            y=df_flow.loc[i+1, 'Vị trí Y'],
            ax=df_flow.loc[i, 'Vị trí X'] + 0.3,
            ay=df_flow.loc[i, 'Vị trí Y'],
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor='#666',
            axref='x',
            ayref='y'
        )
    
    fig.update_layout(
        title='Sơ đồ luồng quy trình - Thứ tự thực hiện các bước',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300,
        showlegend=False,
        plot_bgcolor='white',
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display step details
    with st.expander("📋 Chi tiết các bước trong luồng"):
        for idx, row in df_flow.iterrows():
            step_num = row['Bước']
            step_data = steps[step_num]
            st.write(f"**{row['Tên bước']}:** {step_data['title']}")

def render_additional_charts(steps, step_days):
    """Render additional charts (pie, line, etc.)"""
    st.subheader("📊 Biểu đồ bổ trợ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Biểu đồ tròn - Phân bổ thời gian theo bước**")
        # Sort steps in order
        sorted_step_nums = sorted(steps.keys())
        step_names = [f"Bước {i}" for i in sorted_step_nums]
        days_list = [step_days.get(i, 0) for i in sorted_step_nums]
        
        fig_pie = px.pie(
            values=days_list,
            names=step_names,
            title='Tỷ lệ thời gian của từng bước',
            color_discrete_sequence=px.colors.qualitative.Set3,
            category_orders={'names': step_names}  # Ensure order
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("**Biểu đồ đường - Tiến độ tích lũy**")
        cumulative_days = 0
        cumulative_data = []
        
        # Sort steps in order
        sorted_step_nums = sorted(steps.keys())
        for step_num in sorted_step_nums:
            days = step_days.get(step_num, 0)
            cumulative_days += days
            cumulative_data.append({
                'Bước': f"Bước {step_num}",
                'Thời gian tích lũy': cumulative_days
            })
        
        df_cumulative = pd.DataFrame(cumulative_data)
        
        fig_line = px.line(
            df_cumulative,
            x='Bước',
            y='Thời gian tích lũy',
            markers=True,
            title='Thời gian tích lũy theo từng bước',
            labels={'Thời gian tích lũy': 'Thời gian tích lũy (ngày)'},
            category_orders={'Bước': [f"Bước {i}" for i in sorted_step_nums]}  # Ensure order
        )
        fig_line.update_traces(line_color='#1f77b4', line_width=3, marker_size=10)
        fig_line.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_line, use_container_width=True)

# ==================== FILE MANAGEMENT FUNCTIONS ====================

def init_file_storage():
    """Initialize file storage directory"""
    storage_dir = Path("uploaded_documents")
    storage_dir.mkdir(exist_ok=True)
    return storage_dir

def save_file_info(filename, file_type, storage_dir):
    """Save file metadata to JSON"""
    metadata_file = storage_dir / "metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = []
    
    # Generate unique ID for this file
    file_id = str(uuid.uuid4())[:8]
    
    file_info = {
        'id': file_id,  # Add unique ID
        'filename': filename,
        'file_type': file_type,
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_path': str(storage_dir / filename)
    }
    
    metadata.append(file_info)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_info

def load_file_metadata(storage_dir):
    """Load file metadata"""
    metadata_file = storage_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_text_content(filename, text_content, storage_dir):
    """Save extracted text content to a text file"""
    try:
        # Create text file name from original filename
        base_name = Path(filename).stem
        text_file_path = storage_dir / f"{base_name}_text.txt"
        
        # Save text content
        with open(text_file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return text_file_path
    except Exception as e:
        st.error(f"Lỗi khi lưu nội dung văn bản: {str(e)}")
        return None

def get_saved_text_path(filename, storage_dir):
    """Get path to saved text file if exists"""
    base_name = Path(filename).stem
    text_file_path = storage_dir / f"{base_name}_text.txt"
    return text_file_path if text_file_path.exists() else None

def delete_file_info(filename, storage_dir):
    """Delete file and its metadata"""
    metadata_file = storage_dir / "metadata.json"
    
    if not metadata_file.exists():
        return False
    
    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find and remove file from metadata
        file_info = None
        updated_metadata = []
        for info in metadata:
            if info['filename'] == filename:
                file_info = info
            else:
                updated_metadata.append(info)
        
        if file_info:
            # Delete physical file
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Delete saved text content if exists
            text_file_path = get_saved_text_path(filename, storage_dir)
            if text_file_path and text_file_path.exists():
                text_file_path.unlink()
            
            # Update metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(updated_metadata, f, ensure_ascii=False, indent=2)
            
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi khi xóa file: {str(e)}")
        return False

def extract_text_from_file(file_path, file_type):
    """Extract text content from uploaded file"""
    try:
        if file_type == 'application/pdf' and PDF_AVAILABLE:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' and DOCX_AVAILABLE:
            doc = docx2python(file_path)
            return doc.text
        elif file_type == 'text/plain':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return None
    except Exception as e:
        st.error(f"Lỗi khi đọc file: {str(e)}")
        return None

def render_file_management():
    """Render file upload and management page"""
    st.markdown('<div class="main-header">📁 QUẢN LÝ TÀI LIỆU</div>', unsafe_allow_html=True)
    
    storage_dir = init_file_storage()
    
    # Upload section
    st.subheader("📤 Upload tài liệu")
    
    uploaded_files = st.file_uploader(
        "Chọn file để upload",
        type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls'],
        help="Hỗ trợ các định dạng: PDF, Word, Text, Excel. Có thể upload nhiều file cùng lúc.",
        accept_multiple_files=True,
        key="file_management_upload"
    )
    
    # Initialize session state for tracking uploaded files
    upload_key = "file_management_uploaded"
    if upload_key not in st.session_state:
        st.session_state[upload_key] = []
    
    # Check if new files were uploaded
    if uploaded_files and len(uploaded_files) > 0:
        # Get list of new file names (not yet processed)
        processed_files = st.session_state[upload_key]
        new_files = [f for f in uploaded_files if f.name not in processed_files]
        
        if new_files:
            # Handle multiple files
            saved_files = []
            for uploaded_file in new_files:
                try:
                    # Check if file already exists
                    file_path = storage_dir / uploaded_file.name
                    if file_path.exists():
                        st.warning(f"⚠️ File {uploaded_file.name} đã tồn tại, sẽ được ghi đè.")
                    
                    # Save file
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get file type
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    # Save metadata
                    file_info = save_file_info(uploaded_file.name, file_type, storage_dir)
                    saved_files.append(uploaded_file.name)
                    
                    # Extract and auto-save text content for each file
                    text_content = extract_text_from_file(file_path, file_type)
                    if text_content:
                        saved_text_path = save_text_content(uploaded_file.name, text_content, storage_dir)
                    
                    # Mark as processed
                    st.session_state[upload_key].append(uploaded_file.name)
                except Exception as e:
                    st.error(f"❌ Lỗi khi upload file {uploaded_file.name}: {str(e)}")
            
            if saved_files:
                if len(saved_files) == 1:
                    st.success(f"✅ Đã upload thành công: {saved_files[0]}")
                    # Show preview for single file
                    uploaded_file = new_files[0]
                    file_path = storage_dir / uploaded_file.name
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    # Download button for just uploaded file
                    col_up1, col_up2 = st.columns([3, 1])
                    with col_up2:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            key_base = f"download_uploaded_{uploaded_file.name}_{datetime.now().isoformat()}"
                            unique_key = sanitize_key(key_base)
                            st.download_button(
                                label="⬇️ Tải xuống file vừa upload",
                                data=file_data,
                                file_name=uploaded_file.name,
                                mime=file_type,
                                key=unique_key,
                                use_container_width=True
                            )
                    
                    # Extract and preview text
                    text_content = extract_text_from_file(file_path, file_type)
                    if text_content:
                        # Auto-save text content
                        saved_text_path = save_text_content(uploaded_file.name, text_content, storage_dir)
                        if saved_text_path:
                            st.info(f"💾 Đã tự động lưu nội dung văn bản vào: {saved_text_path.name}")
                        
                        with st.expander("📄 Xem trước nội dung file"):
                            st.text_area("Nội dung", text_content[:5000], height=300, disabled=True, key=f"preview_{uploaded_file.name}")
                            if len(text_content) > 5000:
                                st.info(f"File có {len(text_content)} ký tự. Chỉ hiển thị 5000 ký tự đầu.")
                            
                            # Download text content button
                            if saved_text_path:
                                with open(saved_text_path, 'r', encoding='utf-8') as f:
                                    text_data = f.read()
                                key_base = f"download_text_{uploaded_file.name}_{datetime.now().isoformat()}"
                                unique_key = sanitize_key(key_base)
                                st.download_button(
                                    label="💾 Tải xuống nội dung văn bản (.txt)",
                                    data=text_data,
                                    file_name=saved_text_path.name,
                                    mime="text/plain",
                                    key=unique_key,
                                    use_container_width=True
                                )
                else:
                    st.success(f"✅ Đã upload thành công {len(saved_files)} file: {', '.join(saved_files)}")
                    st.info(f"💾 Đã tự động lưu nội dung văn bản cho các file có thể trích xuất.")
                st.rerun()
    elif uploaded_files is not None and len(uploaded_files) == 0:
        # Reset processed files list when uploader is cleared
        st.session_state[upload_key] = []
    
    st.markdown("---")
    
    # File list
    st.subheader("📋 Danh sách tài liệu đã upload")
    
    metadata = load_file_metadata(storage_dir)
    
    if metadata:
        # Reverse to show newest first
        metadata.reverse()
        
        # Display files with actions in a card-based layout
        st.markdown("### 📋 Danh sách file")
        st.markdown("**💡 Mẹo:** Mỗi file có các nút: ⬇️ Tải xuống, 📄 Đọc nội dung, 💾 Lưu văn bản, 🗑️ Xóa**")
        
        # Create a more interactive display with cards
        for idx, file_info in enumerate(metadata):
            file_path_obj = Path(file_info['file_path'])
            file_exists = file_path_obj.exists()
            
            # File card
            with st.container():
                col_info, col_actions = st.columns([3, 2])
                
                with col_info:
                    status_icon = "✅" if file_exists else "⚠️"
                    status_text = "" if file_exists else '<span style="color: red;"> (File không tồn tại)</span>'
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #667eea;">
                        <strong>{status_icon} {file_info['filename']}</strong>{status_text}<br>
                        <small style="color: #666;">📁 Loại: {file_info['file_type']}<br>📅 Upload: {file_info['upload_date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    # Action buttons
                    col_dl, col_read, col_save, col_del = st.columns(4)
                    
                    with col_dl:
                        if file_exists:
                            with open(file_path_obj, "rb") as f:
                                file_data = f.read()
                                # Use file_path hash for uniqueness
                                file_path_hash = hashlib.md5(str(file_path_obj).encode()).hexdigest()[:16]
                                key_base = f"dl_{file_path_hash}_{idx}"
                                unique_key = sanitize_key(key_base)
                                st.download_button(
                                    "⬇️ Tải xuống",
                                    data=file_data,
                                    file_name=file_info['filename'],
                                    mime=file_info['file_type'],
                                    key=unique_key,
                                    use_container_width=True,
                                    help="Tải xuống file gốc"
                                )
                        else:
                            st.button("⬇️ Tải xuống", key=f"dl_disabled_{idx}", disabled=True, use_container_width=True, help="File không tồn tại")
                    
                    with col_read:
                        if st.button("📄 Đọc", key=f"read_{idx}_{file_info['filename']}", use_container_width=True, help="Đọc nội dung file"):
                            if file_exists:
                                text_content = extract_text_from_file(file_path_obj, file_info['file_type'])
                                if text_content:
                                    st.session_state[f'file_content_{file_info["filename"]}'] = text_content
                                    st.session_state['selected_file_to_view'] = file_info['filename']
                                    st.rerun()
                                else:
                                    st.warning("Không thể đọc nội dung file này")
                            else:
                                st.warning("File không tồn tại")
                    
                    with col_save:
                        # Check if text content exists or can be extracted
                        saved_text_path = get_saved_text_path(file_info['filename'], storage_dir)
                        if saved_text_path and saved_text_path.exists():
                            # Text already saved, offer download
                            with open(saved_text_path, 'r', encoding='utf-8') as f:
                                text_data = f.read()
                            # Use file_path hash for uniqueness
                            file_path_hash = hashlib.md5(str(file_path_obj).encode()).hexdigest()[:16]
                            key_base = f"save_text_{file_path_hash}_{idx}"
                            unique_key = sanitize_key(key_base)
                            st.download_button(
                                "💾 Lưu văn bản",
                                data=text_data,
                                file_name=saved_text_path.name,
                                mime="text/plain",
                                key=unique_key,
                                use_container_width=True,
                                help="Tải xuống nội dung văn bản đã lưu"
                            )
                        elif file_exists:
                            # Try to extract and save text
                            if st.button("💾 Lưu văn bản", key=f"save_btn_{idx}_{file_info['filename']}", use_container_width=True, help="Lưu nội dung văn bản"):
                                text_content = extract_text_from_file(file_path_obj, file_info['file_type'])
                                if text_content:
                                    saved_path = save_text_content(file_info['filename'], text_content, storage_dir)
                                    if saved_path:
                                        st.success(f"✅ Đã lưu nội dung văn bản!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Không thể lưu nội dung văn bản")
                                else:
                                    st.warning("⚠️ Không thể trích xuất nội dung từ file này")
                        else:
                            st.button("💾 Lưu văn bản", key=f"save_disabled_{idx}", disabled=True, use_container_width=True, help="File không tồn tại")
                    
                    with col_del:
                        if st.button("🗑️ Xóa", key=f"del_{idx}_{file_info['filename']}", use_container_width=True, help="Xóa file này"):
                            if delete_file_info(file_info['filename'], storage_dir):
                                st.success(f"✅ Đã xóa file: {file_info['filename']}")
                                # Clear any displayed content for deleted file
                                if f'file_content_{file_info["filename"]}' in st.session_state:
                                    del st.session_state[f'file_content_{file_info["filename"]}']
                                if 'selected_file_to_view' in st.session_state and st.session_state['selected_file_to_view'] == file_info['filename']:
                                    del st.session_state['selected_file_to_view']
                                st.rerun()
                            else:
                                st.error(f"❌ Không thể xóa file: {file_info['filename']}")
                
                st.markdown("---")
        
        # Display file content if a file was selected to view
        if 'selected_file_to_view' in st.session_state and st.session_state['selected_file_to_view']:
            selected_file = st.session_state['selected_file_to_view']
            file_info = next((f for f in metadata if f['filename'] == selected_file), None)
            
            if file_info and f'file_content_{selected_file}' in st.session_state:
                st.markdown("---")
                st.subheader(f"📄 Nội dung file: {selected_file}")
                
                # Close button
                if st.button("❌ Đóng nội dung", key="close_content", use_container_width=False):
                    del st.session_state['selected_file_to_view']
                    if f'file_content_{selected_file}' in st.session_state:
                        del st.session_state[f'file_content_{selected_file}']
                    st.rerun()
                
                st.text_area(
                    "Nội dung",
                    st.session_state[f'file_content_{selected_file}'],
                    height=400,
                    key=f"content_display_{selected_file}",
                    label_visibility="collapsed"
                )
                
                # Save text content button
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1:
                    saved_text_path = get_saved_text_path(selected_file, storage_dir)
                    if saved_text_path and saved_text_path.exists():
                        st.info(f"💾 Nội dung văn bản đã được lưu: {saved_text_path.name}")
                        with open(saved_text_path, 'r', encoding='utf-8') as f:
                            text_data = f.read()
                        key_base = f"download_text_content_{selected_file}_{datetime.now().isoformat()}"
                        unique_key = sanitize_key(key_base)
                        st.download_button(
                            label="💾 Tải xuống nội dung văn bản (.txt)",
                            data=text_data,
                            file_name=saved_text_path.name,
                            mime="text/plain",
                            key=unique_key,
                            use_container_width=True
                        )
                    else:
                        if st.button("💾 Lưu nội dung văn bản", key=f"save_text_content_{selected_file}", use_container_width=True):
                            saved_path = save_text_content(selected_file, st.session_state[f'file_content_{selected_file}'], storage_dir)
                            if saved_path:
                                st.success(f"✅ Đã lưu nội dung văn bản vào: {saved_path.name}")
                                st.rerun()
                
                # Store content for AI assistant
                if 'uploaded_documents_content' not in st.session_state:
                    st.session_state['uploaded_documents_content'] = {}
                st.session_state['uploaded_documents_content'][selected_file] = st.session_state[f'file_content_{selected_file}']
    else:
        st.info("Chưa có tài liệu nào được upload. Hãy upload file ở trên.")

# ==================== STEP TEMPLATE FILES FUNCTIONS ====================

def init_step_templates_storage(step_num):
    """Initialize storage directory for step template files"""
    storage_dir = Path(f"step_templates/step_{step_num}")
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def save_step_template_info(step_num, filename, file_type, storage_dir):
    """Save step template file metadata to JSON"""
    metadata_file = storage_dir / "metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = []
    
    # Generate unique ID for this file
    file_id = str(uuid.uuid4())[:8]
    
    file_info = {
        'id': file_id,  # Add unique ID
        'filename': filename,
        'file_type': file_type,
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_path': str(storage_dir / filename)
    }
    
    metadata.append(file_info)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_info

def load_step_template_metadata(storage_dir):
    """Load step template file metadata"""
    metadata_file = storage_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def delete_step_template_file(step_num, filename, storage_dir):
    """Delete step template file and its metadata"""
    metadata_file = storage_dir / "metadata.json"
    
    if not metadata_file.exists():
        return False
    
    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find and remove file from metadata
        file_info = None
        updated_metadata = []
        for info in metadata:
            if info['filename'] == filename:
                file_info = info
            else:
                updated_metadata.append(info)
        
        if file_info:
            # Delete physical file
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Update metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(updated_metadata, f, ensure_ascii=False, indent=2)
            
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi khi xóa file: {str(e)}")
        return False

def init_substep_templates_storage(step_num, substep_code):
    """Initialize storage directory for substep template files"""
    storage_dir = Path(f"step_templates/step_{step_num}/{substep_code}")
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def save_substep_template_info(step_num, substep_code, filename, file_type, storage_dir):
    """Save substep template file metadata to JSON"""
    metadata_file = storage_dir / "metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = []
    
    # Generate unique ID for this file
    file_id = str(uuid.uuid4())[:8]
    
    file_info = {
        'id': file_id,  # Add unique ID
        'filename': filename,
        'file_type': file_type,
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_path': str(storage_dir / filename)
    }
    
    metadata.append(file_info)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_info

def load_substep_template_metadata(storage_dir):
    """Load substep template file metadata"""
    metadata_file = storage_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def delete_substep_template_file(step_num, substep_code, filename, storage_dir):
    """Delete substep template file and its metadata"""
    metadata_file = storage_dir / "metadata.json"
    
    if not metadata_file.exists():
        return False
    
    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find and remove file from metadata
        file_info = None
        updated_metadata = []
        for info in metadata:
            if info['filename'] == filename:
                file_info = info
            else:
                updated_metadata.append(info)
        
        if file_info:
            # Delete physical file
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Update metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(updated_metadata, f, ensure_ascii=False, indent=2)
            
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi khi xóa file: {str(e)}")
        return False

def render_substep_templates(step_num, substep_code):
    """Render substep template file upload and management section"""
    st.markdown(f"**📎 File mẫu soạn thảo cho {substep_code}**")
    
    storage_dir = init_substep_templates_storage(step_num, substep_code)
    
    # Initialize widget counter in session state for unique keys
    widget_counter_key = f"widget_counter_{step_num}_{substep_code}"
    if widget_counter_key not in st.session_state:
        st.session_state[widget_counter_key] = 0
    
    # Upload section
    uploaded_files = st.file_uploader(
        f"Upload file mẫu cho {substep_code}",
        type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls'],
        help="Hỗ trợ các định dạng: PDF, Word, Text, Excel. Có thể upload nhiều file cùng lúc.",
        accept_multiple_files=True,
        key=f"substep_template_upload_{step_num}_{substep_code}"
    )
    
    # Initialize session state for tracking uploaded files
    upload_key = f"substep_uploaded_{step_num}_{substep_code}"
    if upload_key not in st.session_state:
        st.session_state[upload_key] = []
    
    # Check if new files were uploaded
    if uploaded_files and len(uploaded_files) > 0:
        # Get list of new file names (not yet processed)
        current_file_names = [f.name for f in uploaded_files]
        processed_files = st.session_state[upload_key]
        new_files = [f for f in uploaded_files if f.name not in processed_files]
        
        if new_files:
            # Handle multiple files
            saved_files = []
            for uploaded_file in new_files:
                try:
                    # Check if file already exists
                    file_path = storage_dir / uploaded_file.name
                    if file_path.exists():
                        st.warning(f"⚠️ File {uploaded_file.name} đã tồn tại, sẽ được ghi đè.")
                    
                    # Save file
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get file type
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    # Save metadata
                    file_info = save_substep_template_info(step_num, substep_code, uploaded_file.name, file_type, storage_dir)
                    saved_files.append(uploaded_file.name)
                    # Mark as processed
                    st.session_state[upload_key].append(uploaded_file.name)
                except Exception as e:
                    st.error(f"❌ Lỗi khi upload file {uploaded_file.name}: {str(e)}")
            
            if saved_files:
                if len(saved_files) == 1:
                    st.success(f"✅ Đã upload thành công: {saved_files[0]}")
                    # Show download button for just uploaded file
                    uploaded_file = new_files[0]
                    file_path = storage_dir / uploaded_file.name
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    col_up1, col_up2 = st.columns([3, 1])
                    with col_up2:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            widget_uuid = str(uuid.uuid4())[:12]
                            unique_key = f"download_uploaded_substep_{step_num}_{substep_code}_{widget_uuid}"
                            st.download_button(
                                label="⬇️ Tải xuống file vừa upload",
                                data=file_data,
                                file_name=uploaded_file.name,
                                mime=file_type,
                                key=unique_key,
                                use_container_width=True
                            )
                else:
                    st.success(f"✅ Đã upload thành công {len(saved_files)} file: {', '.join(saved_files)}")
                    # Show download buttons for all uploaded files
                    st.markdown("**Tải xuống các file vừa upload:**")
                    cols = st.columns(min(len(saved_files), 3))
                    for idx, filename in enumerate(saved_files):
                        uploaded_file = new_files[idx]
                        file_path = storage_dir / uploaded_file.name
                        file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                        with cols[idx % 3]:
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                                widget_uuid = str(uuid.uuid4())[:12]
                                unique_key = f"download_uploaded_substep_{step_num}_{substep_code}_{idx}_{widget_uuid}"
                                st.download_button(
                                    label=f"⬇️ {filename[:20]}...",
                                    data=file_data,
                                    file_name=filename,
                                    mime=file_type,
                                    key=unique_key,
                                    use_container_width=True
                                )
                st.rerun()
    elif uploaded_files is not None and len(uploaded_files) == 0:
        # Reset processed files list when uploader is cleared
        st.session_state[upload_key] = []
    
    # File list
    metadata = load_substep_template_metadata(storage_dir)
    
    if metadata:
        # Remove duplicates based on file_path to avoid duplicate keys
        seen_paths = set()
        unique_metadata = []
        for file_info in metadata:
            file_path = file_info.get('file_path', '')
            if file_path and file_path not in seen_paths:
                seen_paths.add(file_path)
                unique_metadata.append(file_info)
        metadata = unique_metadata
        
        # Reverse to show newest first
        metadata.reverse()
        
        # Reset widget counter at the start of rendering file list
        st.session_state[widget_counter_key] = 0
        
        st.markdown(f"*Danh sách file mẫu ({len(metadata)} file):*")
        
        for idx, file_info in enumerate(metadata):
            file_path_obj = Path(file_info['file_path'])
            file_exists = file_path_obj.exists()
            
            # Increment widget counter for each file to ensure unique keys
            st.session_state[widget_counter_key] += 1
            widget_num = st.session_state[widget_counter_key]
            
            # Create a stable unique identifier using file_path hash + widget counter
            file_path_str = str(file_path_obj)
            file_path_hash = hashlib.md5(file_path_str.encode()).hexdigest()[:12]
            unique_id = f"{file_path_hash}_{widget_num}"
            
            col_info, col_download, col_delete = st.columns([3, 1, 1])
            
            with col_info:
                status_icon = "✅" if file_exists else "⚠️"
                st.write(f"{status_icon} **{file_info['filename']}** ({file_info['upload_date']})")
            
            with col_download:
                if file_exists:
                    with open(file_path_obj, 'rb') as f:
                        # Create unique key using file_path hash + widget counter
                        unique_key = f"dl_substep_{step_num}_{substep_code}_{unique_id}"
                        st.download_button(
                            label="📥 Tải",
                            data=f.read(),
                            file_name=file_info['filename'],
                            mime=file_info.get('file_type', 'application/octet-stream'),
                            key=unique_key,
                            use_container_width=True
                        )
            
            with col_delete:
                delete_key = f"del_substep_{step_num}_{substep_code}_{unique_id}"
                if st.button("🗑️ Xóa", key=delete_key, use_container_width=True):
                    if delete_substep_template_file(step_num, substep_code, file_info['filename'], storage_dir):
                        st.success(f"✅ Đã xóa: {file_info['filename']}")
                        st.rerun()

def render_step_templates(step_num):
    """Render step template file upload and management section"""
    st.markdown("---")
    st.subheader("📎 File mẫu soạn thảo")
    
    storage_dir = init_step_templates_storage(step_num)
    
    # Upload section
    uploaded_files = st.file_uploader(
        f"Upload file mẫu cho Bước {step_num}",
        type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls'],
        help="Hỗ trợ các định dạng: PDF, Word, Text, Excel. Có thể upload nhiều file cùng lúc.",
        accept_multiple_files=True,
        key=f"step_template_upload_{step_num}"
    )
    
    # Initialize session state for tracking uploaded files
    upload_key = f"step_uploaded_{step_num}"
    if upload_key not in st.session_state:
        st.session_state[upload_key] = []
    
    # Check if new files were uploaded
    if uploaded_files and len(uploaded_files) > 0:
        # Get list of new file names (not yet processed)
        processed_files = st.session_state[upload_key]
        new_files = [f for f in uploaded_files if f.name not in processed_files]
        
        if new_files:
            # Handle multiple files
            saved_files = []
            for uploaded_file in new_files:
                try:
                    # Check if file already exists
                    file_path = storage_dir / uploaded_file.name
                    if file_path.exists():
                        st.warning(f"⚠️ File {uploaded_file.name} đã tồn tại, sẽ được ghi đè.")
                    
                    # Save file
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get file type
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    # Save metadata
                    file_info = save_step_template_info(step_num, uploaded_file.name, file_type, storage_dir)
                    saved_files.append(uploaded_file.name)
                    # Mark as processed
                    st.session_state[upload_key].append(uploaded_file.name)
                except Exception as e:
                    st.error(f"❌ Lỗi khi upload file {uploaded_file.name}: {str(e)}")
            
            if saved_files:
                if len(saved_files) == 1:
                    st.success(f"✅ Đã upload thành công: {saved_files[0]}")
                    # Show download button for just uploaded file
                    uploaded_file = new_files[0]
                    file_path = storage_dir / uploaded_file.name
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    col_up1, col_up2 = st.columns([3, 1])
                    with col_up2:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            widget_uuid = str(uuid.uuid4())[:12]
                            unique_key = f"download_uploaded_step_{step_num}_{widget_uuid}"
                            st.download_button(
                                label="⬇️ Tải xuống file vừa upload",
                                data=file_data,
                                file_name=uploaded_file.name,
                                mime=file_type,
                                key=unique_key,
                                use_container_width=True
                            )
                else:
                    st.success(f"✅ Đã upload thành công {len(saved_files)} file: {', '.join(saved_files)}")
                    # Show download buttons for all uploaded files
                    st.markdown("**Tải xuống các file vừa upload:**")
                    cols = st.columns(min(len(saved_files), 3))
                    for idx, filename in enumerate(saved_files):
                        uploaded_file = new_files[idx]
                        file_path = storage_dir / uploaded_file.name
                        file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                        with cols[idx % 3]:
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                                widget_uuid = str(uuid.uuid4())[:12]
                                unique_key = f"download_uploaded_step_{step_num}_{idx}_{widget_uuid}"
                                st.download_button(
                                    label=f"⬇️ {filename[:20]}...",
                                    data=file_data,
                                    file_name=filename,
                                    mime=file_type,
                                    key=unique_key,
                                    use_container_width=True
                                )
                st.rerun()
    elif uploaded_files is not None and len(uploaded_files) == 0:
        # Reset processed files list when uploader is cleared
        st.session_state[upload_key] = []
    
    # File list
    metadata = load_step_template_metadata(storage_dir)
    
    if metadata:
        # Reverse to show newest first
        metadata.reverse()
        
        st.markdown(f"**Danh sách file mẫu đã upload ({len(metadata)} file):**")
        
        for idx, file_info in enumerate(metadata):
            file_path_obj = Path(file_info['file_path'])
            file_exists = file_path_obj.exists()
            
            col_info, col_actions = st.columns([4, 1])
            
            with col_info:
                status_icon = "✅" if file_exists else "⚠️"
                st.markdown(f"""
                <div style="background: #f0f2f6; padding: 0.8rem; border-radius: 5px; margin: 0.3rem 0; border-left: 3px solid #4CAF50;">
                    <strong>{status_icon} {file_info['filename']}</strong><br>
                    <small style="color: #666;">📅 Upload: {file_info['upload_date']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_actions:
                if file_exists:
                    with open(file_path_obj, "rb") as f:
                        file_data = f.read()
                    # Use file_path hash for uniqueness
                    file_path_hash = hashlib.md5(str(file_path_obj).encode()).hexdigest()[:16]
                    key_base = f"dl_template_{step_num}_{file_path_hash}_{idx}"
                    unique_key = sanitize_key(key_base)
                    st.download_button(
                        "⬇️",
                        data=file_data,
                        file_name=file_info['filename'],
                        mime=file_info['file_type'],
                        key=unique_key,
                        use_container_width=True,
                        help="Tải xuống"
                    )
                else:
                    st.button("⬇️", key=f"dl_disabled_{step_num}_{idx}", disabled=True, use_container_width=True, help="File không tồn tại")
                
                file_path_hash = hashlib.md5(str(file_path_obj).encode()).hexdigest()[:16]
                del_key_base = f"del_template_{step_num}_{file_path_hash}_{idx}"
                del_key = sanitize_key(del_key_base)
                if st.button("🗑️", key=del_key, use_container_width=True, help="Xóa"):
                    if delete_step_template_file(step_num, file_info['filename'], storage_dir):
                        st.success(f"✅ Đã xóa file: {file_info['filename']}")
                        st.rerun()
                    else:
                        st.error(f"❌ Không thể xóa file: {file_info['filename']}")
    else:
        st.info("Chưa có file mẫu nào được upload cho bước này.")

# ==================== COMPLETED FILES FUNCTIONS ====================

def init_completed_files_storage(step_num, substep_code=None):
    """Initialize storage directory for completed files"""
    if substep_code:
        storage_dir = Path(f"completed_files/step_{step_num}/{substep_code}")
    else:
        storage_dir = Path(f"completed_files/step_{step_num}")
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir

def save_completed_file_info(step_num, filename, file_type, storage_dir, substep_code=None):
    """Save completed file metadata to JSON"""
    metadata_file = storage_dir / "metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = []
    
    # Generate unique ID for this file
    file_id = str(uuid.uuid4())[:8]
    
    file_info = {
        'id': file_id,  # Add unique ID
        'filename': filename,
        'file_type': file_type,
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_path': str(storage_dir / filename)
    }
    
    metadata.append(file_info)
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return file_info

def load_completed_file_metadata(storage_dir):
    """Load completed file metadata"""
    metadata_file = storage_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def delete_completed_file(step_num, filename, storage_dir, substep_code=None):
    """Delete completed file and its metadata"""
    metadata_file = storage_dir / "metadata.json"
    
    if not metadata_file.exists():
        return False
    
    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Find and remove file from metadata
        file_info = None
        updated_metadata = []
        for info in metadata:
            if info['filename'] == filename:
                file_info = info
            else:
                updated_metadata.append(info)
        
        if file_info:
            # Delete physical file
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Update metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(updated_metadata, f, ensure_ascii=False, indent=2)
            
            return True
        return False
    except Exception as e:
        st.error(f"Lỗi khi xóa file: {str(e)}")
        return False

def render_completed_file_upload(step_num, substep_code=None, substep_content=""):
    """Render completed file upload section for step or substep"""
    if substep_code:
        title = f"📎 File hoàn thành cho {substep_code}"
        key_prefix = f"completed_file_{step_num}_{substep_code}"
        storage_dir = init_completed_files_storage(step_num, substep_code)
    else:
        title = f"📎 File hoàn thành cho Bước {step_num}"
        key_prefix = f"completed_file_step_{step_num}"
        storage_dir = init_completed_files_storage(step_num)
    
    st.markdown(f"**{title}**")
    
    # Upload section
    uploaded_files = st.file_uploader(
        f"Upload file hoàn thành",
        type=['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'],
        help="Hỗ trợ các định dạng: PDF, Word, Text, Excel, Image. Có thể upload nhiều file cùng lúc.",
        accept_multiple_files=True,
        key=f"{key_prefix}_upload"
    )
    
    # Initialize session state for tracking uploaded files
    upload_key = f"completed_uploaded_{key_prefix}"
    if upload_key not in st.session_state:
        st.session_state[upload_key] = []
    
    # Check if new files were uploaded
    if uploaded_files and len(uploaded_files) > 0:
        # Get list of new file names (not yet processed)
        processed_files = st.session_state[upload_key]
        new_files = [f for f in uploaded_files if f.name not in processed_files]
        
        if new_files:
            # Handle multiple files
            saved_files = []
            for uploaded_file in new_files:
                try:
                    # Check if file already exists
                    file_path = storage_dir / uploaded_file.name
                    if file_path.exists():
                        st.warning(f"⚠️ File {uploaded_file.name} đã tồn tại, sẽ được ghi đè.")
                    
                    # Save file
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Get file type
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    # Save metadata
                    file_info = save_completed_file_info(step_num, uploaded_file.name, file_type, storage_dir, substep_code)
                    saved_files.append(uploaded_file.name)
                    # Mark as processed
                    st.session_state[upload_key].append(uploaded_file.name)
                except Exception as e:
                    st.error(f"❌ Lỗi khi upload file {uploaded_file.name}: {str(e)}")
            
            if saved_files:
                if len(saved_files) == 1:
                    st.success(f"✅ Đã upload file hoàn thành: {saved_files[0]}")
                    # Show download button for just uploaded file
                    uploaded_file = new_files[0]
                    file_path = storage_dir / uploaded_file.name
                    file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                    
                    col_up1, col_up2 = st.columns([3, 1])
                    with col_up2:
                        with open(file_path, "rb") as f:
                            file_data = f.read()
                            widget_uuid = str(uuid.uuid4())[:12]
                            unique_key = f"download_uploaded_completed_{key_prefix}_{widget_uuid}"
                            st.download_button(
                                label="⬇️ Tải xuống file vừa upload",
                                data=file_data,
                                file_name=uploaded_file.name,
                                mime=file_type,
                                key=unique_key,
                                use_container_width=True
                            )
                else:
                    st.success(f"✅ Đã upload thành công {len(saved_files)} file hoàn thành: {', '.join(saved_files)}")
                    # Show download buttons for all uploaded files
                    st.markdown("**Tải xuống các file vừa upload:**")
                    cols = st.columns(min(len(saved_files), 3))
                    for idx, filename in enumerate(saved_files):
                        uploaded_file = new_files[idx]
                        file_path = storage_dir / uploaded_file.name
                        file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'unknown'
                        with cols[idx % 3]:
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                                widget_uuid = str(uuid.uuid4())[:12]
                                unique_key = f"download_uploaded_completed_{key_prefix}_{idx}_{widget_uuid}"
                                st.download_button(
                                    label=f"⬇️ {filename[:20]}...",
                                    data=file_data,
                                    file_name=filename,
                                    mime=file_type,
                                    key=unique_key,
                                    use_container_width=True
                                )
                st.rerun()
    elif uploaded_files is not None and len(uploaded_files) == 0:
        # Reset processed files list when uploader is cleared
        st.session_state[upload_key] = []
    
    # File list
    metadata = load_completed_file_metadata(storage_dir)
    
    if metadata:
        st.markdown("*Các file đã upload:*")
        # Reverse to show newest first
        metadata.reverse()
        for idx, file_info in enumerate(metadata):
            file_path = Path(file_info['file_path'])
            file_exists = file_path.exists()
            
            col_file1, col_file2, col_file3 = st.columns([3, 1, 1])
            with col_file1:
                status_icon = "✅" if file_exists else "❌"
                st.write(f"{status_icon} **{file_info['filename']}** ({file_info['upload_date']})")
            
            with col_file2:
                if file_exists:
                    with open(file_path, 'rb') as f:
                        # Use file_path hash for uniqueness
                        file_path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:16]
                        key_base = f"download_{key_prefix}_{file_path_hash}_{idx}"
                        unique_key = sanitize_key(key_base)
                        st.download_button(
                            label="📥 Tải",
                            data=f.read(),
                            file_name=file_info['filename'],
                            mime=file_info.get('file_type', 'application/octet-stream'),
                            key=unique_key,
                            use_container_width=True
                        )
            
            with col_file3:
                file_path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:16]
                delete_key_base = f"delete_{key_prefix}_{file_path_hash}_{idx}"
                delete_key = sanitize_key(delete_key_base)
                if st.button("🗑️ Xóa", key=delete_key, use_container_width=True):
                    if delete_completed_file(step_num, file_info['filename'], storage_dir, substep_code):
                        st.success(f"✅ Đã xóa: {file_info['filename']}")
                        st.rerun()

# ==================== CHECKLIST & STATUS FUNCTIONS ====================

CHECKLIST_STATUS_FILE = Path("checklist_status.json")

def save_checklist_status():
    """Save checklist status to JSON file"""
    try:
        status_data = {
            'step_status': st.session_state.get('step_status', {}),
            'substep_status': st.session_state.get('substep_status', {})
        }
        with open(CHECKLIST_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Lỗi khi lưu trạng thái: {str(e)}")
        return False

def load_checklist_status():
    """Load checklist status from JSON file"""
    if CHECKLIST_STATUS_FILE.exists():
        try:
            with open(CHECKLIST_STATUS_FILE, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
                return status_data.get('step_status', {}), status_data.get('substep_status', {})
        except Exception as e:
            st.warning(f"Lỗi khi đọc trạng thái: {str(e)}")
            return {}, {}
    return {}, {}

def init_checklist_status(steps):
    """Initialize checklist and status for steps"""
    # Load from file first
    if 'checklist_loaded' not in st.session_state:
        step_status_from_file, substep_status_from_file = load_checklist_status()
        st.session_state['step_status'] = step_status_from_file
        st.session_state['substep_status'] = substep_status_from_file
        st.session_state['checklist_loaded'] = True
    
    # Initialize missing steps/substeps
    if 'step_status' not in st.session_state:
        st.session_state['step_status'] = {}
    
    for step_num in steps.keys():
        if step_num not in st.session_state['step_status']:
            st.session_state['step_status'][step_num] = {
                'status': 'not_started',  # 'not_started', 'in_progress', 'completed'
                'notes': ''
            }
    
    if 'substep_status' not in st.session_state:
        st.session_state['substep_status'] = {}
    
    for step_num, step_data in steps.items():
        for substep in step_data['substeps']:
            substep_key = f"{step_num}_{substep['code']}"
            if substep_key not in st.session_state['substep_status']:
                st.session_state['substep_status'][substep_key] = {
                    'status': 'not_started',
                    'notes': ''
                }
    
    # Save after initialization
    save_checklist_status()

def get_status_label(status):
    """Get Vietnamese label for status"""
    status_map = {
        'not_started': '⏸️ Chưa thực hiện',
        'in_progress': '🔄 Đang thực hiện',
        'completed': '✅ Hoàn thành'
    }
    return status_map.get(status, status)

def calculate_overall_progress(steps):
    """Calculate overall progress percentage"""
    if 'step_status' not in st.session_state:
        return 0
    
    total_steps = len(steps)
    if total_steps == 0:
        return 0
    
    completed_steps = sum(
        1 for status in st.session_state['step_status'].values()
        if status.get('status') == 'completed'
    )
    
    return int((completed_steps / total_steps) * 100)

def render_step_checklist(step_num, step_data):
    """Render checklist for a specific step"""
    # Ensure step status is initialized
    if 'step_status' not in st.session_state:
        st.session_state['step_status'] = {}
    if step_num not in st.session_state['step_status']:
        st.session_state['step_status'][step_num] = {
            'status': 'not_started',
            'notes': ''
        }
    
    # Ensure substep statuses are initialized
    if 'substep_status' not in st.session_state:
        st.session_state['substep_status'] = {}
    for substep in step_data['substeps']:
        substep_key = f"{step_num}_{substep['code']}"
        if substep_key not in st.session_state['substep_status']:
            st.session_state['substep_status'][substep_key] = {
                'status': 'not_started',
                'notes': ''
            }
    
    step_status = st.session_state['step_status'][step_num]
    
    st.markdown("---")
    st.markdown("### ✅ Checklist & Trạng thái thực hiện")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Status selector
        status = st.selectbox(
            f"Trạng thái Bước {step_num}",
            options=['not_started', 'in_progress', 'completed'],
            format_func=get_status_label,
            index=['not_started', 'in_progress', 'completed'].index(step_status['status']),
            key=f"step_status_{step_num}"
        )
        st.session_state['step_status'][step_num]['status'] = status
        save_checklist_status()  # Save when status changes
        
        # Notes
        notes = st.text_area(
            f"Ghi chú cho Bước {step_num}",
            value=step_status['notes'],
            height=100,
            key=f"step_notes_{step_num}"
        )
        st.session_state['step_status'][step_num]['notes'] = notes
        save_checklist_status()  # Save when notes change
    
    with col2:
        st.write(f"**Trạng thái hiện tại:**")
        st.markdown(f"### {get_status_label(status)}")
    
    # Show completed file upload section if step is completed
    if status == 'completed':
        render_completed_file_upload(step_num)
    
    # Substeps checklist
    if step_data['substeps']:
        st.markdown("**Chi tiết công việc:**")
        for substep in step_data['substeps']:
            substep_key = f"{step_num}_{substep['code']}"
            if substep_key not in st.session_state['substep_status']:
                st.session_state['substep_status'][substep_key] = {
                    'status': 'not_started',
                    'notes': ''
                }
            substep_status = st.session_state['substep_status'][substep_key]
            
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"- **{substep['code']}:** {substep['content'][:100]}{'...' if len(substep['content']) > 100 else ''}")
            with col_b:
                substep_status_val = st.selectbox(
                    f"Trạng thái {substep['code']}",
                    options=['not_started', 'in_progress', 'completed'],
                    format_func=get_status_label,
                    index=['not_started', 'in_progress', 'completed'].index(substep_status['status']),
                    key=f"substep_status_{substep_key}"
                )
                st.session_state['substep_status'][substep_key]['status'] = substep_status_val
                save_checklist_status()  # Save when substep status changes
            
            # Show completed file upload section if substep is completed
            if substep_status_val == 'completed':
                st.markdown("<div style='margin-left: 2rem; padding: 0.5rem; background: #f8f9fa; border-radius: 5px; margin-top: 0.5rem; margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
                render_completed_file_upload(step_num, substep['code'], substep['content'])
                st.markdown("</div>", unsafe_allow_html=True)

def render_checklist_status(steps):
    """Render checklist and status management page"""
    st.markdown('<div class="main-header">✅ CHECKLIST & TRẠNG THÁI THỰC HIỆN</div>', unsafe_allow_html=True)
    
    init_checklist_status(steps)
    
    # Overall progress
    progress_percentage = calculate_overall_progress(steps)
    st.subheader("📊 Tiến độ tổng thể")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress_percentage / 100)
    with col2:
        st.metric("Tiến độ", f"{progress_percentage}%")
    
    # Status legend
    st.markdown("""
    <div style="background: #f0f2f6; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        <strong>Chú thích trạng thái:</strong><br>
        ⏸️ Chưa thực hiện | 🔄 Đang thực hiện | ✅ Hoàn thành
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Steps checklist
    st.subheader("📋 Checklist các bước")
    
    for step_num in sorted(steps.keys()):
        step_data = steps[step_num]
        step_status = st.session_state['step_status'][step_num]
        
        with st.expander(f"**BƯỚC {step_num}:** {step_data['title']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Status selector
                status = st.selectbox(
                    f"Trạng thái Bước {step_num}",
                    options=['not_started', 'in_progress', 'completed'],
                    format_func=get_status_label,
                    index=['not_started', 'in_progress', 'completed'].index(step_status['status']),
                    key=f"step_status_{step_num}"
                )
                st.session_state['step_status'][step_num]['status'] = status
                
                # Notes
                notes = st.text_area(
                    f"Ghi chú cho Bước {step_num}",
                    value=step_status['notes'],
                    height=100,
                    key=f"step_notes_{step_num}"
                )
                st.session_state['step_status'][step_num]['notes'] = notes
            
            with col2:
                st.write(f"**Trạng thái hiện tại:**")
                st.markdown(f"### {get_status_label(status)}")
                st.write(f"**Số công việc:** {len(step_data['substeps'])}")
            
            # Substeps checklist
            if step_data['substeps']:
                st.markdown("**Chi tiết công việc:**")
                for substep in step_data['substeps']:
                    substep_key = f"{step_num}_{substep['code']}"
                    substep_status = st.session_state['substep_status'][substep_key]
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"- {substep['code']}: {substep['content'][:80]}...")
                    with col_b:
                        substep_status_val = st.selectbox(
                            f"Trạng thái {substep['code']}",
                            options=['not_started', 'in_progress', 'completed'],
                            format_func=get_status_label,
                            index=['not_started', 'in_progress', 'completed'].index(substep_status['status']),
                            key=f"substep_status_{substep_key}"
                        )
                        st.session_state['substep_status'][substep_key]['status'] = substep_status_val
                save_checklist_status()  # Save when substep status changes

# ==================== AI ASSISTANT FUNCTIONS ====================

def save_api_key_to_env(api_key):
    """Save API key to .env file. If api_key is empty, remove OPENAI_API_KEY from .env"""
    env_file = Path('.env')
    try:
        # Read existing .env file if exists
        env_lines = []
        found_openai_key = False
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    original_line = line.rstrip('\n\r')
                    line_stripped = original_line.strip()
                    # Skip OPENAI_API_KEY line if we want to remove it (api_key is empty) or replace it
                    if line_stripped.startswith('OPENAI_API_KEY='):
                        found_openai_key = True
                        if api_key:  # Only keep the line if we have a new key to save
                            env_lines.append(f"OPENAI_API_KEY={api_key}")
                        # Otherwise skip this line (removing it)
                    else:
                        # Keep all other lines as-is
                        env_lines.append(original_line)
        
        # If OPENAI_API_KEY wasn't found and we want to add it
        if api_key and not found_openai_key:
            env_lines.append(f"OPENAI_API_KEY={api_key}")
        elif api_key and found_openai_key:
            # Key was found and replaced above, nothing to do
            pass
        
        # Write back to .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            for line in env_lines:
                f.write(line + '\n')
        
        return True
    except Exception as e:
        st.error(f"Lỗi khi lưu API key: {str(e)}")
        return False

def load_api_key_from_env():
    """Load API key from .env file"""
    env_file = Path('.env')
    try:
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OPENAI_API_KEY='):
                        return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return None

def init_openai_client():
    """Initialize OpenAI client - checks session state first, then .env file, then environment variable"""
    if not OPENAI_AVAILABLE:
        return None
    
    # Check session state first (user input)
    api_key = st.session_state.get('openai_api_key', '')
    
    # If not in session state, check .env file
    if not api_key:
        api_key = load_api_key_from_env()
    
    # If still not found, check environment variable
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY', '')
    
    if not api_key:
        return None
    
    try:
        return openai.OpenAI(api_key=api_key)
    except Exception:
        return None

def get_ai_response(prompt, context=""):
    """Get response from OpenAI API"""
    client = init_openai_client()
    if not client:
        return None
    
    try:
        full_prompt = f"{context}\n\nCâu hỏi: {prompt}\n\nTrả lời bằng tiếng Việt:"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI chuyên về quy trình đầu tư và dự án. Bạn CÓ THỂ đọc và phân tích nội dung các tài liệu được cung cấp trong ngữ cảnh. Hãy trả lời câu hỏi dựa trên ngữ cảnh và tài liệu được cung cấp. Luôn trả lời bằng tiếng Việt. Nếu có tài liệu trong ngữ cảnh, hãy tham khảo và trích dẫn nội dung từ tài liệu đó."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Lỗi khi gọi API: {str(e)}"

def render_ai_assistant(steps):
    """Render AI assistant page"""
    st.markdown('<div class="main-header">🤖 TRỢ LÝ AI</div>', unsafe_allow_html=True)
    
    if not OPENAI_AVAILABLE:
        st.warning("⚠️ Chưa cài đặt thư viện OpenAI. Cài đặt bằng lệnh: pip install openai python-dotenv")
        st.info("💡 Để sử dụng trợ lý AI, bạn cần:\n1. Cài đặt: pip install openai python-dotenv\n2. Nhập API key bên dưới hoặc tạo file .env với OPENAI_API_KEY=your_api_key")
        return
    
    # API Key input section
    st.subheader("🔑 Cấu hình API Key")
    
    # Initialize session state for API key
    if 'openai_api_key' not in st.session_state:
        # Try to load from .env file first
        env_key = load_api_key_from_env()
        if not env_key:
            # Fallback to environment variable
            env_key = os.getenv('OPENAI_API_KEY', '')
        st.session_state['openai_api_key'] = env_key
    
    # Load saved API key from .env for display
    saved_api_key = load_api_key_from_env()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.get('openai_api_key', ''),
            type="password",
            help="Nhập API key của bạn. Lấy từ: https://platform.openai.com/api-keys",
            placeholder="sk-...",
            key="api_key_input"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("💾 Lưu vào file", use_container_width=True):
            if api_key_input and api_key_input.startswith('sk-'):
                if save_api_key_to_env(api_key_input):
                    st.session_state['openai_api_key'] = api_key_input
                    st.success("✅ Đã lưu API key vào file .env thành công!")
                    st.rerun()
            else:
                st.error("❌ API key không hợp lệ. API key phải bắt đầu bằng 'sk-'")
    
    # Show saved API key section
    if saved_api_key:
        st.markdown("---")
        st.markdown("### 📋 API Key đã lưu trong file")
        col_display1, col_display2 = st.columns([4, 1])
        with col_display1:
            # Show full API key for easy copy (visible text input)
            st.text_input(
                "API Key đã lưu (click để chọn và copy)",
                value=saved_api_key,
                type="default",
                key="saved_api_key_display",
                help="Click vào ô này để chọn toàn bộ và copy API key (Ctrl+C hoặc Cmd+C)"
            )
        with col_display2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🗑️ Xóa", help="Xóa API key khỏi file .env", use_container_width=True):
                if save_api_key_to_env(''):
                    st.session_state['openai_api_key'] = ''
                    st.success("✅ Đã xóa API key khỏi file .env")
                    st.rerun()
    
    # Show current session API key status
    if st.session_state.get('openai_api_key'):
        masked_key = st.session_state['openai_api_key'][:7] + "..." + st.session_state['openai_api_key'][-4:] if len(st.session_state['openai_api_key']) > 11 else "***"
        if saved_api_key and st.session_state['openai_api_key'] == saved_api_key:
            st.info(f"🔐 Đang sử dụng API key từ file .env: {masked_key}")
        else:
            st.info(f"🔐 API key tạm thời (chưa lưu vào file): {masked_key}")
    else:
        if not saved_api_key:
            st.warning("⚠️ Chưa có API key. Vui lòng nhập API key ở trên và nhấn 'Lưu vào file'")
    
    st.markdown("---")
    
    # Check if client can be initialized
    client = init_openai_client()
    if not client:
        st.error("❌ Không thể khởi tạo OpenAI client. Vui lòng kiểm tra API key.")
        st.info("💡 Lấy API key từ: https://platform.openai.com/api-keys")
        return
    
    # Build context from steps
    context = "Thông tin về quy trình:\n"
    for step_num in sorted(steps.keys()):
        step_data = steps[step_num]
        context += f"\nBước {step_num}: {step_data['title']}\n"
        context += f"Căn cứ pháp lý: {step_data['can_cu']}\n"
        if step_data.get('can_cu_tien_do'):
            context += f"Căn cứ tiến độ: {step_data['can_cu_tien_do']}\n"
    
    # Auto-load all uploaded documents for AI context
    storage_dir = init_file_storage()
    metadata = load_file_metadata(storage_dir)
    
    # Initialize uploaded_documents_content if not exists
    if 'uploaded_documents_content' not in st.session_state:
        st.session_state['uploaded_documents_content'] = {}
    
    # Load content for all uploaded files that haven't been loaded yet
    for file_info in metadata:
        filename = file_info['filename']
        if filename not in st.session_state['uploaded_documents_content']:
            file_path = Path(file_info['file_path'])
            if file_path.exists():
                text_content = extract_text_from_file(file_path, file_info['file_type'])
                if text_content:
                    st.session_state['uploaded_documents_content'][filename] = text_content
    
    # Add uploaded documents context
    if st.session_state['uploaded_documents_content']:
        context += "\n\n=== TÀI LIỆU ĐÃ UPLOAD (BẠN CẦN TRẢ LỜI DỰA TRÊN CÁC TÀI LIỆU NÀY) ===\n"
        for filename, content in st.session_state['uploaded_documents_content'].items():
            # Use first 5000 characters for better context
            context += f"\n--- Nội dung file: {filename} ---\n{content[:5000]}\n"
            if len(content) > 5000:
                context += f"... (còn {len(content) - 5000} ký tự nữa)\n"
        context += "\n=== KẾT THÚC TÀI LIỆU ===\n"
        context += "\nLƯU Ý: Bạn có thể đọc và trả lời câu hỏi dựa trên nội dung các tài liệu đã upload ở trên. Hãy tham khảo nội dung tài liệu để trả lời chính xác.\n"
    
    # Show info about loaded documents
    if st.session_state['uploaded_documents_content']:
        num_files = len(st.session_state['uploaded_documents_content'])
        total_chars = sum(len(content) for content in st.session_state['uploaded_documents_content'].values())
        st.success(f"✅ Đã tải {num_files} file vào bộ nhớ AI ({total_chars:,} ký tự). AI có thể đọc và trả lời dựa trên nội dung các file này.")
    else:
        st.info("💡 Chưa có file nào được tải vào bộ nhớ AI. Hãy upload file ở trang '📁 Tài liệu' và đọc nội dung để AI có thể sử dụng.")
    
    # Chat interface
    st.subheader("💬 Hỏi đáp với AI")
    
    # Initialize chat history
    if 'ai_chat_history' not in st.session_state:
        st.session_state['ai_chat_history'] = []
    
    # Display chat history
    for message in st.session_state['ai_chat_history']:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                st.markdown(f"<div style='background: #e3f2fd; padding: 1rem; border-radius: 8px; border-left: 4px solid #2196f3;'>🤖 <strong>Trợ lý AI:</strong><br>{message['content']}</div>", unsafe_allow_html=True)
    
    # Chat input
    user_query = st.chat_input("Nhập câu hỏi của bạn...")
    
    if user_query:
        # Add user message
        st.session_state['ai_chat_history'].append({'role': 'user', 'content': user_query})
        
        # Get AI response
        with st.spinner("🤖 AI đang suy nghĩ..."):
            ai_response = get_ai_response(user_query, context)
        
        if ai_response:
            st.session_state['ai_chat_history'].append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        else:
            st.error("Không thể nhận được phản hồi từ AI")
    
    st.markdown("---")

