# Sistem Rekomendasi Transportasi Umum Jakarta (Ripple Down Rules)

Sistem pakar berbasis Single Classification Ripple Down Rules (SCRDR) berbentuk CLI Python. Pakar (petugas layanan
transportasi) memberi rekomendasi moda transportasi umum kepada konsumen, dan knowledge base bertambah setiap kali
pakar tidak setuju dengan kesimpulan sistem.

## Menjalankan

Butuh Python 3.8+ tanpa library tambahan. Jalankan dari folder proyek:

```
python src/rdr.py
```

Saat pertama dijalankan, program membuat `KB/kb.json` berisi satu rule awal `R0: t -> Naik TransJakarta`.

Menu:

1. **Konsultasi kasus baru**: masukkan 8 atribut konsumen, sistem menampilkan jalur penelusuran dan rekomendasi.
2. **Tampilkan tree knowledge base**: cetak tree beserta kasus kunci setiap rule.
3. **Muat kasus dari file**: jalankan kasus dari file JSON (default `data/kasus_uji.json`) satu per satu.
4. **Reset knowledge base**: kembalikan KB ke satu rule `R0: t -> Naik TransJakarta`.
5. **Keluar**.

## Struktur proyek

```
.
├── src/
│   └── rdr.py            Program utama
├── KB/
│   └── kb.json           Knowledge base aktif (dibuat otomatis, tidak di-commit)
├── data/
│   ├── kasus_uji.json    8 kasus demo berurutan, dengan catatan keputusan pakar di setiap kasus
│   └── kb_contoh.json    Hasil KB setelah menjalankan seluruh kasus_uji.json
├── .gitignore
└── README.md
```

`KB/kb.json` sengaja tidak dimasukkan ke repository agar setiap clone baru berawal dari KB dengan satu rule.
Untuk melihat hasil akhir demo tanpa menjalankan ulang, salin `data/kb_contoh.json` ke `KB/kb.json`.

## Format input angka

Angka memakai format Indonesia: titik sebagai pemisah ribuan dan koma sebagai desimal. Contoh: `20000` atau
`20.000` dibaca 20.000, `1.500.000` dibaca 1.500.000, dan `12,5` dibaca 12,5.

## Atribut kasus

| Atribut | Jenis | Nilai |
|---|---|---|
| jarak_km | numerik | 0-200 |
| budget_rp | numerik | 0-10.000.000 |
| jam_berangkat | numerik | 0-23 |
| jumlah_orang | numerik | 1-50 |
| waktu_maks_menit | numerik | 1-600 |
| barang_bawaan | kategorikal | tidak, sedikit, banyak |
| cuaca | kategorikal | cerah, hujan |
| tujuan | kategorikal | kerja, wisata, bandara |

## Cara kerja

**Struktur rule.** Setiap rule menyimpan kondisi (konjungsi AND), kesimpulan, kasus kunci (kasus yang membuat rule
itu dibuat), true-child, dan false-child.

**Penelusuran.** Mulai dari R0. Jika kondisi node terpenuhi, kesimpulannya dicatat lalu penelusuran lanjut ke
true-child (pengecualian). Jika tidak terpenuhi, lanjut ke false-child. Kesimpulan akhir adalah kesimpulan dari rule
terakhir yang menyala, karena kesimpulan sebelumnya sudah dianulir.

**Saat pakar tidak setuju:**

1. Pakar memilih kesimpulan yang benar dari daftar kesimpulan di KB, atau mengetik kesimpulan baru.
2. Sistem membandingkan kasus baru dengan kasus kunci milik rule pemberi kesimpulan, lalu menawarkan kondisi yang
   dipenuhi kasus baru tetapi tidak dipenuhi kasus kunci. Atribut kategorikal memakai `=` atau `!=`. Untuk atribut
   numerik pakar menentukan operator (`>`, `>=`, `<`, `<=`) dan ambang, lalu sistem memvalidasi kondisinya.
   Rule root tidak punya kasus kunci, sehingga semua atribut kasus baru menjadi kandidat.
3. Pakar memilih satu kondisi atau lebih.
4. Rule baru ditempel pada node terakhir yang dievaluasi: sebagai true-child jika node itu menyala, atau sebagai
   false-child jika tidak. Rule baru tetap merupakan pengecualian bagi kesimpulan yang dianulir.
5. Jika kasus baru identik dengan kasus kunci, rule ditolak karena tidak ada kondisi pembeda, dan KB tidak berubah.

## Tree hasil demo (`data/kb_contoh.json`)

```
R0: JIKA benar (t) MAKA Naik TransJakarta
[T] R1: JIKA jarak_km > 25 MAKA Naik KRL
    [T] R2: JIKA tujuan = bandara MAKA Naik KA Bandara
        [F] R5: JIKA jam_berangkat > 22 MAKA Naik taksi
    [F] R3: JIKA waktu_maks_menit <= 40 MAKA Naik MRT
        [F] R4: JIKA jumlah_orang > 3 MAKA Naik taksi
```

Untuk mengulang demo dari awal: pilih menu 4 (reset), lalu menu 3 dan ikuti catatan pakar pada setiap kasus.

## Anggota Kelompok

| NIM | Nama |
|---|---|
| 13523005 | Muhammad Alfansya |
| 13523041 | Hanif Kalyana Aditya |
