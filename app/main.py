from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from .models import ChatRequest, ChatResponse, KeywordsResponse
import re

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
            "jadwal", "schedule", "tanggal", "waktu", "divisi", "organisasi", "panitia",
            "lokasi", "kampus", "alamat", "fasilitas", "kontak", "instagram",
            "tips", "persiapan", "panduan", "dress", "pakaian", "seragam",
            "tata tertib", "aturan", "peraturan", "punishment", "hukuman", "sanksi",
            "atribut", "perlengkapan", "tugas", "assignment", "mentor", "kompi"
        ]
        if any(k in s for k in allow):
            return True
        # short greetings still allowed when mentioning ZEERO or ORMIK later
        return False

    # (internal header removed to avoid exposing base prompt)

    def _get_keyword_based_response(self, user_input: str) -> str:
        s = user_input.lower()

        # Greetings/intro
        if any(k in s for k in ["halo", "hai", "hello", "zeero", "siapa"]):
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

        if any(k in s for k in ["jadwal", "schedule", "tanggal", "waktu"]):
            lines = [f"• **{x['title']}** - {x['date']}" for x in self.context['ormikData']['schedule']]
            return (
                "📅 **Jadwal ORMIK Explore 2025:**\n\n" + "\n".join(lines) + "\n\n" +
                "⏰ **Waktu:**\n• Setiap hari dimulai pukul **06:30 WIB**\n"
                "• Registrasi ulang 30 menit sebelumnya\n"
                "• Pastikan datang tepat waktu ya!\n\n"
                "📖 **Info Detail:** Unduh guidebook untuk rundown lengkap."
            )

        if any(k in s for k in ["divisi", "struktur", "organisasi", "panitia", "tim"]):
            return (
                "👥 **Struktur Organisasi ORMIK 2025:**\n\n"
                "**🏆 Core Team:**\n"
                "• Project Officer (PO)\n• Sekretaris\n• Bendahara\n• Liaison Officer (LO)\n\n"
                "**⚡ Divisi Operasional:**\n"
                "• Event\n• Media\n• Kreatif\n• Kedisiplinan\n• Mentor\n• Logistik\n• Konsumsi\n• Medis\n• IT Support\n\n"
                "Ingin tahu detail divisi tertentu? Tanya aja! 🌟"
            )

        if any(k in s for k in ["lokasi", "kampus", "tempat", "alamat", "fasilitas"]):
            return (
                "🏫 **Lokasi Kegiatan ORMIK:**\n\n"
                "**STT Terpadu Nurul Fikri**\n"
                "📍 Jl. Lenteng Agung Raya No. 20-21, Jagakarsa, Jakarta Selatan 12610\n\n"
                "🗺️ **Fasilitas:** Auditorium, ruang kelas ber-AC, lab komputer, Masjid Al-Hikmah, kantin, area parkir.\n\n"
                "🚌 **Akses:** TransJakarta (Lenteng Agung), KRL (Stasiun Lenteng Agung), angkot Pasar Minggu–Bogor.\n"
                "📍 Google Maps: \"STT Terpadu Nurul Fikri\""
            )

        if any(k in s for k in ["kontak", "contact", "hubungi", "telepon", "whatsapp", "email", "instagram"]):
            ig = self.context['ormikData']['contact']
            return (
                "📞 **Kontak ORMIK 2025:**\n\n"
                f"**Instagram DM:** {ig['instagram_handle']}\n"
                f"Link: {ig['instagram']}\n\n"
                "Semua komunikasi resmi via DM Instagram ya! ⏰ Respon: 2–4 jam kerja."
            )

        if any(k in s for k in ["tips", "saran", "persiapan", "panduan", "aturan"]):
            return (
                "💡 **Tips Sukses ORMIK 2025:**\n\n"
                "✅ **Sebelum:** Baca guidebook, siapkan dress code, istirahat cukup, cek jadwal, siapkan tas.\n"
                "✅ **Selama:** Tepat waktu (06:30), aktif, ramah, ikuti arahan mentor, jaga kebersihan.\n"
                "✅ **Mindset:** Terbuka, berani tanya, nikmati proses. 🌟"
            )

        if any(k in s for k in ["dress", "pakaian", "baju", "seragam"]):
            return (
                "👔 **Dress Code ORMIK 2025:**\n\n"
                "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna."
            )

        if any(k in s for k in ["tata tertib", "peraturan", "tertib"]):
            return (
                "📋 **Tata Tertib:** Jaga nama baik kampus, hadir 06:30, ikuti rangkaian, hormati panitia, terapkan 6S, isi presensi, pakai atribut.\n"
                "**Dilarang:** Senjata, rokok/vape, narkoba, alkohol, pornografi, kontak fisik lawan jenis, smartphone tanpa izin, perhiasan berlebih, rambut berwarna."
            )

        if any(k in s for k in ["punishment", "hukuman", "sanksi", "pelanggaran"]):
            return (
                "⚖️ **Punishment:**\n"
                "• Ringan: Pungut 10 sampah.\n"
                "• Sedang: Nyanyi Mars STT NF + surat maaf (15 tanda tangan).\n"
                "• Berat: Evaluasi PO/SC.\n"
                "• Khusus: Dilaporkan kampus (contoh: narkoba/pelecehan)."
            )

        if any(k in s for k in ["atribut", "perlengkapan", "barang", "bawa", "perlu"]):
            return (
                "🎒 **Atribut & Perlengkapan:**\n\n"
                "**Day 1:** ATK, topi rimba navy, name tag, passport, kresek sepatu, sandal, alat salat, BPJS, tumbler, snack.\n"
                "**Last Day:** Item serupa + konsumsi sesuai panduan.\n"
                "**Per Kompi:** Trash bag."
            )

        if any(k in s for k in ["tugas", "assignment", "kerjaan"]):
            return (
                "📝 **Tugas ORMIK 2025:**\n\n"
                "**Pra ORMIK (Individu):** Name tag ZEERO (A4 laminating), twibbon + tag @ormikxplore, video perkenalan reels, hafal Hymne & Mars.\n"
                "**Pra ORMIK (Kompi):** Akun IG kompi, logo, yel‑yel, persiapan bakat, passport kompi.\n"
                "**Day 1:** Resume individu; kompi: yel‑yel + dokumentasi + konten edukasi.\n"
                "**Last Day:** Gift & 2 surat pesawat untuk mentor/panitia; kompi: unjuk bakat kolaborasi."
            )

        return (
            "Halo! Saya **ZEERO** 🤖 siap bantu info resmi ORMIK 2025.\n\n"
            "**Yang bisa ditanya:** `jadwal`, `divisi`, `lokasi`, `kontak`, `tips`, `dress code`, `tata tertib`, `punishment`, `atribut`, `tugas`.\n"
            "Contoh: *\"Apa dress code untuk putri?\"* ✨"
        )

    # === Utilities ===
    def _available_keywords(self):
        return [
            'jadwal','schedule','tanggal','waktu',
            'divisi','struktur','organisasi','panitia','tim',
            'lokasi','kampus','tempat','alamat','fasilitas',
            'kontak','telepon','whatsapp','email','instagram',
            'tips','saran','persiapan','panduan','aturan',
            'dress code','pakaian','seragam','baju',
            'tata tertib','peraturan','tertib',
            'punishment','hukuman','sanksi','pelanggaran',
            'atribut','perlengkapan','barang','bawa','perlu',
            'tugas','assignment','kerjaan'
        ]

    def _get_keyword_confidence(self, user_input: str) -> float:
        s = user_input.lower()
        high = ['jadwal','schedule','tanggal','waktu','kontak','contact','telepon','instagram','lokasi','alamat','kampus','tempat','dress code','pakaian','baju','seragam']
        med  = ['divisi','struktur','panitia','tim','atribut','perlengkapan','barang','tugas','assignment','kerjaan','tata tertib','peraturan','punishment','hukuman','sanksi']
        conf = 0.0
        for k in high:
            if k in s: conf += 0.4
        for k in med:
            if k in s: conf += 0.3
        return min(conf, 1.0)

    def _init_context(self) -> Dict[str, Any]:
        return {
            "ormikData": {
                "schedule": [
                    {"id": "pra-ormik", "title": "PRA ORMIK", "date": "Senin, Sept 8, 2025", "fullDate": "2025-09-08"},
                    {"id": "day-1", "title": "DAY 1", "date": "Selasa, Sept 16, 2025", "fullDate": "2025-09-16"},
                    {"id": "day-2", "title": "DAY 2", "date": "Rabu, Sept 17, 2025", "fullDate": "2025-09-17"},
                    {"id": "day-3", "title": "DAY 3", "date": "Kamis, Sept 18, 2025", "fullDate": "2025-09-18"},
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
