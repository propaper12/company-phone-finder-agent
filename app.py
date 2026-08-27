import os
import sys
import time
import asyncio
import aiohttp
import pandas as pd
import streamlit as st

# Windows konsolu UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from excel_manager import ExcelManager
from async_engine import async_search_single_company

# Sayfa Yapılandırması
st.set_page_config(
    page_title="10K Şirket Telefon Bulucu Agent (Ultra Async)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6B7280;
        margin-bottom: 1.5rem;
    }
    .stProgress > div > div > div > div {
        background-color: #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# Session State
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "current_file" not in st.session_state:
    st.session_state.current_file = None
if "excel_manager" not in st.session_state:
    st.session_state.excel_manager = None

# Başlık
st.markdown('<div class="main-header">⚡ 10K Şirket Telefon Bulucu (Ultra Hızlı Asenkron Motor)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Non-blocking Asynchronous I/O ile 10.000 şirketi dakikalar içinde eşzamanlı tarayın.</div>', unsafe_allow_html=True)

# Yan Panel
with st.sidebar:
    st.header("⚙️ Ayarlar ve Veri Girişi")
    
    upload_option = st.radio("Dosya Seçim Yöntemi:", ["📤 Dosya Yükle", "📁 Klasörden Seç"])
    
    selected_file_path = None
    
    if upload_option == "📤 Dosya Yükle":
        uploaded_file = st.file_uploader("Excel veya CSV Dosyası Yükleyin", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            save_path = os.path.join(os.getcwd(), uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_file_path = save_path
    else:
        existing_files = [
            f for f in os.listdir('.') 
            if f.endswith(('.xlsx', '.xls', '.csv')) 
            and not f.endswith(('_telefon_sonuclari.xlsx', '_telefon_sonuclari.csv'))
        ]
        if existing_files:
            selected_filename = st.selectbox("Klasördeki Dosyayı Seçin:", existing_files)
            selected_file_path = os.path.join(os.getcwd(), selected_filename)
        else:
            st.warning("Klasörde uygun Excel/CSV dosyası bulunamadı.")

    st.markdown("---")
    st.subheader("⚡ Ultra Hız & Concurrency Ayarı")
    concurrency_limit = st.slider("Eşzamanlı İstek Sayısı (Concurrency)", min_value=10, max_value=80, value=40, step=5, help="Aynı anda internete kaç paralel istek gönderileceğini belirler. 30-50 önerilir.")
    deep_scan = st.checkbox("🌐 Web Sitelerine de Gir (Maksimum Başarı)", value=True)
    save_batch_size = st.slider("Diske Kaydetme Aralığı", min_value=20, max_value=100, value=50, step=10)

# Ana Gövde
if selected_file_path and os.path.exists(selected_file_path):
    if st.session_state.current_file != selected_file_path:
        st.session_state.current_file = selected_file_path
        st.session_state.excel_manager = ExcelManager(selected_file_path)

    mgr = st.session_state.excel_manager

    cols = list(mgr.df.columns)
    default_col = mgr.detect_company_column()
    default_idx = cols.index(default_col) if default_col in cols else 0
    
    col_select1, col_select2 = st.columns([2, 1])
    with col_select1:
        company_col = st.selectbox("🏢 Şirket Adı Sütunu:", cols, index=default_idx)
        mgr.company_col = company_col
    with col_select2:
        output_file_name = os.path.basename(mgr.output_file)
        st.text_input("💾 Çıktı Dosyası Adı:", value=output_file_name, disabled=True)

    pending_indices = mgr.get_pending_indices()
    unfound_indices = mgr.get_unfound_indices()
    total_rows = len(mgr.df)
    completed_rows = total_rows - len(pending_indices)
    
    found_count = len(mgr.df[mgr.df['Durum'] == 'Tamamlandı'])
    not_found_count = len(mgr.df[mgr.df['Durum'] == 'Bulunamadı'])

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("📊 Toplam Satır", f"{total_rows:,}")
    with m2:
        metric_processed = st.empty()
        metric_processed.metric("✅ İşlenen", f"{completed_rows:,}")
    with m3:
        metric_found = st.empty()
        metric_found.metric("📞 Bulunan Telefon", f"{found_count:,}")
    with m4:
        metric_not_found = st.empty()
        metric_not_found.metric("❌ Bulunamayan", f"{not_found_count:,}")
    with m5:
        metric_rate = st.empty()
        success_rate = (found_count / completed_rows * 100) if completed_rows > 0 else 0.0
        metric_rate.metric("🎯 Başarı Oranı", f"%{success_rate:.1f}")

    st.markdown("---")

    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.8, 1.5])
    
    with btn_col1:
        start_btn = st.button("🚀 Ultra Hızlı Taramayı Başlat", type="primary", use_container_width=True, disabled=st.session_state.is_running or len(pending_indices) == 0)
    with btn_col2:
        retry_unfound_btn = st.button(f"🔄 Bulunamayanları Tekrar Tara ({len(unfound_indices)})", type="secondary", use_container_width=True, disabled=st.session_state.is_running or len(unfound_indices) == 0)
    with btn_col3:
        stop_btn = st.button("⏹️ Durdur", type="secondary", use_container_width=True, disabled=not st.session_state.is_running)

    progress_bar = st.progress(completed_rows / total_rows if total_rows > 0 else 0)
    status_text = st.empty()

    st.subheader("📋 Canlı Veri Tablosu")
    table_placeholder = st.empty()
    table_placeholder.dataframe(mgr.df.head(300), use_container_width=True, height=330)

    if os.path.exists(mgr.output_file):
        with open(mgr.output_file, "rb") as f:
            st.download_button(
                label="📥 Güncellenmiş Excel Dosyasını İndir",
                data=f,
                file_name=os.path.basename(mgr.output_file),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    async def run_async_scanner(target_indices, is_retry=False):
        st.session_state.is_running = True
        status_text.info(f"⚡ Ultra Asenkron Motor Devrede: {concurrency_limit} eşzamanlı bağlantı ile taranıyor...")
        
        semaphore = asyncio.Semaphore(concurrency_limit)
        connector = aiohttp.TCPConnector(limit=concurrency_limit + 20, ttl_dns_cache=300)
        
        current_f = len(mgr.df[mgr.df['Durum'] == 'Tamamlandı'])
        current_nf = len(mgr.df[mgr.df['Durum'] == 'Bulunamadı'])
        done_count = 0
        start_t = time.time()

        async def worker(session, idx):
            nonlocal done_count, current_f, current_nf
            async with semaphore:
                company_name = str(mgr.df.at[idx, company_col])
                phone, url = await async_search_single_company(session, company_name, deep_scan=deep_scan)
                
                prev_status = mgr.df.at[idx, 'Durum']
                mgr.update_row(idx, phone, url)
                done_count += 1
                
                if phone:
                    if prev_status != 'Tamamlandı':
                        current_f += 1
                        if prev_status == 'Bulunamadı':
                            current_nf -= 1
                else:
                    if prev_status != 'Bulunamadı' and prev_status != 'Tamamlandı':
                        current_nf += 1
                        
                if done_count % save_batch_size == 0 or done_count == len(target_indices):
                    mgr.save()
                    
                if done_count % 5 == 0 or done_count == len(target_indices):
                    elapsed = time.time() - start_t
                    speed = done_count / elapsed if elapsed > 0 else 0
                    
                    metric_found.metric("📞 Bulunan Telefon", f"{current_f:,}")
                    metric_not_found.metric("❌ Bulunamayan", f"{max(0, current_nf):,}")
                    
                    tot = current_f + current_nf
                    rate = (current_f / tot * 100) if tot > 0 else 0.0
                    metric_rate.metric("🎯 Başarı Oranı", f"%{rate:.1f} ({speed:.1f} şirket/sn)")
                    
                    if not is_retry:
                        p_val = min(1.0, (completed_rows + done_count) / total_rows)
                        progress_bar.progress(p_val)
                        metric_processed.metric("✅ İşlenen", f"{(completed_rows + done_count):,}")

                if done_count % 25 == 0:
                    table_placeholder.dataframe(mgr.df.head(300), use_container_width=True, height=330)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [worker(session, idx) for idx in target_indices]
            await asyncio.gather(*tasks, return_exceptions=True)

        mgr.save()
        st.session_state.is_running = False
        status_text.success("🎉 Ultra Asenkron Tarama Tamamlandı! Excel kaydedildi.")

    if start_btn:
        asyncio.run(run_async_scanner(pending_indices, is_retry=False))
        st.rerun()

    if retry_unfound_btn:
        asyncio.run(run_async_scanner(unfound_indices, is_retry=True))
        st.rerun()

else:
    st.info("👈 Lütfen sol menüden bir Excel/CSV dosyası yükleyin veya mevcut bir dosyayı seçin.")
