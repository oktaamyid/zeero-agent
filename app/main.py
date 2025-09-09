    FUZZY_MATCH_CUTOFF = 0.8  # Class constant for fuzzy match cutoff
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from .models import ChatRequest, ChatResponse, KeywordsResponse
import re
from difflib import get_close_matches

ALLOWED_ORIGINS = ["*"]

app = FastAPI(title="ZEERO Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OFFTOPIC_MSG = (
    "Maaf, saya hanya bisa membantu pertanyaan seputar ORMIK 2025 dan STT Nurul Fikri. "
    "Silakan hubungi @ormikxplore di Instagram untuk informasi lainnya."
)

class ZEEROAgent:
    def __init__(self) -> None:
        self.context = self._init_context()

    # === Public API ===
    def reply(self, user_input: str) -> ChatResponse:
        topic_ok = self._is_on_topic(user_input)
        if not topic_ok:
            answer = self._wrap("\n".join([OFFTOPIC_MSG]))
            return ChatResponse(answer=answer, confidence=0.0, topic_ok=False, truncated=False)

        text = self._get_keyword_based_response(user_input)
        text, truncated = self._limit_words(text, 400)
        conf = self._get_keyword_confidence(user_input)
        return ChatResponse(answer=text, confidence=conf, topic_ok=True, truncated=truncated)

    def keywords(self) -> KeywordsResponse:
        return KeywordsResponse(keywords=self._available_keywords())

    # === Rules/Heuristics ===
    def _is_on_topic(self, user_input: str) -> bool:
        s = user_input.lower()
        allow = [
            "ormik", "stt nurul fikri", "stt nf", "nurul fikri", "zeero",
            "jadwal", "schedule", "tanggal", "waktu", "kapan", "jam", "hari",
            "divisi", "organisasi", "panitia",
            "lokasi", "kampus", "alamat", "fasilitas", "dimana", "di mana",
            "kontak", "instagram", "hubungi",
            "tips", "persiapan", "panduan", "dress", "pakaian", "seragam", "outfit",
            "tata tertib", "aturan", "peraturan", "punishment", "hukuman", "sanksi",
            "hak", "kewajiban", "ketentuan", "perizinan", "izin",
            "atribut", "perlengkapan", "tugas", "assignment", "mentor", "kompi",
            "pra ormik", "pra-ormik", "pra", "day 1", "day-1", "last day", "hari pertama", "hari terakhir"
        ]
    if self._has_any_keyword(s, allow):
            return True
        # short greetings still allowed when mentioning ZEERO or ORMIK later
        return False

    # (internal header removed to avoid exposing base prompt)

    def _get_keyword_based_response(self, user_input: str) -> str:
        s = user_input.lower()

        # Greetings/intro
    if self._has_any_keyword(s, ["halo", "hai", "hello", "zeero", "siapa"]):
            return (
                "Halo! Saya **ZEERO** 🤖, Asisten AI untuk ORMIK Explore 2025!\n\n"
                "Saya siap bantu info tentang:\n"
                "• 📅 **Jadwal** kegiatan ORMIK\n"
                "• 👥 **Struktur organisasi** dan divisi\n"
                "• 📍 **Lokasi** & fasilitas kampus\n"
                "• 📞 **Kontak** informasi\n"
                "• 💡 **Tips** & panduan\n"
                "• 👔 **Dress code** & persiapan\n\n"
                "Tanya dengan kata kunci seperti `jadwal`, `divisi`, `lokasi`, atau `tips`! 😊"
            )

    if self._has_any_keyword(s, ["jadwal", "schedule", "tanggal", "waktu", "kapan", "jam", "hari"]):
            lines = [f"• **{x['title']}** - {x['date']}" for x in self.context['ormikData']['schedule']]
            return (
                "📅 **Jadwal ORMIK Explore 2025:**\n\n" + "\n".join(lines) + "\n\n" +
                "⏰ **Waktu:**\n• Setiap hari dimulai pukul **06:30 WIB**\n"
                "• Registrasi ulang 30 menit sebelumnya\n"
                "• Pastikan datang tepat waktu ya!\n\n"
                "📖 **Info Detail:** Unduh guidebook untuk rundown lengkap."
            )

    if self._has_any_keyword(s, ["divisi", "struktur", "organisasi", "panitia", "tim"]):
            return (
                "👥 **Struktur Organisasi ORMIK 2025:**\n\n"
                "**🏆 Core Team:**\n"
                "• Project Officer (PO)\n• Sekretaris\n• Bendahara\n• Liaison Officer (LO)\n\n"
                "**⚡ Divisi Operasional:**\n"
                "• Event\n• Media\n• Kreatif\n• Kedisiplinan\n• Mentor\n• Logistik\n• Konsumsi\n• Medis\n• IT Support\n\n"
                "Ingin tahu detail divisi tertentu? Tanya aja yah! 🌟"
            )

    if self._has_any_keyword(s, ["lokasi", "kampus", "tempat", "alamat", "fasilitas", "dimana", "di mana"]):
            return (
                "🏫 **Lokasi Kegiatan ORMIK:**\n\n"
                "**STT Terpadu Nurul Fikri**\n"
                "📍 Jl. Lenteng Agung Raya No. 20-21, Jagakarsa, Jakarta Selatan 12610\n\n"
                "🗺️ **Fasilitas:** Auditorium, ruang kelas ber-AC, lab komputer, Masjid Al-Hikmah, kantin, area parkir.\n\n"
                "🚌 **Akses:** TransJakarta (Lenteng Agung), KRL (Stasiun Lenteng Agung), angkot Pasar Minggu–Bogor.\n"
                "📍 Google Maps: \"STT Terpadu Nurul Fikri\""
            )

    if self._has_any_keyword(s, ["kontak", "contact", "hubungi", "telepon", "whatsapp", "email", "instagram", "cp"]):
            ig = self.context['ormikData']['contact']
            return (
                "📞 **Kontak ORMIK 2025:**\n\n"
                f"**Instagram DM:** {ig['instagram_handle']}\n"
                f"Link: {ig['instagram']}\n\n"
                "Semua komunikasi resmi via DM Instagram ya! ⏰ Respon: 2–4 jam kerja."
            )

    if self._has_any_keyword(s, ["tips", "saran", "persiapan", "panduan", "aturan"]):
            return (
                "💡 **Tips Sukses ORMIK 2025:**\n\n"
                "✅ **Sebelum:** Baca guidebook, siapkan dress code, istirahat cukup, cek jadwal, siapkan tas.\n"
                "✅ **Selama:** Tepat waktu (06:30), aktif, ramah, ikuti arahan mentor, jaga kebersihan.\n"
                "✅ **Mindset:** Terbuka, berani tanya, nikmati proses. 🌟"
            )

    if self._has_any_keyword(s, ["dress", "pakaian", "baju", "seragam", "outfit"]):
            return (
                "👔 **Dress Code ORMIK 2025:**\n\n"
                "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna."
            )

    if self._has_any_keyword(s, ["tata tertib", "peraturan", "tertib"]):
            return (
                "📋 **Tata Tertib:** Jaga nama baik kampus, hadir 06:30, ikuti rangkaian, hormati panitia, terapkan 6S, isi presensi, pakai atribut.\n"
                "**Dilarang:** Senjata, rokok/vape, narkoba, alkohol, pornografi, kontak fisik lawan jenis, smartphone tanpa izin, perhiasan berlebih, rambut berwarna."
            )

    if self._has_any_keyword(s, ["punishment", "hukuman", "sanksi", "pelanggaran"]):
            return (
                "⚖️ **Punishment:**\n"
                "• Ringan: Pungut 10 sampah.\n"
                "• Sedang: Nyanyi Mars STT NF + surat maaf (15 tanda tangan).\n"
                "• Berat: Evaluasi PO/SC.\n"
                "• Khusus: Dilaporkan kampus (contoh: narkoba/pelecehan)."
            )

    if self._has_any_keyword(s, ["hak"]):
            return (
                "🎓 **Hak Peserta:**\n"
                "1. Mengeluarkan pendapat.\n"
                "2. Mendapat perlakuan adil.\n"
                "3. Mendapat pembelaan panitia jika dirugikan.\n"
                "4. Mendapat info jelas seputar ORMIK.\n"
                "5. Menerima materi ORMIK.\n"
                "6. Mendapat sertifikat jika mengikuti penuh.\n"
                "7. Melaporkan tindakan panitia yang merugikan."
            )

    if self._has_any_keyword(s, ["kewajiban"]):
            return (
                "📘 **Kewajiban Peserta:**\n"
                "1. Mengikuti seluruh rangkaian ORMIK.\n"
                "2. Menjaga nama baik STT NF.\n"
                "3. Menaati seluruh ketentuan panitia."
            )

        if self._has_any_keyword(s, ["ketentuan"]) and self._has_any_keyword(s, ["putra"]):
            return (
                "👕 **Ketentuan Putra:**\n"
                "• Pakaian rapi, baju dimasukkan, lengan tidak digulung, tidak ketat.\n"
                "• Ikat pinggang hitam, kaos kaki putih, sepatu hitam.\n"
                "• Rambut rapi, tidak menutupi mata; yang panjang diikat.\n"
                "• Tanpa aksesori (jaket, gelang/kalung, topi).\n"
                "• Dilarang membawa narkoba, alkohol, rokok/vape, senjata tajam."
            )

        if self._has_any_keyword(s, ["ketentuan"]) and self._has_any_keyword(s, ["putri"]):
            return (
                "👗 **Ketentuan Putri:**\n"
                "• Pakaian longgar tidak transparan, baju tidak dimasukkan.\n"
                "• Rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam.\n"
                "• Muslim: jilbab segiempat + ciput; non‑Muslim rambut diikat rapi.\n"
                "• Tanpa riasan berlebihan atau softlens berwarna.\n"
                "• Tanpa aksesori (jaket, gelang/kalung, topi) dan barang terlarang."
            )

    if self._has_any_keyword(s, ["perizinan", "izin"]):
            return (
                "📝 **Perizinan:**\n"
                "• Saat acara: minta izin ke Tim Kedisiplinan atau Mentor dengan alasan jelas.\n"
                "• Tidak hadir: kirim surat izin ke Mentor via WhatsApp H-1 (maks 23.59) disertai bukti otentik.\n"
                "  Format: Nama - Kompi - Alasan - Bukti."
            )

    if self._has_any_keyword(s, ["atribut", "perlengkapan", "barang", "bawa", "perlu"]):
            return (
                "🎒 **Atribut & Perlengkapan:**\n\n"
                "**Day 1:** ATK, topi rimba navy, name tag, passport, kresek sepatu, sandal, alat salat, BPJS, tumbler, snack.\n"
                "**Last Day:** Item serupa + konsumsi sesuai panduan.\n"
                "**Per Kompi:** Trash bag."
            )

    if self._has_any_keyword(s, ["tugas", "assignment", "kerjaan"]) and self._has_any_keyword(s, ["pra ormik", "pra-ormik", "praormik", "pra"]):
            return (
                "📝 **Tugas Pra ORMIK:**\n\n"
                "• Individu: Name tag ZEERO (A4 laminating), unggah twibbon + tag @ormikxplore, video perkenalan reels, hafal Hymne & Mars.\n"
                "• Kompi: Buat akun IG, logo, yel-yel, siapkan bakat, dan buku passport kompi.\n\n"
                "Mau info tugas Day 1 atau Last Day juga? 😊"
            )

    if self._has_any_keyword(s, ["tugas", "assignment", "kerjaan"]) and self._has_any_keyword(s, ["day 1", "day-1", "hari pertama"]):
            return (
                "📝 **Tugas Day 1:**\n\n"
                "• Individu: Membuat resume materi Day 1.\n"
                "• Kompi: Unggah video yel-yel di IG kompi, dokumentasi setelah acara, dan konten edukasi tema teknologi (beda tiap kompi).\n\n"
                "Ingin tahu tugas untuk Pra ORMIK atau Last Day juga? 🤔"
            )

    if self._has_any_keyword(s, ["tugas", "assignment", "kerjaan"]) and self._has_any_keyword(s, ["last day", "hari terakhir", "lastday"]):
            return (
                "📝 **Tugas Last Day:**\n\n"
                "• Individu: Beri mini gift ke Mentor serta dua surat berbentuk pesawat untuk Mentor dan salah satu panitia.\n"
                "• Kompi: Tampilkan unjuk bakat kolaborasi dua kompi di bawah satu Mentor.\n\n"
                "Mau sekalian lihat tugas Pra ORMIK atau Day 1? 😊"
            )

    if self._has_any_keyword(s, ["tugas", "assignment", "kerjaan"]):
            return (
                "📝 **Tugas ORMIK 2025 (Ringkasan):**\n\n"
                "• Pra ORMIK: Name tag, twibbon IG, video perkenalan, hafal lagu.\n"
                "• Day 1: Resume materi; kompi buat yel-yel, dokumentasi, konten edukasi.\n"
                "• Last Day: Mini gift & dua surat pesawat; kompi unjuk bakat kolaborasi.\n\n"
                "Untuk detail setiap hari, tanyakan dengan kata kunci seperti `tugas day 1` atau `tugas last day`."
            )

        return (
            "Halo! Saya **ZEERO** 🤖 siap bantu info resmi ORMIK 2025.\n\n"
            "**Yang bisa ditanya:** `jadwal`, `divisi`, `lokasi`, `kontak`, `tips`, `dress code`, `tata tertib`, `punishment`, `hak`, `kewajiban`, `ketentuan`, `perizinan`, `atribut`, `tugas`.\n"
            "Contoh: *\"Apa dress code untuk putri?\"* ✨"
        )

    # === Utilities ===
    def _available_keywords(self):
        return [
            'jadwal','schedule','tanggal','waktu','kapan','jam','hari',
            'divisi','struktur','organisasi','panitia','tim',
            'lokasi','kampus','tempat','alamat','fasilitas','dimana','di mana',
            'kontak','telepon','whatsapp','email','instagram','hubungi','cp',
            'tips','saran','persiapan','panduan','aturan',
            'dress code','pakaian','seragam','baju','outfit',
            'tata tertib','peraturan','tertib',
            'punishment','hukuman','sanksi','pelanggaran',
            'hak','kewajiban','ketentuan','perizinan','izin',
            'atribut','perlengkapan','barang','bawa','perlu',
            'tugas','assignment','kerjaan','putra','putri',
            'pra ormik','pra-ormik','pra',
            'day 1','day-1','hari pertama',
            'last day','hari terakhir'
        ]

    def _get_keyword_confidence(self, user_input: str) -> float:
        s = user_input.lower()
        high = ['jadwal','schedule','tanggal','waktu','kapan','jam','hari',
                'kontak','contact','telepon','instagram','lokasi','alamat','kampus','tempat','dimana','di mana',
                'dress code','pakaian','baju','seragam','outfit']
        med  = ['divisi','struktur','panitia','tim','atribut','perlengkapan','barang','tugas','assignment','kerjaan',
                'tata tertib','peraturan','punishment','hukuman','sanksi',
                'hak','kewajiban','ketentuan','perizinan','izin','putra','putri']
        conf = 0.0
        for k in high:
            if self._has_keyword(s, [k]): conf += 0.4
        for k in med:
            if self._has_keyword(s, [k]): conf += 0.3
        return min(conf, 1.0)

    def _has_keyword(self, text: str, keywords: list[str]) -> bool:
        text_lower = text.lower()
        tokens = re.findall(r"\w+", text_lower)
        keywords_set = set(k.lower() for k in keywords)
        # Exact match: check if any token matches a keyword
        if any(token in keywords_set for token in tokens):
            return True
        # Fuzzy match: check if any token is close to a keyword
        for token in tokens:
            if get_close_matches(token, keywords_set, n=1, cutoff=0.8):
                return True
        # Substring match for multi-word keywords
        return any(k in text_lower for k in keywords_set)

    def _init_context(self) -> Dict[str, Any]:
        return {
            "ormikData": {
                "schedule": [
                    {"id": "pra-ormik", "title": "PRA ORMIK", "date": "Senin, Sept 8, 2025", "fullDate": "2025-09-08"},
                    {"id": "day-1", "title": "DAY 1", "date": "Selasa, Sept 16, 2025", "fullDate": "2025-09-16"},
                    {"id": "last-day", "title": "LAST DAY", "date": "Sabtu, Sept 20, 2025", "fullDate": "2025-09-20"}
                ],
                "contact": {
                    "instagram": "https://www.instagram.com/ormikxplore/",
                    "instagram_handle": "@ormikxplore"
                }
            }
        }

    def _limit_words(self, text: str, max_words: int):
        words = re.findall(r"\S+", text)
        if len(words) <= max_words:
            return text, False
        trimmed = " ".join(words[:max_words])
        return trimmed, True

    def _wrap(self, text: str) -> str:
        return text

agent = ZEEROAgent()

# === Routes ===
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/keywords", response_model=KeywordsResponse)
def get_keywords():
    return agent.keywords()

@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    # Optional: place simple header token check here if needed
    return agent.reply(req.query)
