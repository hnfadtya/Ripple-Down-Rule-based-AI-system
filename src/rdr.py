"""Sistem rekomendasi transportasi umum Jakarta berbasis Ripple Down Rules (SCRDR).

Knowledge base berbentuk tree biner:
- true-child  : rule pengecualian, dievaluasi jika kondisi node terpenuhi
- false-child : rule alternatif, dievaluasi jika kondisi node tidak terpenuhi
Kesimpulan akhir adalah kesimpulan dari rule terakhir yang menyala.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # folder proyek (induk dari src/)
KB_PATH = ROOT / "KB" / "kb.json"
KASUS_DEFAULT = "data/kasus_uji.json"
KESIMPULAN_DEFAULT = "Naik TransJakarta"

ATRIBUT = {
    "jarak_km": {"tipe": "numerik", "min": 0, "max": 200, "ket": "jarak perjalanan (km)"},
    "budget_rp": {"tipe": "numerik", "min": 0, "max": 10_000_000, "ket": "budget (Rp)"},
    "jam_berangkat": {"tipe": "numerik", "min": 0, "max": 23, "ket": "jam berangkat (0-23)"},
    "jumlah_orang": {"tipe": "numerik", "min": 1, "max": 50, "ket": "jumlah orang"},
    "waktu_maks_menit": {"tipe": "numerik", "min": 1, "max": 600, "ket": "waktu tempuh maksimal (menit)"},
    "barang_bawaan": {"tipe": "kategorikal", "nilai": ["tidak", "sedikit", "banyak"], "ket": "barang bawaan"},
    "cuaca": {"tipe": "kategorikal", "nilai": ["cerah", "hujan"], "ket": "cuaca"},
    "tujuan": {"tipe": "kategorikal", "nilai": ["kerja", "wisata", "bandara"], "ket": "tujuan perjalanan"},
}
OPERATOR_NUMERIK = [">", ">=", "<", "<="]


# ---------------------------------------------------------------- knowledge base

def kb_awal():
    return {
        "root": 0,
        "next_id": 1,
        "rules": {
            "0": {"id": 0, "kondisi": [], "kesimpulan": KESIMPULAN_DEFAULT,
                  "kasus_kunci": None, "true": None, "false": None},
        },
    }


def muat_kb():
    if not KB_PATH.exists():
        kb = kb_awal()
        simpan_kb(kb)
        return kb
    with open(KB_PATH, encoding="utf-8") as f:
        return json.load(f)


def simpan_kb(kb):
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)


def rule(kb, rid):
    return None if rid is None else kb["rules"][str(rid)]


# ---------------------------------------------------------------- kondisi

def cek_kondisi(kond, kasus):
    nilai, op, ambang = kasus[kond["atribut"]], kond["op"], kond["nilai"]
    if op == "=":
        return nilai == ambang
    if op == "!=":
        return nilai != ambang
    if op == ">":
        return nilai > ambang
    if op == ">=":
        return nilai >= ambang
    if op == "<":
        return nilai < ambang
    if op == "<=":
        return nilai <= ambang
    raise ValueError(f"Operator tidak dikenal: {op}")


def rule_menyala(r, kasus):
    return all(cek_kondisi(k, kasus) for k in r["kondisi"])


def teks_kondisi(kondisi):
    if not kondisi:
        return "benar (t)"
    return " DAN ".join(f"{k['atribut']} {k['op']} {fmt(k['nilai'])}" for k in kondisi)


def fmt(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return str(v)


def teks_kasus(kasus):
    return ", ".join(f"{a}={fmt(kasus[a])}" for a in ATRIBUT)


# ---------------------------------------------------------------- penelusuran

def telusuri(kb, kasus):
    """Telusuri tree dan kembalikan (rule pemberi kesimpulan, node terakhir dievaluasi, hasil node itu, jalur)."""
    node = rule(kb, kb["root"])
    menyala, terakhir, hasil_terakhir, jalur = None, None, None, []
    while node is not None:
        ok = rule_menyala(node, kasus)
        jalur.append((node["id"], ok))
        terakhir, hasil_terakhir = node, ok
        if ok:
            menyala = node
            node = rule(kb, node["true"])
        else:
            node = rule(kb, node["false"])
    return menyala, terakhir, hasil_terakhir, jalur


def cetak_jalur(jalur):
    print("  Jalur penelusuran: " + " -> ".join(f"R{rid} {'T' if ok else 'F'}" for rid, ok in jalur))


# ---------------------------------------------------------------- input

def tanya(prompt, default=None):
    teks = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "
    jawab = input(teks).strip()
    return jawab if jawab else ("" if default is None else str(default))


def tanya_ya(prompt):
    while True:
        jawab = tanya(prompt + " (y/n)").lower()
        if jawab in ("y", "ya"):
            return True
        if jawab in ("n", "tidak", "t"):
            return False
        print("  Jawab dengan y atau n.")


def ke_angka(teks):
    """Ubah teks ke angka dengan format Indonesia: titik = pemisah ribuan, koma = desimal.

    Contoh: "20.000" -> 20000, "1.500.000" -> 1500000, "12,5" -> 12.5.
    """
    v = float(teks.strip().replace(".", "").replace(",", "."))
    return int(v) if v.is_integer() else v


def validasi_nilai(atr, nilai):
    info = ATRIBUT[atr]
    if info["tipe"] == "numerik":
        if not isinstance(nilai, (int, float)) or not info["min"] <= nilai <= info["max"]:
            return f"{atr} harus angka {info['min']}..{info['max']}"
    elif nilai not in info["nilai"]:
        return f"{atr} harus salah satu dari {', '.join(info['nilai'])}"
    return None


def input_kasus():
    print("\nMasukkan data konsumen:")
    kasus = {}
    for atr, info in ATRIBUT.items():
        while True:
            if info["tipe"] == "numerik":
                teks = tanya(f"  {info['ket']}")
                try:
                    nilai = ke_angka(teks)
                except ValueError:
                    print("  Masukkan angka.")
                    continue
            else:
                pilihan = info["nilai"]
                daftar = ", ".join(f"{i}={v}" for i, v in enumerate(pilihan, 1))
                teks = tanya(f"  {info['ket']} ({daftar})").lower()
                nilai = pilihan[int(teks) - 1] if teks.isdigit() and 1 <= int(teks) <= len(pilihan) else teks
            galat = validasi_nilai(atr, nilai)
            if galat:
                print("  " + galat)
                continue
            kasus[atr] = nilai
            break
    return kasus


# ---------------------------------------------------------------- akuisisi rule baru

def pilih_kesimpulan(kb, kesimpulan_sekarang):
    daftar = sorted({r["kesimpulan"] for r in kb["rules"].values()})
    print("\nKesimpulan yang benar menurut pakar:")
    for i, k in enumerate(daftar, 1):
        print(f"  {i}. {k}")
    print("  atau ketik kesimpulan baru")
    while True:
        jawab = tanya("Pilihan")
        if not jawab:
            continue
        hasil = daftar[int(jawab) - 1] if jawab.isdigit() and 1 <= int(jawab) <= len(daftar) else jawab
        if hasil == kesimpulan_sekarang:
            print(f"  Itu sama dengan kesimpulan sistem ({hasil}). Pilih kesimpulan lain.")
            continue
        return hasil


def kandidat_kondisi(kasus_baru, kasus_kunci):
    """Atribut yang bisa membedakan kasus baru dari kasus kunci.

    Kategorikal langsung jadi kondisi siap pakai; numerik ambangnya ditentukan pakar.
    Tanpa kasus kunci (rule root), semua atribut kasus baru menjadi kandidat.
    """
    kandidat = []
    for atr, info in ATRIBUT.items():
        nilai = kasus_baru[atr]
        if kasus_kunci is not None and kasus_kunci[atr] == nilai:
            continue
        if info["tipe"] == "numerik":
            kandidat.append({"atribut": atr, "tipe": "numerik"})
        else:
            kandidat.append({"atribut": atr, "tipe": "kategorikal", "op": "=", "nilai": nilai})
            if kasus_kunci is not None:
                kandidat.append({"atribut": atr, "tipe": "kategorikal", "op": "!=", "nilai": kasus_kunci[atr]})
    return kandidat


def teks_kandidat(c, kasus_baru, kasus_kunci):
    if c["tipe"] == "kategorikal":
        return f"{c['atribut']} {c['op']} {c['nilai']}"
    atr = c["atribut"]
    teks = f"{atr} (numerik) - kasus baru: {fmt(kasus_baru[atr])}"
    if kasus_kunci is not None:
        teks += f", kasus kunci: {fmt(kasus_kunci[atr])}"
    return teks + " -> tentukan operator dan ambang"


def valid_untuk_kasus(kond, kasus_baru, kasus_kunci):
    if not cek_kondisi(kond, kasus_baru):
        return "kasus baru tidak memenuhi kondisi ini"
    if kasus_kunci is not None and cek_kondisi(kond, kasus_kunci):
        return "kasus kunci juga memenuhi kondisi ini, jadi tidak membedakan"
    return None


def buat_kondisi_numerik(atr, kasus_baru, kasus_kunci):
    baru = kasus_baru[atr]
    if kasus_kunci is None:
        saran_op, saran_ambang = ">=", baru
    elif baru > kasus_kunci[atr]:
        saran_op, saran_ambang = ">", kasus_kunci[atr]
    else:
        saran_op, saran_ambang = "<=", baru
    while True:
        op = tanya(f"  Operator ({' '.join(OPERATOR_NUMERIK)})", saran_op)
        if op not in OPERATOR_NUMERIK:
            print("  Operator tidak valid.")
            continue
        try:
            ambang = ke_angka(tanya("  Ambang", saran_ambang))
        except ValueError:
            print("  Masukkan angka.")
            continue
        kond = {"atribut": atr, "op": op, "nilai": ambang}
        galat = valid_untuk_kasus(kond, kasus_baru, kasus_kunci)
        if galat:
            print(f"  Kondisi {teks_kondisi([kond])} ditolak: {galat}.")
            continue
        return kond


def pilih_kondisi(kasus_baru, kasus_kunci):
    kandidat = kandidat_kondisi(kasus_baru, kasus_kunci)
    if not kandidat:
        return None
    terpilih = []
    while kandidat:
        print("\nKondisi yang dipenuhi kasus baru" +
              (" dan tidak dipenuhi kasus kunci:" if kasus_kunci is not None else " (rule root tidak punya kasus kunci):"))
        for i, c in enumerate(kandidat, 1):
            print(f"  {i}. {teks_kandidat(c, kasus_baru, kasus_kunci)}")
        jawab = tanya("Pilih nomor kondisi" + (" (kosongkan jika selesai)" if terpilih else ""))
        if not jawab:
            if terpilih:
                break
            continue
        if not (jawab.isdigit() and 1 <= int(jawab) <= len(kandidat)):
            print("  Nomor tidak valid.")
            continue
        c = kandidat[int(jawab) - 1]
        if c["tipe"] == "numerik":
            kond = buat_kondisi_numerik(c["atribut"], kasus_baru, kasus_kunci)
        else:
            kond = {"atribut": c["atribut"], "op": c["op"], "nilai": c["nilai"]}
        terpilih.append(kond)
        kandidat = [k for k in kandidat if k["atribut"] != kond["atribut"]]
        print(f"  Kondisi sementara: {teks_kondisi(terpilih)}")
        if kandidat and not tanya_ya("Tambah kondisi lain (AND)?"):
            break
    return terpilih


def tambah_rule(kb, kasus, menyala, terakhir, hasil_terakhir):
    kesimpulan = pilih_kesimpulan(kb, menyala["kesimpulan"])
    kasus_kunci = menyala["kasus_kunci"]
    if kasus_kunci is not None:
        print(f"\nKasus kunci R{menyala['id']}: {teks_kasus(kasus_kunci)}")
    kondisi = pilih_kondisi(kasus, kasus_kunci)
    if kondisi is None:
        print("\nRule baru DITOLAK: kasus baru identik dengan kasus kunci "
              f"R{menyala['id']} pada semua atribut, sehingga tidak ada kondisi pembeda.")
        print("Periksa kembali data kasus atau kesimpulan pakar. Knowledge base tidak diubah.")
        return None

    rid = kb["next_id"]
    kb["next_id"] += 1
    kb["rules"][str(rid)] = {"id": rid, "kondisi": kondisi, "kesimpulan": kesimpulan,
                             "kasus_kunci": dict(kasus), "true": None, "false": None}
    cabang = "true" if hasil_terakhir else "false"
    terakhir[cabang] = rid
    simpan_kb(kb)

    print(f"\nRule baru R{rid}: JIKA {teks_kondisi(kondisi)} MAKA {kesimpulan}")
    print(f"Ditempel sebagai {cabang}-child R{terakhir['id']} "
          f"(pengecualian bagi kesimpulan R{menyala['id']}: {menyala['kesimpulan']}).")
    return rid


# ---------------------------------------------------------------- konsultasi

def konsultasi(kb, kasus, catatan=None):
    print("\nKasus: " + teks_kasus(kasus))
    if catatan:
        print("Catatan: " + catatan)
    menyala, terakhir, hasil_terakhir, jalur = telusuri(kb, kasus)
    cetak_jalur(jalur)
    print(f"  Rekomendasi sistem: {menyala['kesimpulan']} (dari R{menyala['id']})")
    if tanya_ya("Apakah pakar setuju?"):
        print(f"Rekomendasi diberikan ke konsumen: {menyala['kesimpulan']}")
        return
    if tambah_rule(kb, kasus, menyala, terakhir, hasil_terakhir) is not None:
        menyala, _, _, jalur = telusuri(kb, kasus)
        cetak_jalur(jalur)
        print(f"Rekomendasi diberikan ke konsumen: {menyala['kesimpulan']}")


def muat_kasus_file():
    path = Path(tanya("Path file kasus", KASUS_DEFAULT))
    if not path.is_absolute() and not path.exists():
        path = ROOT / path
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Gagal membaca file: {e}")
        return []
    hasil = []
    for i, item in enumerate(data, 1):
        kasus = item.get("kasus", item)
        galat = [validasi_nilai(a, kasus[a]) if a in kasus else f"{a} tidak ada" for a in ATRIBUT]
        galat = [g for g in galat if g]
        if galat:
            print(f"Kasus #{i} dilewati: {'; '.join(galat)}")
            continue
        hasil.append((item.get("nama", f"Kasus #{i}"), {a: kasus[a] for a in ATRIBUT}, item.get("catatan")))
    return hasil


# ---------------------------------------------------------------- tampilan tree

def cetak_tree(kb, tampil_kunci=False):
    def cetak(rid, awalan, label):
        r = rule(kb, rid)
        if r is None:
            return
        print(f"{awalan}{label}R{r['id']}: JIKA {teks_kondisi(r['kondisi'])} MAKA {r['kesimpulan']}")
        sub = awalan + ("    " if label else "")
        if tampil_kunci and r["kasus_kunci"] is not None:
            print(f"{sub}    kasus kunci: {teks_kasus(r['kasus_kunci'])}")
        cetak(r["true"], sub, "[T] ")
        cetak(r["false"], sub, "[F] ")

    print(f"\nKnowledge base ({len(kb['rules'])} rule). [T] = true-child/pengecualian, [F] = false-child")
    cetak(kb["root"], "", "")


# ---------------------------------------------------------------- menu

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kb = muat_kb()
    print("=== Sistem Rekomendasi Transportasi Umum Jakarta (Ripple Down Rules) ===")
    try:
        menu(kb)
    except (EOFError, KeyboardInterrupt):
        print("\nProgram dihentikan. Rule yang sudah dibuat tetap tersimpan di KB/kb.json.")


def menu(kb):
    while True:
        print("\nMenu:\n  1. Konsultasi kasus baru\n  2. Tampilkan tree knowledge base\n"
              "  3. Muat kasus dari file\n  4. Reset knowledge base\n  5. Keluar")
        pilihan = tanya("Pilihan")
        if pilihan == "1":
            konsultasi(kb, input_kasus())
        elif pilihan == "2":
            cetak_tree(kb, tanya_ya("Tampilkan kasus kunci?"))
        elif pilihan == "3":
            daftar = muat_kasus_file()
            for n, (nama, kasus, catatan) in enumerate(daftar, 1):
                print(f"\n--- {nama} ({n}/{len(daftar)}) ---")
                konsultasi(kb, kasus, catatan)
        elif pilihan == "4":
            if tanya_ya(f"Yakin reset ke satu rule (t -> {KESIMPULAN_DEFAULT})?"):
                kb = kb_awal()
                simpan_kb(kb)
                print("Knowledge base direset.")
        elif pilihan == "5":
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
