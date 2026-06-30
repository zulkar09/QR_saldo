import streamlit as st
import pandas as pd
import qrcode
import cv2
import numpy as np
import gspread
from google.auth.exceptions import GoogleAuthError

# 1. INISIALISASI HALAMAN (Wajib di baris paling atas)
st.set_page_config(page_title="Dompet Digital Ranting", page_icon="💳", layout="wide")

# 2. FUNGSI AKSES GOOGLE SHEETS (Sederhana & Aman)
# Silakan masukkan URL Google Sheet Anda yang sudah di-share "Anyone with the link"
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1xD0dPE1Shl1ddpph4Nw4p3mDuuYmKqIM/edit?usp=drive_link&ouid=106632842841779642489&rtpof=true&sd=true"

@st.cache_data(ttl=0)  # ttl=0 artinya selalu ambil data paling segar tanpa jeda waktu
def ambil_data_sheets(url):
    try:
        # Menghubungkan menggunakan fitur public share agar mudah tanpa file json kredensial
        # Jika sheet di-set "Anyone with the link can view", kita bisa membacanya langsung
        import urllib.parse
        sheet_id = url.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return pd.read_csv(export_url)
    except Exception as e:
        st.error(f"Gagal menghubungkan ke Google Sheets: {e}")
        # Jika gagal, buatkan data darurat agar aplikasi tidak crash
        return pd.DataFrame([{"ID": "MHD-001", "Nama": "Eyang Karso", "Saldo (Poin)": 150000}])

# Memuat data
df_anggota = ambil_data_sheets(URL_SHEETS)

# 3. FUNGSI PEMPROSESAN SALDO
def proses_transaksi(id_anggota, jumlah, aksi):
    st.warning("⚠️ Untuk versi gratis tanpa file kunci rahasia, silakan edit/simpan perubahan saldo langsung di Google Sheets Anda agar 100% aman dan tercatat permanen.")

# 4. ARSITEKTUR UI/UX PREMIUM
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
                # Mengubah foto kamera menjadi format yang dikenali OpenCV
                file_bytes = np.asarray(bytearray(foto_kamera.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, 1)
                
                # Membaca QR Code menggunakan OpenCV (Sangat stabil di Cloud)
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(img)
                
                if data:
                    id_terdeteksi = data
                    st.info(f"💳 Kartu Terdeteksi! ID Anggota: **{id_terdeteksi}**")
                else:
                    st.warning("⚠️ Kartu terlihat, tapi QR Code tidak terbaca. Pastikan posisi tegak dan cahaya cukup.")
            except Exception as e:
                st.error(f"Gagal memproses kamera: {e}")
                
    st.write("### Detail Transaksi")
    col1, col2, col3 = st.columns(3)
    with col1:
        id_input = st.text_input("ID Anggota", value=id_terdeteksi if id_terdeteksi else "", placeholder="Contoh: MHD-001")
    with col2:
        aksi = st.selectbox("Jenis Transaksi", ["Kurang (Belanja/Tarik)", "Tambah (Top Up)"])
    with col3:
        jumlah_poin = st.number_input("Jumlah Poin / Rupiah", min_value=0, step=1000)
        
    if st.button("Proses Transaksi", type="primary"):
        if id_input and jumlah_poin > 0:
            # Mencari nama anggota berdasarkan ID
            if id_input in df_anggota['ID'].values:
                nama_pilihan = df_anggota[df_anggota['ID'] == id_input]['Nama'].values[0]
                saldo_pilihan = df_anggota[df_anggota['ID'] == id_input]['Saldo (Poin)'].values[0]
                
                if "Kurang" in aksi and saldo_pilihan < jumlah_poin:
                    st.error(f"❌ Transaksi Gagal: Saldo {nama_pilihan} tidak mencukupi (Sisa: {saldo_pilihan})")
                else:
                    st.success(f"✅ Permintaan Transaksi untuk **{nama_pilihan}** sebesar **{jumlah_poin}** berhasil diverifikasi!")
            else:
                st.error("❌ ID Anggota tidak ditemukan di Google Sheets!")
        else:
            st.warning("Mohon isi ID Anggota dan Jumlah Poin.")

# ================= TAB 2: DAFTAR SALDO =================
with tab2:
    st.subheader("Data Poin Anggota (Live dari Google Sheets)")
    st.dataframe(df_anggota, use_container_width=True)
    if st.button("🔄 Segarkan Data (Refresh)"):
        st.cache_data.clear()
        st.rerun()

# ================= TAB 3: CETAK KARTU BARU =================
with tab3:
    st.subheader("Generator QR Code Fisik")
    st.write("Pilih ID Anggota yang ada di Google Sheets untuk dibuatkan QR Code kartunya:")
    
    id_untuk_qr = st.selectbox("Pilih ID Anggota:", df_anggota['ID'].values if not df_anggota.empty else ["Belum ada data"])
    
    if id_untuk_qr and id_untuk_qr != "Belum ada data":
        # Membuat QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(id_untuk_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Konversi ke format yang bisa dibaca Streamlit
        import io
        buf = io.BytesIO()
        img_qr.save(buf, format='PNG')
        byte_im = buf.getvalue()
        
        st.image(byte_im, caption=f"QR Code untuk ID: {id_untuk_qr}", width=200)
        st.info("💡 Screenshot QR Code ini, lalu cetak sebagai kartu fisik untuk sesepuh.")
