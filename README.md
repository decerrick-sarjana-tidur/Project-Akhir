# MyVault

MyVault membantu mencatat target tabungan, setoran, penarikan, dan progres setiap rencana.

> **Penting:** MyVault adalah pencatat manual. Aplikasi tidak menyimpan atau memindahkan uang dan tidak terhubung ke rekening bank.

## Panduan Pengguna APK

### Memulai

1. Instal APK MyVault dari sumber yang tepercaya, lalu buka aplikasinya.
2. Masuk dengan Google atau email dan kata sandi. Untuk membuat akun email, pilih **Daftar**, isi nama, email, dan kata sandi minimal 6 karakter.
3. Jika hanya ingin mencoba, pilih **Lanjutkan sebagai tamu**.

Akun Google atau email memerlukan koneksi internet untuk memuat dan menyinkronkan vault. Mode tamu menggunakan data contoh dan data yang diubah di mode ini hanya tersimpan sementara di perangkat. Data tamu akan hilang saat aplikasi dimulai ulang, jadi jangan gunakan mode tamu untuk catatan penting.

### Navigasi

Gunakan navigasi di bagian bawah layar:

- **Dashboard** menampilkan jumlah tabungan, progres gabungan, vault prioritas, dan aktivitas terbaru.
- **Vault** menampilkan semua target tabungan. Ketuk vault untuk melihat detail.
- **Statistik** menampilkan setoran bersih per bulan, tabungan per kategori, dan vault yang sudah selesai.
- **Pengaturan** berisi pilihan mata uang, notifikasi, dan tombol keluar.

### Membuat target tabungan

1. Ketuk tombol **+**.
2. Isi nama vault, kategori, target nominal, dan deadline.
3. Tambahkan link barang tujuan jika diperlukan, lalu tandai sebagai prioritas bila ingin menampilkannya di Dashboard.
4. Ketuk **Buat vault**.

Vault baru dimulai dari saldo nol. Untuk membuka target, ketuk vault pada tab **Vault**. Detail menampilkan saldo, sisa target, deadline, saran setoran harian/mingguan, dan riwayat transaksi.

### Mencatat setoran dan penarikan

1. Buka detail vault.
2. Pilih **Tambah saldo** untuk mencatat setoran atau **Tarik saldo** untuk mencatat penarikan.
3. Masukkan nominal atau pilih nominal cepat, lalu konfirmasi.

Penarikan tidak akan membuat saldo vault menjadi kurang dari nol. Setoran yang melewati 25%, 50%, 75%, atau 100% target dapat memunculkan notifikasi pencapaian jika notifikasi diizinkan.

Di detail vault, ikon bintang mengatur prioritas, ikon bagikan membagikan detail, dan ikon tempat sampah menghapus vault. Pastikan vault yang dipilih benar sebelum mengonfirmasi penghapusan.

### Pengaturan dan penyimpanan

- **IDR/USD** mengubah format tampilan nominal. Pilihan USD memakai kurs tetap di aplikasi, bukan kurs pasar langsung.
- **Notifikasi otomatis** menjadwalkan pengingat harian pukul 20.00.
- **Jadwal kustom** meminta izin notifikasi lalu membuka pemilih waktu.
- **Keluar** mengakhiri sesi akun. Untuk mode tamu, tombolnya kembali ke layar login.

Vault pada akun tersimpan dan disinkronkan ke cloud. Jika akun pernah berhasil memuat data tetapi koneksi sedang bermasalah, aplikasi dapat membuka salinan lokal dalam mode baca-saja; perubahan baru tidak dapat disimpan sampai koneksi pulih. Mode tamu berbeda: datanya bukan salinan akun dan tidak bertahan setelah aplikasi dimulai ulang.

---

## Untuk Pengembang

### Menjalankan (tanpa cloud sync)

```bash
pip install -r requirements.txt
flet run myvault/main.py
# atau sebagai web app:
flet run --web myvault/main.py
```

Tanpa file `.env`, app langsung berjalan dalam **mode tamu** menggunakan
data contoh dari `data.py`. Data hilang saat app di-restart.

Setelah akun berhasil memuat vault dari Firestore, snapshot vault disimpan melalui
Secure Storage native (Android Keystore/iOS Keychain). Jika jaringan tidak tersedia
saat sesi dipulihkan atau vault dimuat, snapshot akun tersebut dapat dibuka dalam
mode baca-saja. Perubahan tidak dapat dilakukan secara offline dan cache tidak
dibagikan antar-UID. Web preview tetap memerlukan koneksi untuk memuat vault.

---

## Setup Firebase untuk Flet

Flet menggunakan Firebase Authentication untuk akun dan Cloud Firestore untuk
vault. Gunakan Firebase project khusus Flet yang terpisah dari project APK Flutter
agar akun dan data Firestore kedua app tidak tercampur.

