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
            "atribut", "perlengkapan", "tugas", "assignment", "mentor", "kompi"
        ]
        if self._has_keyword(s, allow):
            return True
        # short greetings still allowed when mentioning ZEERO or ORMIK later
        return False

    # (internal header removed to avoid exposing base prompt)

    def _get_keyword_based_response(self, user_input: str) -> str:
        if self._has_keyword(s, ["hak"]):
            return (
                "🎓 **Hak Peserta ORMIK 2025:**\n"
                "1. Mengeluarkan pendapat, baik secara lisan maupun tulisan.\n"
                "2. Memperoleh perlakuan yang adil dan layak berdasarkan nilai-nilai kemanusiaan.\n"
                "3. Mendapat pembelaan dari panitia apabila diperlakukan secara tidak adil.\n"
                "4. Mendapat informasi yang jelas tentang jadwal kegiatan dan segala yang berkaitan dengan kegiatan ORMIK STT NF.\n"
                "5. Mendapatkan materi ORMIK STT NF.\n"
                "6. Mendapatkan sertifikat bagi yang mengikuti seluruh rangkaian kegiatan ORMIK STT NF, sesuai dengan ketentuan panitia pelaksana.\n"
                "7. Melaporkan segala tindakan panitia yang melanggar nilai kemanusiaan dan merugikan STT NF."
            )
        if self._has_keyword(s, ["kewajiban"]):
            return (
                "📘 **Kewajiban Peserta ORMIK 2025:**\n"
                "1. Mengikuti seluruh rangkaian kegiatan ORMIK STT NF atau yang telah dijadwalkan oleh panitia pelaksana.\n"
                "2. Wajib menjaga nama baik STT Terpadu Nurul Fikri dan IM STT NF.\n"
                "3. Menaati segala ketentuan yang telah ditetapkan oleh panitia pelaksana."
            )
        if self._has_keyword(s, ["ketentuan"]) and ("putra" in s):
            return (
                "👕 **Ketentuan Peserta Putra ORMIK 2025:**\n"
                "1. Pakaian bersih, rapi, dan sopan.\n"
                "2. Baju dimasukkan.\n"
                "3. Lengan tidak digulung.\n"
                "4. Tidak ketat.\n"
                "5. Menggunakan ikat pinggang hitam.\n"
                "6. Menggunakan kaos kaki berwarna putih diatas mata kaki.\n"
                "7. Rambut tidak dicat dan rapi (disisir, tidak menutupi mata, yang panjang diikat rapi).\n"
                "8. Menggunakan sepatu berwarna dominan hitam.\n"
                "9. Kuku bersih dan tidak panjang.\n"
                "10. Dilarang menggunakan aksesori (jaket, gelang/kalung, topi kecuali jam tangan).\n"
                "11. Dilarang membawa barang terlarang (narkoba, minuman keras/alkohol, rokok/vape, senjata tajam/alat berbahaya)."
            )
        if self._has_keyword(s, ["ketentuan"]) and ("putri" in s):
            return (
                "👗 **Ketentuan Peserta Putri ORMIK 2025:**\n"
                "1. Pakaian bersih, rapi, dan sopan.\n"
                "2. Mengenakan pakaian yang longgar, tidak transparan, dan tidak memperlihatkan lekuk tubuh.\n"
                "3. Baju tidak dimasukkan (dikeluarkan).\n"
                "4. Pakaian tidak ketat.\n"
                "5. Lengan baju tidak digulung.\n"
                "6. Wajib mengenakan rok bahan (bukan rok span) dengan panjang hingga mata kaki.\n"
                "7. Menggunakan kaos kaki berwarna putih di atas mata kaki.\n"
                "8. Rambut tidak dicat dan rapi. Muslim: jilbab segiempat (bukan instan) + ciput. Non-Muslim: rambut panjang diikat rapi.\n"
                "9. Menggunakan sepatu berwarna dominan hitam.\n"
                "10. Kuku bersih, tidak panjang, dan tidak diwarnai.\n"
                "11. Dilarang memakai riasan (make up) berlebihan.\n"
                "12. Tidak diperkenankan menggunakan kontak lensa (softlens) berwarna.\n"
                "13. Dilarang menggunakan aksesori (jaket, gelang/kalung, topi kecuali jam tangan).\n"
                "14. Dilarang membawa barang terlarang (narkoba, minuman keras/alkohol, rokok/vape, senjata tajam/alat berbahaya)."
            )
        if self._has_keyword(s, ["perizinan", "izin"]):
            return (
                "📝 **Perizinan ORMIK 2025:**\n"
                "1. Izin saat acara: langsung ke Tim Kedisiplinan atau Mentor di ruangan, berikan alasan jelas (misal: ke toilet, cuci muka, dll).\n"
                "2. Izin tidak mengikuti ORMIK: buat surat izin dan kirim via WhatsApp ke Mentor masing-masing, H-1 (maksimal 23.59 WIB) sebelum acara.\n"
                "   Sertakan bukti otentik (misal: surat keterangan sakit).\n"
                "   Format: Nama - Kompi - Alasan izin - Bukti otentik."
            )
        if self._has_keyword(s, ["atribut", "perlengkapan", "barang", "bawa", "perlu"]):
            return (
                "🎒 **Atribut & Perlengkapan ORMIK 2025:**\n\n"
                "**Day 1 (Individu):**\n"
                "1. Snack level up, snack zero panggang, air pegunungan, putih salju, bola kuning, kotak garing rasa ayam.\n"
                "2. ATK\n3. Topi rimba (navy)\n4. Name tag\n5. Buku passport\n6. Kantung kresek (sepatu)\n7. Sandal\n8. Alat salat\n9. BPJS\n10. Tumbler/tempat minum\n"
                "**Per Kompi:** Trash bag\n"
                "**Last Day (Individu):**\n"
                "1. ATK\n2. Topi rimba (navy)\n3. Name tag\n4. Buku passport\n5. Kantung kresek (sepatu)\n6. Sandal\n7. Alat salat\n8. BPJS\n9. Tumbler/tempat minum\n"
                "**Per Kompi:** Trash bag"
            )
        if self._has_keyword(s, ["tugas", "assignment", "kerjaan"]):
            return (
                "📝 **Tugas ORMIK 2025:**\n\n"
                "**Pra ORMIK:**\n"
                "Individu:\n1. Name tag siluet Zeroo (A4 laminating, isi: nama kompi, logo, nama, foto 3x4, Prodi, asal daerah, motto hidup, tali sesuai Prodi).\n2. Twibbon IG (template, tag @ormikxplore, @sttnf_official, Mentor, kirim link ke GForm).\n3. Video perkenalan (kemeja putih, bawahan hitam, profil, fun fact, hobi, alasan pilih Prodi, kalimat siap terbang, frame khusus, upload reels IG, tag, kirim link ke GForm).\n4. Hafal Hymne & Mars STT NF (buat video, kirim link ke GForm).\n"
                "Kompi:\n1. Akun IG kompi\n2. Logo kompi\n3. Yel-yel\n4. Persiapan bakat untuk last day\n5. Buku passport (A5, isi: biografi, yel-yel, tabel tugas, dresscode, TTD panitia, referensi YouTube/Pin).\n"
                "**Day 1:**\nIndividu: Resume materi day 1.\nKompi: Video yel-yel (upload IG kompi), dokumentasi (upload IG kompi), konten video edukasi tema teknologi (beda tiap kompi, boleh sebelum day 1, upload ke GForm).\n"
                "**Last Day:**\nIndividu: Mini gift untuk Mentor, dua surat pesawat untuk Mentor dan panitia.\nKompi: Unjuk bakat kolaborasi dua kompi di bawah satu Mentor.\n"
                "Ingin tahu detail tugas untuk hari tertentu? Tanyakan misal: 'Tugas Day 1', 'Tugas Pra ORMIK', atau 'Tugas Last Day'."
            )
        s = user_input.lower()

        # Greetings/intro
        if self._has_keyword(s, ["halo", "hai", "hello", "zeero", "siapa"]):
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

        if self._has_keyword(s, ["jadwal", "schedule", "tanggal", "waktu", "kapan", "jam", "hari"]):
            lines = [f"• **{x['title']}** - {x['date']}" for x in self.context['ormikData']['schedule']]
            return (
                "📅 **Jadwal ORMIK Explore 2025:**\n\n" + "\n".join(lines) + "\n\n" +
                "⏰ **Waktu:**\n• Setiap hari dimulai pukul **06:30 WIB**\n"
                "• Registrasi ulang 30 menit sebelumnya\n"
                "• Pastikan datang tepat waktu ya!\n\n"
                "📖 **Info Detail:** Unduh guidebook untuk rundown lengkap."
            )

        if self._has_keyword(s, ["divisi", "struktur", "organisasi", "panitia", "tim"]):
            return (
                "👥 **Struktur Organisasi ORMIK 2025:**\n\n"
                "**🏆 Core Team:**\n"
                "• Project Officer (PO)\n• Sekretaris\n• Bendahara\n• Liaison Officer (LO)\n\n"
                "**⚡ Divisi Operasional:**\n"
                "• Event\n• Media\n• Kreatif\n• Kedisiplinan\n• Mentor\n• Logistik\n• Konsumsi\n• Medis\n• IT Support\n\n"
                "Ingin tahu detail divisi tertentu? Tanya aja! 🌟"
            )

        if self._has_keyword(s, ["lokasi", "kampus", "tempat", "alamat", "fasilitas", "dimana", "di mana"]):
            return (
                "🏫 **Lokasi Kegiatan ORMIK:**\n\n"
                "**STT Terpadu Nurul Fikri**\n"
                "📍 Jl. Lenteng Agung Raya No. 20-21, Jagakarsa, Jakarta Selatan 12610\n\n"
                "🗺️ **Fasilitas:** Auditorium, ruang kelas ber-AC, lab komputer, Masjid Al-Hikmah, kantin, area parkir.\n\n"
                "🚌 **Akses:** TransJakarta (Lenteng Agung), KRL (Stasiun Lenteng Agung), angkot Pasar Minggu–Bogor.\n"
                "📍 Google Maps: \"STT Terpadu Nurul Fikri\""
            )

        if self._has_keyword(s, ["kontak", "contact", "hubungi", "telepon", "whatsapp", "email", "instagram", "cp"]):
            ig = self.context['ormikData']['contact']
            return (
                "📞 **Kontak ORMIK 2025:**\n\n"
                f"**Instagram DM:** {ig['instagram_handle']}\n"
                f"Link: {ig['instagram']}\n\n"
                "Semua komunikasi resmi via DM Instagram ya! ⏰ Respon: 2–4 jam kerja."
            )

        if self._has_keyword(s, ["tips", "saran", "persiapan", "panduan", "aturan"]):
            return (
                "💡 **Tips Sukses ORMIK 2025:**\n\n"
                "✅ **Sebelum:** Baca guidebook, siapkan dress code, istirahat cukup, cek jadwal, siapkan tas.\n"
                "✅ **Selama:** Tepat waktu (06:30), aktif, ramah, ikuti arahan mentor, jaga kebersihan.\n"
                "✅ **Mindset:** Terbuka, berani tanya, nikmati proses. 🌟"
            )

        if self._has_keyword(s, ["dress", "pakaian", "baju", "seragam", "outfit"]):
            return (
                "👔 **Dress Code ORMIK 2025:**\n\n"
                "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna."
            )

        if self._has_keyword(s, ["tata tertib", "peraturan", "tertib"]):
            return (
                "📋 **Tata Tertib Peserta ORMIK 2025:**\n"
                "1. Peserta wajib menjaga nama baik Almamater STT Terpadu Nurul Fikri.\n"
                "2. Peserta wajib datang tepat waktu pada pukul 06.30 WIB.\n"
                "3. Peserta wajib mengikuti seluruh rangkaian ORMIK dan wajib izin apabila tidak bisa mengikuti atau meninggalkan serangkaian acara ORMIK.\n"
                "4. Peserta wajib menghormati dan menghargai panitia maupun sesama peserta ORMIK.\n"
                "5. Peserta wajib menjaga sikap, perilaku, dan tidak boleh gaduh selama acara berlangsung.\n"
                "6. Peserta wajib menerapkan 6S (Senyum, Salam, Sapa, Sopan, Santun, dan Semangat) kepada siapapun.\n"
                "7. Peserta wajib mengisi semua presensi yang disediakan oleh panitia.\n"
                "8. Peserta wajib menggunakan pakaian yang telah ditentukan panitia dari hari pertama hingga akhir.\n"
                "9. Peserta tidak boleh meninggalkan ruang kelas tanpa seizin Tim Kedisiplinan dan Mentor.\n"
                "10. Peserta wajib memakai atribut yang sesuai dengan yang sudah ditentukan.\n"
                "11. Peserta wajib membawa dan melaksanakan penugasan yang diberikan dengan sebaik-baiknya dan penuh tanggung jawab.\n"
                "12. Dilarang membawa senjata tajam dan senjata api.\n"
                "13. Dilarang membawa, mengedarkan, dan menggunakan rokok, rokok elektrik (vape), obat-obatan terlarang, minuman keras, serta barang yang berbau pornografi.\n"
                "14. Dilarang mengikuti rangkaian acara ORMIK dalam keadaan di bawah pengaruh minuman beralkohol dan obat-obatan terlarang.\n"
                "15. Dilarang melakukan kontak fisik dengan lawan jenis, baik peserta maupun panitia ORMIK.\n"
                "16. Dilarang menggunakan smartphone selama acara berlangsung, kecuali jika telah mendapatkan izin dari Mentor dan Tim Kedisiplinan.\n"
                "17. Dilarang menggunakan kalimat atau perkataan yang merendahkan pihak lain.\n"
                "18. Dilarang memakai perhiasan, make up berlebihan, tindik, bertato, dan rambut berwarna."
            )

        if self._has_keyword(s, ["punishment", "hukuman", "sanksi", "pelanggaran"]):
            return (
                "⚖️ **Punishment ORMIK 2025:**\n"
                "• Ringan: Memungut 10 sampah di area kampus. (Pelanggaran 1x)\n"
                "• Sedang: Menyanyikan Mars STT NF & surat permintaan maaf (15 tanda tangan panitia). (Pelanggaran 2x)\n"
                "• Berat: Evaluasi langsung oleh Project Officer/Steering Committee. (Setelah punishment sedang, masih melanggar)\n"
                "• Khusus: Dilaporkan ke pihak kampus. (Contoh: narkoba, minuman keras, pornografi, datang dalam pengaruh alkohol/obat, pelecehan seksual)"
            )

        if self._has_keyword(s, ["atribut", "perlengkapan", "barang", "bawa", "perlu"]):
            return (
                "🎒 **Atribut & Perlengkapan:**\n\n"
                "**Day 1:** ATK, topi rimba navy, name tag, passport, kresek sepatu, sandal, alat salat, BPJS, tumbler, snack.\n"
                "**Last Day:** Item serupa + konsumsi sesuai panduan.\n"
                "**Per Kompi:** Trash bag."
            )

        if self._has_keyword(s, ["tugas", "assignment", "kerjaan"]):
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
            'jadwal','schedule','tanggal','waktu','kapan','jam','hari',
            'divisi','struktur','organisasi','panitia','tim',
            'lokasi','kampus','tempat','alamat','fasilitas','dimana','di mana',
            'kontak','telepon','whatsapp','email','instagram','hubungi','cp',
            'tips','saran','persiapan','panduan','aturan',
            'dress code','pakaian','seragam','baju','outfit',
            'tata tertib','peraturan','tertib',
            'punishment','hukuman','sanksi','pelanggaran',
            'atribut','perlengkapan','barang','bawa','perlu',
            'tugas','assignment','kerjaan'
        ]

    def _get_keyword_confidence(self, user_input: str) -> float:
        s = user_input.lower()
        high = ['jadwal','schedule','tanggal','waktu','kapan','jam','hari',
                'kontak','contact','telepon','instagram','lokasi','alamat','kampus','tempat','dimana','di mana',
                'dress code','pakaian','baju','seragam','outfit']
        med  = ['divisi','struktur','panitia','tim','atribut','perlengkapan','barang','tugas','assignment','kerjaan','tata tertib','peraturan','punishment','hukuman','sanksi']
        conf = 0.0
        for k in high:
            if self._has_keyword(s, [k]): conf += 0.4
        for k in med:
            if self._has_keyword(s, [k]): conf += 0.3
        return min(conf, 1.0)

    def _has_keyword(self, text: str, keywords: list[str]) -> bool:
        tokens = re.findall(r"\w+", text.lower())
        for token in tokens:
            if get_close_matches(token, keywords, n=1, cutoff=0.8):
                return True
        return any(k in text for k in keywords)

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
