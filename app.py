import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
from streamlit_gsheets import GSheetsConnection

# 1. INISIALISASI HALAMAN (Wajib di baris paling atas)
st.set_page_config(page_title="Dompet Digital Ranting", page_icon="💳", layout="wide")

# 2. KONEKSI KE GOOGLE SHEETS
# Masukkan link Google Sheets Anda yang sudah di-share "Anyone with the link" di bawah ini
URL_SHEET = "https://docs.google.com/spreadsheets/d/1xD0dPE1Shl1ddpph4Nw4p3mDuuYmKqIM/edit?usp=drive_link&ouid=106632842841779642489&rtpof=true&sd=true"

# Menghubungkan Streamlit ke Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi untuk membaca data dari Google Sheets (Gunakan cache agar cepat, di-refresh saat ada transaksi)
def ambil_data():
    return conn.read(spreadsheet=URL_SHEET, ttl="0d")

# Memuat data anggota
df_anggota = ambil_data()

# Fungsi untuk menyimpan perubahan kembali ke Google Sheets
def simpan_ke_sheet(df_baru):
    conn.update(spreadsheet=URL_SHEET, data=df_baru)
    st.cache_data.clear()  # Bersihkan memori sementara agar data terbaru langsung muncul

# Fungsi untuk memproses transaksi saldo
def proses_transaksi(id_anggota, jumlah, aksi):
    global df_anggota
    if id_anggota in df_anggota['ID'].values:
        idx = df_anggota[df_anggota['ID'] == id_anggota].index[0]
        nama = df_anggota.at[idx, 'Nama']
        saldo_sekarang = df_anggota.at[idx, 'Saldo (Poin)']
        
        if aksi == "Tambah":
            df_anggota.at[idx, 'Saldo (Poin)'] += jumlah
            simpan_ke_sheet(df_anggota)
            st.success(f"✅ Berhasil menambah {jumlah} poin ke {nama}")
        elif aksi == "Kurang":
            if saldo_sekarang >= jumlah:
                df_anggota.at[idx, 'Saldo (Poin)'] -= jumlah
                simpan_ke_sheet(df_anggota)
                st.success(f"✅ Berhasil memotong {jumlah} poin dari {nama}")
            else:
                st.error(f"❌ Transaksi Gagal: Saldo {nama} tidak mencukupi!")
    else:
        st.error("❌ ID Anggota tidak ditemukan di Google Sheets!")

# 3. ARSITEKTUR UI/UX PREMIUM
st.title("💳 Sistem Kasir & Dompet Digital Ranting")
st.write("Data tersimpan aman dan sinkron otomatis dengan Google Sheets Anda.")
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
                img = Image.open(foto_kamera)
                hasil_scan = decode(img)
                if hasil_scan:
                    id_terdeteksi = hasil_scan[0].data.decode('utf-8')
                    st.info(f"💳 Kartu Terdeteksi! ID Anggota: **{id_terdeteksi}**")
                else:
                    st.warning("⚠️ Kartu terlihat, tapi kodenya tidak terbaca. Pastikan cahaya cukup terang.")
            except Exception as e:
                st.error(f"Gagal membaca kamera: {e}")
                
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
            tipe_aksi = "Tambah" if "Tambah" in aksi else "Kurang"
            proses_transaksi(id_input, jumlah_poin, tipe_aksi)
            st.rerun()
        else:
            st.warning("Mohon isi ID Anggota dan Jumlah Poin terlebih dahulu.")

# ================= TAB 2: DAFTAR SALDO =================
with tab2:
    st.subheader("Data Poin Anggota (Live dari Google Sheets)")
    st.dataframe(df_anggota, use_container_width=True)
    if st.button("🔄 Segarkan Data (Refresh)"):
        st.cache_data.clear()
        st.rerun()

# ================= TAB 3: CETAK KARTU BARU =================
with tab3:
    st.subheader("Buat Anggota Baru & Cetak QR Fisik")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        id_baru = st.text_input("Buat ID Baru (Misal: MHD-004)")
        nama_baru = st.text_input("Nama Sesepuh / Anggota")
        saldo_awal = st.number_input("Saldo Awal Poin", min_value=0, value=0)
        
        if st.button("Daftarkan Anggota Baru"):
            if id_baru and nama_baru:
                if id_baru in df_anggota['ID'].values:
                    st.error("ID sudah digunakan!")
                else:
                    # Tambah baris baru ke dataframe dan simpan ke Google Sheets
                    baris_baru = pd.DataFrame([{"ID": id_baru, "Nama": nama_baru, "Saldo (Poin)": saldo_awal}])
                    df_anggota = pd.concat([df_anggota, baris_baru], ignore_index=True)
                    simpan_ke_sheet(df_anggota)
                    st.success(f"Anggota {nama_baru} berhasil didaftarkan ke Google Sheets!")
                    st.rerun()
            else:
                st.warning("Nama dan ID tidak boleh kosong.")
                
    with col_f2:
        st.write("### Generator QR Code Fisik")
        id_untuk_qr = st.selectbox("Pilih ID Anggota untuk dicetak:", df_anggota['ID'])
        
        if id_untuk_qr:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(id_untuk_qr)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            st.image(img_qr.to_image(), caption=f"QR Code untuk ID: {id_untuk_qr}", width=200)