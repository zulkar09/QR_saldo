import streamlit as st
import pandas as pd
import qrcode
import cv2
import numpy as np

# 1. INISIALISASI HALAMAN
st.set_page_config(page_title="Dompet Digital Ranting", page_icon="💳", layout="wide")

# 2. FUNGSI AKSES GOOGLE SHEETS
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1xD0dPE1Shl1ddpph4Nw4p3mDuuYmKqIM/edit?usp=drive_link&ouid=106632842841779642489&rtpof=true&sd=true"

@st.cache_data(ttl=0)
def ambil_data_sheets(url):
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        
        # Bersihkan nama kolom dari spasi liar agar tidak error
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal menghubungkan ke Google Sheets: {e}")
        return pd.DataFrame(columns=["ID", "Nama", "Saldo (Poin)"])

# Memuat data
df_anggota = ambil_data_sheets(URL_SHEETS)

# 3. ARSITEKTUR UI/UX PREMIUM
st.title("💳 Sistem Kasir & Dompet Digital Ranting")
st.write("Aplikasi kasir ramah lansia menggunakan QR Code fisik.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📸 Scan & Transaksi Kasir", "📋 Daftar Saldo Anggota", "🖨️ Cetak Kartu Baru"])

# ================= TAB 1: SCAN & TRANSAKSI =================
with tab1:
    st.subheader("Menu Transaksi Kasir")
    foto_kamera = st.camera_input("Arahkan QR Code Kartu Fisik Sesepuh ke Kamera")
    id_terdeteksi = None
    
    if foto_kamera:
        with st.spinner("Membaca kartu..."):
            try:
                file_bytes = np.asarray(bytearray(foto_kamera.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, 1)
                
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(img)
                
                if data:
                    # Ambil teks asli, hapus spasi di depan/belakang, dan jadikan huruf besar
                    id_terdeteksi = str(data).strip().upper()
                    st.info(f"🎯 Kamera Berhasil Membaca Teks: **`{id_terdeteksi}`**")
                else:
                    st.warning("⚠️ Kamera aktif, namun QR Code belum terbaca terang. Dekatkan sedikit atau pastikan tidak silau.")
            except Exception as e:
                st.error(f"Gagal memproses gambar kamera: {e}")
                
    st.write("### Detail Transaksi")
    col1, col2, col3 = st.columns(3)
    with col1:
        id_input = st.text_input("ID Anggota", value=id_terdeteksi if id_terdeteksi else "", placeholder="Contoh: MHD-001")
        # Format input manual agar seragam (huruf besar & tanpa spasi)
        if id_input:
            id_input = id_input.strip().upper()
            
    with col2:
        aksi = st.selectbox("Jenis Transaksi", ["Kurang (Belanja/Tarik)", "Tambah (Top Up)"])
    with col3:
        jumlah_poin = st.number_input("Jumlah Poin / Rupiah", min_value=0, step=1000)
        
    if st.button("Proses Transaksi", type="primary"):
        if id_input and jumlah_poin > 0:
            if not df_anggota.empty and 'ID' in df_anggota.columns:
                # Modifikasi pencarian agar kebal huruf besar/kecil dan spasi
                df_anggota['ID_CLEAN'] = df_anggota['ID'].astype(str).str.strip().str.upper()
                
                if id_input in df_anggota['ID_CLEAN'].values:
                    data_orang = df_anggota[df_anggota['ID_CLEAN'] == id_input].iloc[0]
                    nama_pilihan = data_orang['Nama']
                    saldo_pilihan = data_orang['Saldo (Poin)']
                    
                    if "Kurang" in aksi and saldo_pilihan < jumlah_poin:
                        st.error(f"❌ Transaksi Gagal: Saldo {nama_pilihan} tidak mencukupi (Sisa: {saldo_pilihan})")
                    else:
                        st.success(f"✅ VERIFIKASI BERHASIL! Nama: {nama_pilihan} | Saldo saat ini: {saldo_pilihan}")
                        st.balloons()
                else:
                    st.error(f"❌ ID ` {id_input} ` TIDAK DITEMUKAN di Google Sheets! Periksa kembali kolom ID di Excel Anda.")
            else:
                st.error("❌ Format Google Sheets salah atau kosong. Pastikan ada kolom bernama 'ID' di baris pertama.")
        else:
            st.warning("Mohon isi ID Anggota dan Jumlah Poin.")

# ================= TAB 2: DAFTAR SALDO =================
with tab2:
    st.subheader("Data Poin Anggota (Live dari Google Sheets)")
    if not df_anggota.empty:
        st.dataframe(df_anggota[['ID', 'Nama', 'Saldo (Poin)']], use_container_width=True)
    else:
        st.warning("Data kosong atau Google Sheets tidak terhubung dengan benar.")
    if st.button("🔄 Segarkan Data (Refresh)"):
        st.cache_data.clear()
        st.rerun()

# ================= TAB 3: CETAK KARTU BARU =================
with tab3:
    st.subheader("Generator QR Code Fisik")
    if not df_anggota.empty and 'ID' in df_anggota.columns:
        id_untuk_qr = st.selectbox("Pilih ID Anggota:", df_anggota['ID'].values)
        
        if id_untuk_qr:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(str(id_untuk_qr).strip().upper()) # Memastikan QR yang dicetak berformat huruf besar bersih
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            import io
            buf = io.BytesIO()
            img_qr.save(buf, format='PNG')
            byte_im = buf.getvalue()
            
            st.image(byte_im, caption=f"QR Code Standar untuk ID: {id_untuk_qr}", width=200)
    else:
        st.write("Belum ada data ID untuk dibuatkan QR.")