### 1. Gunakan project Firebase yang sudah ada

Buka project Firebase MyVault Flet di <https://console.firebase.google.com/>. Catat
**Project ID** dan **Web API Key** dari Project settings → General. Flet membaca
dua nilai ini dari `.env`; Flet tidak membaca `google-services.json` secara langsung.
File `google-services.json` tetap digunakan oleh build Android Flutter.

### 2. Aktifkan metode login

Di **Authentication → Sign-in method**, aktifkan **Email/Password** dan **Google**.
Gunakan OAuth Client ID bertipe **Web application** dari Google Cloud Console.
Di Firebase provider Google, masukkan Client ID dan Client Secret yang sama.
Tambahkan `http://localhost:8550/oauth_callback` sebagai Authorized redirect URI
di OAuth Client Google.

### 3. Buat Firestore dan atur rules

Buat Cloud Firestore database, buka tab **Rules**, lalu salin isi
[`firestore.rules`](firestore.rules) dan klik **Publish**. Rules membatasi setiap
akun hanya ke dokumen miliknya sendiri di `flet_users/{uid}/vaults/{vaultId}`.

Data Flet disimpan terpisah di `flet_users/{uid}/vaults`. Firebase Authentication
tetap memakai akun yang sama dengan Flutter, tetapi dokumen vault dan transaksi
tidak bercampur.

### 4. Isi `.env` Flet

Tambahkan `FIREBASE_API_KEY`, `FIREBASE_PROJECT_ID`, `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, dan `FIREBASE_OAUTH_REDIRECT_URL` dari Firebase/Google
Cloud. Untuk menjalankan lokal, callback-nya `http://localhost:8550/oauth_callback`.
Jangan commit `.env`.

### 5. Jalankan app

```powershell
flet run --web --port 8550 myvault/main.py
```

Login Google berlangsung lewat browser OAuth Flet lalu Firebase Auth REST.
Functions tidak digunakan, jadi langkah ini tidak memerlukan upgrade Blaze.

**Batas keamanan:** cara ini untuk development/penggunaan pribadi. Client Secret
berada di konfigurasi app Flet; jangan bagikan APK yang dibuat dengan Secret ini.
Rilis publik memerlukan backend tepercaya atau Google Sign-In native.

Data Supabase lama tidak otomatis disalin ke Firestore. File `supabase_schema.sql`
hanya tersisa sebagai arsip.

---

## Alur sinkronisasi

```
App start
  ├─ Ada Firebase session di client_storage?
  │     YA  → refresh token → load vaults dari Firestore → tampilkan app
  │     TIDAK → tampilkan auth screen
  │
Auth screen
  ├─ Email/Google login atau daftar → simpan session → load vaults
  └─ "Lanjutkan sebagai tamu" → load 4 seed vaults → tampilkan app (no sync)

Setiap perubahan vault (buat, transaksi, toggle priority):
  ├─ Update state lokal → UI langsung diperbarui
  └─ Background thread → sync ke Firestore (non-blocking)

Mode offline:
  └─ Jaringan gagal → tampilkan snapshot Secure Storage per UID (baca-saja)
```

Notifikasi lokal memakai Flet extension `flet-reminders` dan Flutter
`flutter_local_notifications`. Toggle otomatis menjadwalkan pengingat harian pukul
20:00; jadwal kustom meminta izin notifikasi lalu membuka pemilih waktu. Milestone
25/50/75/100% juga mengirim notifikasi OS saat transaksi melewati ambang. Android
menggunakan alarm inexact agar tidak memerlukan izin exact alarm; receiver boot
menjadwalkan ulang notifikasi setelah perangkat restart. Web preview tidak dapat
menjamin pengingat saat browser tertutup. Build iOS memerlukan macOS dan Xcode.

---

## Struktur

```
myvault/
  main.py         — entrypoint, MyVaultApp, auth flow, navigasi, toast/confetti
  auth_screen.py  — layar login/daftar (AuthScreen class)
  db.py           — Firebase Auth + Firestore REST operations
  screens.py      — 4 tab (dashboard/vaults/stats/settings) + detail vault
  modals.py       — sheet tambah/tarik saldo & buat vault baru
  components.py   — widget reusable (progress bar/ring, donut, tombol, toggle)
  theme.py        — palet warna, kategori, formatter Rupiah/USD
  compat.py       — shim API Flet lintas-versi
  data.py         — seed data 4 vault contoh (dipakai di mode tamu)

firestore.rules      — Rules akses Firestore per UID
supabase_schema.sql  — skema arsip untuk project Supabase lama
.env                 — konfigurasi Firebase lokal (JANGAN di-commit)
.gitignore           — exclude .env, .venv, __pycache__, dll
requirements.txt     — flet, python-dotenv
```
