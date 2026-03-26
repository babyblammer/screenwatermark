# Versioning Rules — ScreenWatermark Pro

---

## Format Versi

```
  X  .  Y  .  Z  A
  │     │     │  └── Build index (a, b, c, ...)
  │     │     └───── Hotfix version
  │     └─────────── Update version
  └───────────────── Live version
```

Versi dibaca dari kiri ke kanan. Setiap segmen memiliki makna yang berbeda dan aturan kenaikan yang independen.

---

## Penjelasan Per Segmen

### X — Live Version
Kenaikan besar yang menandakan perubahan arsitektur, platform, atau fitur fundamental aplikasi. Naik ketika ada perubahan yang secara signifikan membedakan produk dari versi sebelumnya.

Contoh: `3.x.x` → `4.0.0`

### Y — Update Version
Kenaikan yang menandakan penambahan fitur baru atau perubahan fungsionalitas yang cukup signifikan namun tidak mengubah fondasi aplikasi.

Nilai Y dibatasi **0–9**. Jika Y sudah berada di angka 9 dan ada update baru, maka Y reset ke 0 dan X naik satu angka secara otomatis.

Contoh: `3.9.x` → `4.0.0` (bukan `3.10.0`)

### Z — Hotfix Version
Kenaikan yang menandakan perbaikan bug tanpa penambahan fitur baru. Setiap siklus hotfix dimulai dari `.1` dan naik secara urut.

Contoh: `3.9.0` → `3.9.1` → `3.9.2`

> `Z = 0` berarti belum ada hotfix pada update tersebut.

### A — Build Index
Huruf alfabet yang menandakan urutan build yang dirilis developer dalam **satu siklus rilis** (X.Y.Z yang sama). Setiap build baru yang diserahkan ke QA menaikkan satu huruf, dan alfabet **tetap dipertahankan pada versi rilis publik**.

- `a` = build pertama
- `b` = build kedua
- `c` = build ketiga
- dst.

Build yang lolos QA dan dirilis ke publik membawa alfabet terakhirnya. Alfabet hanya reset ke `a` ketika X, Y, atau Z naik.

---

## Aturan Reset Build Index

Build index kembali ke `a` setiap kali salah satu dari X, Y, atau Z naik:

| Kejadian | Contoh |
|---|---|
| Hotfix baru | `3.9.1e` → `3.9.2a` |
| Update baru (Y < 9) | `3.8.xe` → `3.9.0a` |
| Update baru (Y = 9) | `3.9.xe` → `4.0.0a` ← Y carry-over ke X |
| Live version baru | `3.x.xe` → `4.0.0a` |

---

## Contoh Bacaan

| Versi | Artinya |
|---|---|
| `3.9.0a` | Versi live 3, update ke-9, belum ada hotfix, build pertama |
| `3.9.1a` | Hotfix pertama dari update 3.9, build pertama |
| `3.9.1e` | Hotfix pertama dari update 3.9, build ke-5 — jika ini yang lolos QA, maka `3.9.1e` adalah versi rilis |
| `3.9.2a` | Hotfix kedua dari update 3.9, build pertama — build index reset ke a |
| `3.10.0a` | ❌ Tidak valid — Y tidak boleh melebihi 9 |
| `4.0.0a` | Update baru saat Y = 9 → X naik, Y dan Z reset ke 0, build index reset ke a |

---

## Contoh Siklus Lengkap

```
3.9.0           ← rilis publik update ke-9

  — ditemukan bug —

3.9.1a          ← dev rilis build pertama hotfix ke-1, QA test
3.9.1b          ← masih ada bug, dev rilis build kedua
3.9.1c          ← masih ada bug, dev rilis build ketiga
3.9.1d          ← masih ada bug, dev rilis build keempat
3.9.1e          ← masih ada bug, dev rilis build kelima  ← posisi saat ini

3.9.1f          ← build berikutnya (menunggu rilis dari developer)

  — semua bug selesai —

3.9.1f          ← build ke-6 lolos QA → ini versi rilis publik (alfabet tetap ada)

  — ditemukan bug baru —

3.9.2a          ← hotfix ke-2 dimulai, build index reset ke a
```

---

## Catatan

- Alfabet **selalu ada** di setiap versi, baik internal maupun rilis publik — tidak pernah dihapus.
- Versi rilis publik adalah build terakhir yang dinyatakan stabil oleh QA, dengan alfabet yang sudah tercantum (contoh: `3.9.1e` bukan `3.9.1`).
- Jumlah build dalam satu siklus tidak dibatasi — alfabet terus naik (`a` → `z`) sesuai kebutuhan.
