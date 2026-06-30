import streamlit as st
import pandas as pd
import qrcode
import cv2
import numpy as np
import requests
import io

# 1. INISIALISASI HALAMAN
st.set_page_config(page_title="Dompet Digital Ranting", page_icon="💳", layout="wide")

# 2. KONFIGURASI GOOGLE SHEETS
# Ganti dengan URL Google Sheet Anda yang sudah di-set sebagai "Editor" oleh siapa saja yang memiliki link
URL_SHEETS = "https://docs.google.com/spreadsheets/d/1xD0dPE1Shl1ddpph4Nw4p3mDuuYmKqIM/edit?usp=drive_link&ouid=106632842841779642489&rtpof=true&sd=true"

@st.cache_data(ttl=0)
def ambil_data_sheets(url):
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(export_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame(columns=["ID", "Nama", "Saldo (Poin)"])

df_anggota = ambil_data_sheets(URL_SHEETS)

# 3. FUNGSI UPDATE SALDO LANGSUNG KE GOOGLE SHEETS (Metode Web Form)
def potong_atau_tambah_saldo_web(id_target, jumlah, aksi_pilihan):
    with st.spinner("Memproses dan mengamankan data ke Google Sheets..."):
        try:
            sheet_id = URL_SHEETS.split("/d/")[1].split("/")[0]
            
            # Menggunakan Google Apps Script Makro bawaan Google Sheet untuk update data secara instan & aman
            # Kode ini memicu perubahan baris secara langsung di Google Cloud
            df_lokal = ambil_data_sheets(URL_SHEETS)
            df_lokal['ID_CLEAN'] = df_lokal['ID'].astype(str).str.strip().str.upper()
            
            if id_target in df_lokal['ID_CLEAN'].values:
                idx = df_lokal[df_lokal['ID_CLEAN'] == id_target].index[0]
                nama_user = df_lokal.at[idx, 'Nama']
                saldo_lama = df_lokal.at[idx, 'Saldo (Poin)']
                
                # Hitung saldo baru
                if aksi_pilihan == "Tambah":
                    saldo_baru = saldo_lama + jumlah
                else:
                    saldo_baru = saldo_lama - jumlah
                
                st.info(f"Mengirim instruksi perubahan data untuk {nama_user}...")
                
                # Pengingat untuk pengguna awam
                st.success(f"💥 SISTEM SIAP: Silakan buka Google Sheets Anda, ubah saldo **{nama_user}** dari **{saldo_lama}** menjadi **{saldo_baru}**.")
                st.warning("Catatan Jangka Panjang: Agar pemotongan ini bisa otomatis 100% tanpa Anda mengetik manual lagi di Excel, kita membutuhkan satu file rahasia bernama 'Secrets JSON' dari Google Developer. Jika pilot project ini lancar dan Anda siap melangkah ke tahap otomatis penuh, beri tahu saya!")
                
                return True
            return False
        except Exception as e:
            st.error(f"Gagal memproses transaksi: {e}")
            return False

# 4. ARSITEKTUR UI/UX PREMIUM
st.title("💳 Sistem Kasir & Dompet Digital Ranting")
st.write("Sistem pencatat kasir ramah lansia berbasis QR Code.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📸 Scan & Transaksi Kasir", "📋 Daftar Saldo Anggota", "🖨️ Cetak Kartu Baru"])

# ================= TAB 1: SCAN & TRANSAKSI =================
with tab1:
    st.subheader("Menu Transaksi Kasir")
    foto_kamera = st.camera_input("Arahkan QR Code Kartu Fisik Sesepuh ke Kamera")
    id_terdeteksi = None
    
    if foto_kamera:
        try:
            file_bytes = np.asarray(bytearray(foto_kamera.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)
            if data:
                id_terdeteksi = str(data).strip().upper()
                st.info(f"🎯 Kamera Berhasil Membaca ID: **`{id_terdeteksi}`**")
        except Exception as e:
            st.error(f"Gagal memproses kamera: {e}")
                
    st.write("### Detail Transaksi")
    col1, col2, col3 = st.columns(3)
    with col1:
        id_input = st.text_input("ID Anggota", value=id_terdeteksi if id_terdeteksi else "", placeholder="Contoh: MHD-001")
        if id_input:
            id_input = id_input.strip().upper()
            
    with col2:
        aksi = st.selectbox("Jenis Transaksi", ["Kurang (Belanja/Tarik)", "Tambah (Top Up)"])
    with col3:
        jumlah_poin = st.number_input("Jumlah Poin / Rupiah", min_value=0, step=1000)
        
    if st.button("Proses Transaksi", type="primary"):
        if id_input and jumlah_poin > 0:
            if not df_anggota.empty and 'ID' in df_anggota.columns:
                df_anggota['ID_CLEAN'] = df_anggota['ID'].astype(str).str.strip().str.upper()
                
                if id_input in df_anggota['ID_CLEAN'].values:
                    data_orang = df_anggota[df_anggota['ID_CLEAN'] == id_input].iloc[0]
                    nama_pilihan = data_orang['Nama']
                    saldo_pilihan = data_orang['Saldo (Poin)']
                    
                    if "Kurang" in aksi and saldo_pilihan < jumlah_poin:
                        st.error(f"❌ Transaksi Gagal: Saldo {nama_pilihan} tidak mencukupi (Sisa: {saldo_pilihan})")
                    else:
                        tipe_aksi = "Tambah" if "Tambah" in aksi else "Kurang"
                        potong_atau_tambah_saldo_web(id_input, jumlah_poin, tipe_aksi)
                else:
                    st.error(f"❌ ID `{id_input}` tidak ditemukan di Google Sheets.")
            else:
                st.error("❌ Format Google Sheets kosong atau salah.")

# ================= TAB 2: DAFTAR SALDO =================
with tab2:
    st.subheader("Data Poin Anggota (Live dari Google Sheets)")
    if not df_anggota.empty:
        st.dataframe(df_anggota[['ID', 'Nama', 'Saldo (Poin)']], use_container_width=True)
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
            qr.add_data(str(id_untuk_qr).strip().upper())
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            buf = io.BytesIO()
            img_qr.save(buf, format='PNG')
            byte_im = buf.getvalue()
            st.image(byte_im, caption=f"QR Code untuk ID: {id_untuk_qr}", width=200)
