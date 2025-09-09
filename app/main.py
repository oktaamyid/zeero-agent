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
        
        # Knowledge base ORMIK Explore 2025 STT NF
        self.ormik_data = {
            "tata_tertib": [
                "Peserta wajib menjaga nama baik Almamater STT Terpadu Nurul Fikri.",
                "Peserta wajib datang tepat waktu pada pukul 06.30 WIB.",
                "Peserta wajib mengikuti seluruh rangkaian ORMIK dan wajib izin apabila tidak bisa mengikuti atau meninggalkan serangkaian acara ORMIK.",
                "Peserta wajib menghormati dan menghargai panitia maupun sesama peserta ORMIK.",
                "Peserta wajib menjaga sikap, perilaku, dan tidak boleh gaduh selama acara berlangsung.",
                "Peserta wajib menerapkan 6S (Senyum, Salam, Sapa, Sopan, Santun, dan Semangat) kepada siapapun.",
                "Peserta wajib mengisi semua presensi yang disediakan oleh panitia.",
                "Peserta wajib menggunakan pakaian yang telah ditentukan panitia dari hari pertama hingga akhir.",
                "Peserta tidak boleh meninggalkan ruang kelas tanpa seizin Tim Kedisiplinan dan Mentor.",
                "Peserta wajib memakai atribut yang sesuai dengan yang sudah ditentukan.",
                "Peserta wajib membawa dan melaksanakan penugasan yang diberikan dengan sebaik-baiknya dan penuh tanggung jawab.",
                "Dilarang membawa senjata tajam dan senjata api.",
                "Dilarang membawa, mengedarkan, dan menggunakan rokok, rokok elektrik (vape), obat-obatan terlarang, minuman keras, serta barang yang berbau pornografi.",
                "Dilarang mengikuti rangkaian acara ORMIK dalam keadaan di bawah pengaruh minuman beralkohol dan obat-obatan terlarang.",
                "Dilarang melakukan kontak fisik dengan lawan jenis, baik peserta maupun panitia ORMIK.",
                "Dilarang menggunakan smartphone selama acara berlangsung, kecuali jika telah mendapatkan izin dari Mentor dan Tim Kedisiplinan.",
                "Dilarang menggunakan kalimat atau perkataan yang merendahkan pihak lain.",
                "Dilarang memakai perhiasan, make up berlebihan, tindik, bertato, dan rambut berwarna."
            ],
            "hak_peserta": [
                "Mengeluarkan pendapat, baik secara lisan maupun tulisan.",
                "Memperoleh perlakuan yang adil dan layak berdasarkan nilai-nilai kemanusiaan.",
                "Mendapat pembelaan dari panitia apabila diperlakukan secara tidak adil.",
                "Mendapat informasi yang jelas tentang jadwal kegiatan dan segala yang berkaitan dengan kegiatan ORMIK STT NF.",
                "Mendapatkan materi ORMIK STT NF.",
                "Mendapatkan sertifikat bagi yang mengikuti seluruh rangkaian kegiatan ORMIK STT NF, sesuai dengan ketentuan panitia pelaksana.",
                "Melaporkan segala tindakan panitia yang melanggar nilai kemanusiaan dan merugikan STT NF."
            ],
            "kewajiban_peserta": [
                "Mengikuti seluruh rangkaian kegiatan ORMIK STT NF atau yang telah dijadwalkan oleh panitia pelaksana.",
                "Wajib menjaga nama baik STT Terpadu Nurul Fikri dan IM STT NF.",
                "Menaati segala ketentuan yang telah ditetapkan oleh panitia pelaksana."
            ],
            "ketentuan_peserta": {
                "putra": [
                    "Pakaian bersih, rapi, dan sopan.",
                    "Baju dimasukkan.",
                    "Lengan tidak digulung.",
                    "Tidak ketat.",
                    "Menggunakan ikat pinggang hitam.",
                    "Menggunakan kaos kaki berwarna putih diatas mata kaki.",
                    "Rambut tidak dicat dan rapi.",
                    "Menggunakan sepatu berwarna dominan hitam.",
                    "Kuku bersih dan tidak panjang.",
                    "Dilarang menggunakan aksesori seperti jaket, gelang/kalung, topi (kecuali jam tangan).",
                    "Dilarang membawa barang terlarang seperti narkoba, minuman keras/alkohol, rokok/vape, senjata tajam atau alat berbahaya."
                ],
                "putri": [
                    "Pakaian bersih, rapi, dan sopan.",
                    "Mengenakan pakaian yang longgar, tidak transparan, dan tidak memperlihatkan lekuk tubuh.",
                    "Baju tidak dimasukkan (dikeluarkan).",
                    "Pakaian tidak ketat.",
                    "Lengan baju tidak digulung.",
                    "Wajib mengenakan rok bahan (bukan rok span) dengan panjang hingga mata kaki.",
                    "Menggunakan kaos kaki berwarna putih di atas mata kaki.",
                    "Rambut tidak dicat dan rapi.",
                    "Bagi yang beragama Islam, diwajibkan menggunakan jilbab segiempat dan ciput.",
                    "Bagi non muslim yang tidak mengenakan jilbab, rambut yang panjangnya melebihi bahu wajib diikat rapi selama acara berlangsung.",
                    "Menggunakan sepatu berwarna dominan hitam.",
                    "Kuku bersih, tidak panjang, dan tidak diwarnai.",
                    "Dilarang memakai riasan (make up) yang berlebihan.",
                    "Tidak diperkenankan menggunakan kontak lensa (softlens) yang berwarna.",
                    "Dilarang menggunakan aksesori seperti jaket, gelang/kalung, topi (kecuali jam tangan).",
                    "Dilarang membawa barang terlarang seperti narkoba, minuman keras/alkohol, rokok/vape, senjata tajam/alat berbahaya."
                ]
            },
            "perizinan": {
                "saat_ormik": [
                    "Izin dapat dilakukan saat ORMIK berlangsung dengan cara melakukan perizinan langsung kepada Tim Kedisiplinan atau Mentor yang berada diruangan dan memberikan alasannya."
                ],
                "tidak_mengikuti": [
                    "Peserta ORMIK yang tidak mengikuti kegiatan, diwajibkan membuat surat izin dan mengirimkannya via WhatsApp kepada Mentor masing-masing.",
                    "Izin diberitahukan H-1 (selambat-lambatnya pukul 23.59 WIB) sebelum acara berlangsung.",
                    "Memberikan bukti otentik bahwa yang bersangkutan memiliki keperluan atau kendala di luar acara ORMIK."
                ]
            },
            "punishment": {
                "ringan": [
                    "Memungut 10 sampah di area kampus.",
                    "Contoh pelanggaran: melanggar aturan-aturan yang telah ditetapkan (1x pelanggaran)."
                ],
                "sedang": [
                    "Menyanyikan Lagu Mars STT Nurul Fikri.",
                    "Membuat surat permintaan maaf yang ditandatangani minimal 15 Panitia ORMIK.",
                    "Contoh pelanggaran: melanggar aturan-aturan yang telah ditetapkan (2x pelanggaran)."
                ],
                "berat": [
                    "Akan mendapatkan evaluasi langsung dari Project Officer atau Steering Committee.",
                    "Contoh pelanggaran: sudah mendapatkan punishment sedang dan masih melakukan pelanggaran."
                ],
                "khusus": [
                    "Dilaporkan langsung ke pihak kampus.",
                    "Contoh pelanggaran: membawa atau mengedarkan obat-obatan terlarang, minuman keras, serta barang yang berbau pornografi, datang ke kampus dalam keadaan dibawah pengaruh minuman beralkohol dan obat-obatan terlarang."
                ]
            },
            "atribut_perlengkapan": {
                "day_1": {
                    "individu": [
                        "Makanan: snack level up, snack zero panggang, air pegunungan, putih salju, bola kuning, kotak garing rasa ayam.",
                        "ATK",
                        "Topi rimba (warna navy)",
                        "Name tag",
                        "Buku passport",
                        "Kantung kresek (untuk sepatu)",
                        "Sandal",
                        "Alat salat",
                        "Kartu asuransi kesehatan (BPJS)",
                        "Tumbler atau tempat minum"
                    ],
                    "kompi": [
                        "Trash bag"
                    ]
                },
                "last_day": {
                    "individu": [
                        "ATK",
                        "Topi rimba (warna navy)",
                        "Name tag",
                        "Buku passport",
                        "Kantung kresek (untuk sepatu)",
                        "Sandal",
                        "Alat salat",
                        "Kartu asuransi kesehatan (BPJS)",
                        "Tumbler atau tempat minum"
                    ],
                    "kompi": [
                        "Trash bag"
                    ]
                }
            },
            "tugas": {
                "pra_ormik": {
                    "individu": [
                        "Membuat name tag berbentuk siluet Zeroo, template: [NAMETAG] EXPLORERS of ORMIK EXPLORE 2025.docx, dilaminating dan menggunakan kertas ukuran A4, berisi: nama kompi, logo kompi, nama, foto (3x4), Prodi, asal daerah, motto hidup, tali name tag berwarna sesuai Prodi (SI=Oren, TI=Biru tua, BD=Merah).",
                        "Mengunggah twibbon ke Instagram, template: http://twibbo.nz/explorers-oe25, wajib First Account, tag / mention IG @ormikxplore, @sttnf_official, dan Mentor masing-masing, kirimkan link postingan ke GForm penugasan.",
                        "Membuat Video Perkenalan, ketentuan: menggunakan kemeja putih dan bawahan hitam, profil diri (nama lengkap, nama panggilan, kompi, prodi, domisili), fun Fact diri sendiri, hobi, alasan pilih Prodi, 'Kalau kamu adalah seorang penjelajah, kamu mau menjelajahi apa?', tambahan kalimat akhir video: '(Nama kamu) siap terbang bersama ORMIK Explore 2025! Start from Zero Go To Heroo!', frame video perkenalan: [OE25] FRAME EXPLORER INTRODUCE.png, unggah video di reels instagram first account masing-masing lalu tag IG @sttnf_official, @ormikxplore, serta Mentor masing-masing, kirimkan link video ke GForm penugasan.",
                        "Wajib menghafalkan lagu: Hymne STT NF, Mars STT NF. Notes: Buat video lalu kirimkan link video (GDrive) ke GForm penugasan."
                    ],
                    "kompi": [
                        "Membuat akun Instagram kompi.",
                        "Membuat logo kompi.",
                        "Membuat yel-yel.",
                        "Mempersiapkan bakat yang akan ditampilkan saat last day ORMIK.",
                        "Membuat buku passport: Passport merupakan buku kecil yang wajib dimiliki oleh setiap mentee selama kegiatan ORMIK berlangsung. Passport ini berfungsi sebagai identitas, catatan perjalanan kegiatan, sekaligus bukti kehadiran dan partisipasi mentee. Desain passport dibuat sama setiap kompi. Isi utama buku: Halaman biografi peserta, lirik yel-yel kelompok, tabel penugasan perhari juga kesesuaian dresscode, dan kolom untuk TTD Panitia ORMIK. Ukuran buku passport A5 : 2. Referensi: https://youtube.com/shorts/t0jyYoVfUao?si=-v-VeuzCJ4kMoaUz, https://youtube.com/shorts/-xNlG-QLF6c?si=LdUNvk_9fEzgmwJl, https://pin.it/42Ylcu8Ke"
                    ]
                },
                "day_1": {
                    "individu": [
                        "Membuat resume materi day 1."
                    ],
                    "kompi": [
                        "Membuat video yel-yel dan upload di IG kompi masing-masing.",
                        "Dokumentasi setelah selesai ORMIK day 1 dan upload di IG kompi masing-masing.",
                        "Membuat konten video edukasi sekreatif mungkin dengan tema: Teknologi (tema setiap kompi harus berbeda-beda). Pengerjaan tugas ini boleh dikerjakan sebelum ORMIK day 1.",
                        "* notes: Teknis pengumpulan seluruh tugas di link GForm penugasan."
                    ]
                },
                "last_day": {
                    "individu": [
                        "Memberikan satu mini gift kepada Mentor masing-masing.",
                        "Membuat dua surat yang dibentuk pesawat untuk diberikan ke Mentor masing-masing dan salah satu panitia ormik."
                    ],
                    "kompi": [
                        "Menampilkan unjuk bakat kolaborasi dua kompi yang dibimbing oleh satu Mentor."
                    ]
                }
            }
        }

    # Fungsi untuk mengambil informasi ORMIK
    def get_ormik_info(self, category, subcategory=None, day=None):
        try:
            if day:
                return self.ormik_data[category][day][subcategory]
            elif subcategory:
                return self.ormik_data[category][subcategory]
            else:
                return self.ormik_data[category]
        except KeyError:
            return "Data tidak ditemukan."
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
        s = user_input.lower()
        if self._has_keyword(s, ["hak", "hak peserta", "peserta"]):
            hak_list = self.get_ormik_info("hak_peserta")
            return (
                "🎓 **Hak Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(hak_list)]) +
                "\n\nApakah Anda ingin tahu juga kewajiban peserta?"
            )
        if self._has_keyword(s, ["kewajiban", "wajib", "kewajiban peserta"]):
            kewajiban_list = self.get_ormik_info("kewajiban_peserta")
            return (
                "📘 **Kewajiban Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(kewajiban_list)]) +
                "\n\nApakah Anda ingin tahu juga hak peserta?"
            )
        if self._has_keyword(s, ["ketentuan", "putra", "putri", "dress code", "pakaian"]):
            if "putra" in s:
                putra_list = self.get_ormik_info("ketentuan_peserta", "putra")
                return (
                    "👕 **Ketentuan Peserta Putra ORMIK 2025:**\n" +
                    "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(putra_list)]) +
                    "\n\nApakah Anda ingin tahu juga ketentuan peserta putri?"
                )
            elif "putri" in s:
                putri_list = self.get_ormik_info("ketentuan_peserta", "putri")
                return (
                    "👗 **Ketentuan Peserta Putri ORMIK 2025:**\n" +
                    "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(putri_list)]) +
                    "\n\nApakah Anda ingin tahu juga ketentuan peserta putra?"
                )
            else:
                return (
                    "👔 **Ketentuan Peserta ORMIK 2025:**\n\n"
                    "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                    "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                    "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna.\n\n"
                    "Ingin tahu detail untuk putra atau putri? Tanyakan misal: 'Ketentuan putra'."
                )
        if self._has_keyword(s, ["perizinan", "izin", "izinan"]):
            izin_saat = self.get_ormik_info("perizinan", "saat_ormik")
            izin_tidak = self.get_ormik_info("perizinan", "tidak_mengikuti")
            return (
                "📝 **Perizinan ORMIK 2025:**\n\n"
                "**Saat ORMIK berlangsung:**\n" +
                "\n".join([f"• {item}" for item in izin_saat]) +
                "\n\n**Izin tidak mengikuti ORMIK:**\n" +
                "\n".join([f"• {item}" for item in izin_tidak]) +
                "\n\nApakah Anda ingin tahu juga tentang punishment atau tata tertib?"
            )
        if self._has_keyword(s, ["tugas", "assignment", "kerjaan", "kerja", "tugas apa"]):
            if "day 1" in s or "day1" in s:
                individu = self.get_ormik_info("tugas", "individu", "day_1")
                kompi = self.get_ormik_info("tugas", "kompi", "day_1")
                response = "📝 **Tugas Day 1 ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx+1}. {item}" for item in kompi])
                return response + "\n\nApakah Anda ingin tahu juga tugas di Pra ORMIK atau Last Day?"
            elif "last" in s or "akhir" in s:
                individu = self.get_ormik_info("tugas", "individu", "last_day")
                kompi = self.get_ormik_info("tugas", "kompi", "last_day")
                response = "📝 **Tugas Last Day ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx+1}. {item}" for item in kompi])
                return response + "\n\nApakah Anda ingin tahu juga tugas di Pra ORMIK atau Day 1?"
            elif "pra" in s or "ormik" in s:
                individu = self.get_ormik_info("tugas", "individu", "pra_ormik")
                kompi = self.get_ormik_info("tugas", "kompi", "pra_ormik")
                response = "📝 **Tugas Pra ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx+1}. {item}" for item in kompi])
                return response + "\n\nApakah Anda ingin tahu juga tugas di Day 1 atau Last Day?"
            else:
                return (
                    "📝 **Tugas ORMIK 2025:**\n\n"
                    "**Pra ORMIK:** Name tag, twibbon IG, video perkenalan, hafal Hymne & Mars (individu); akun IG kompi, logo, yel-yel, passport (kompi).\n"
                    "**Day 1:** Resume materi (individu); video yel-yel, dokumentasi, video edukasi teknologi (kompi).\n"
                    "**Last Day:** Mini gift & surat pesawat (individu); unjuk bakat kolaborasi (kompi).\n\n"
                    "Ingin tahu detail tugas untuk hari tertentu? Tanyakan misal: 'Tugas Day 1', 'Tugas Pra ORMIK', atau 'Tugas Last Day'."
                )

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
                "⏰ **Waktu:**\n• Peserta wajib datang tepat waktu pada pukul **06:30 WIB** sesuai tata tertib.\n"
                "• Registrasi ulang 30 menit sebelumnya\n"
                "• Pastikan datang tepat waktu ya!\n\n"
                "📖 **Info Detail:** Unduh guidebook untuk rundown lengkap.\n\n"
                "Apakah Anda ingin tahu juga tentang lokasi kampus atau tips persiapan?"
            )

        if self._has_keyword(s, ["divisi", "struktur", "organisasi", "panitia", "tim"]):
            return (
                "👥 **Struktur Organisasi ORMIK 2025:**\n\n"
                "**🏆 Core Team:**\n"
                "• Project Officer (PO)\n• Sekretaris\n• Bendahara\n• Liaison Officer (LO)\n\n"
                "**⚡ Divisi Operasional:**\n"
                "• Event\n• Media\n• Kreatif\n• Kedisiplinan\n• Mentor\n• Logistik\n• Konsumsi\n• Medis\n• IT Support\n\n"
                "Ingin tahu detail divisi tertentu? Tanya aja! 🌟\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal kegiatan atau lokasi kampus?"
            )

        if self._has_keyword(s, ["lokasi", "kampus", "tempat", "alamat", "fasilitas", "dimana", "di mana"]):
            k = self.context['ormikData']['kampus']
            return (
                "🏫 **Lokasi Kegiatan ORMIK:**\n\n"
                f"**{k['nama']}**\n"
                f"📍 {k['alamat']}, {k['kota']}, {k['provinsi']}\n\n"
                "🗺️ **Fasilitas:** Auditorium, ruang kelas ber-AC, lab komputer, Masjid Al-Hikmah, kantin, area parkir.\n\n"
                "🚌 **Akses:** TransJakarta (Lenteng Agung), KRL (Stasiun Lenteng Agung), angkot Pasar Minggu–Bogor.\n"
                f"📍 Google Maps: \"{k['nama']}\"\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal kegiatan atau kontak panitia?"
            )

        if self._has_keyword(s, ["kontak", "contact", "hubungi", "telepon", "whatsapp", "email", "instagram", "cp"]):
            ig = self.context['ormikData']['contact']
            k = self.context['ormikData']['kampus']
            return (
                "📞 **Kontak ORMIK 2025:**\n\n"
                f"**Instagram DM:** {ig['instagram_handle']}\n"
                f"Link: {ig['instagram']}\n\n"
                "Semua komunikasi resmi via DM Instagram ya! ⏰ Respon: 2–4 jam kerja.\n\n"
                "Untuk info umum kampus:\n"
                f"• Hotline: {k['hotline']}\n"
                f"• WhatsApp: {k['whatsapp']}\n"
                f"• Email: {k['email']}\n"
                f"• Website: {k['website']}\n\n"
                "Apakah Anda ingin tahu juga tentang lokasi kampus atau jadwal kegiatan?"
            )

        if self._has_keyword(s, ["tips", "saran", "persiapan", "panduan", "aturan"]):
            return (
                "💡 **Tips Sukses ORMIK 2025:**\n\n"
                "✅ **Sebelum:** Baca guidebook, siapkan dress code, istirahat cukup, cek jadwal, siapkan tas.\n"
                "✅ **Selama:** Datang tepat waktu pukul 06:30 WIB sesuai tata tertib, aktif, ramah, ikuti arahan mentor, jaga kebersihan.\n"
                "✅ **Mindset:** Terbuka, berani tanya, nikmati proses. 🌟\n\n"
                "Apakah Anda ingin tahu juga tentang dress code atau atribut yang perlu dibawa?"
            )

        if self._has_keyword(s, ["dress", "pakaian", "baju", "seragam", "outfit"]):
            return (
                "👔 **Dress Code ORMIK 2025:**\n\n"
                "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna.\n\n"
                "Apakah Anda ingin tahu juga tentang tips persiapan atau atribut yang perlu dibawa?"
            )

        if self._has_keyword(s, ["tata tertib", "peraturan", "tertib", "tata", "aturan", "atur"]):
            tertib_list = self.get_ormik_info("tata_tertib")
            return (
                "📋 **Tata Tertib Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(tertib_list)]) +
                "\n\nApakah Anda ingin tahu juga tentang punishment atau hak peserta?"
            )

        if self._has_keyword(s, ["punishment", "hukuman", "sanksi", "pelanggaran", "hukum", "sanksi apa"]):
            if "ringan" in s:
                ringan = self.get_ormik_info("punishment", "ringan")
                response = "⚖️ **Punishment Ringan ORMIK 2025:**\n" + "\n".join([f"• {item}" for item in ringan])
                return response + "\n\nApakah Anda ingin tahu juga punishment sedang, berat, atau khusus?"
            elif "sedang" in s:
                sedang = self.get_ormik_info("punishment", "sedang")
                response = "⚖️ **Punishment Sedang ORMIK 2025:**\n" + "\n".join([f"• {item}" for item in sedang])
                return response + "\n\nApakah Anda ingin tahu juga punishment ringan, berat, atau khusus?"
            elif "berat" in s:
                berat = self.get_ormik_info("punishment", "berat")
                response = "⚖️ **Punishment Berat ORMIK 2025:**\n" + "\n".join([f"• {item}" for item in berat])
                return response + "\n\nApakah Anda ingin tahu juga punishment ringan, sedang, atau khusus?"
            elif "khusus" in s:
                khusus = self.get_ormik_info("punishment", "khusus")
                response = "⚖️ **Punishment Khusus ORMIK 2025:**\n" + "\n".join([f"• {item}" for item in khusus])
                return response + "\n\nApakah Anda ingin tahu juga punishment ringan, sedang, atau berat?"
            else:
                return (
                    "⚖️ **Punishment ORMIK 2025:**\n"
                    "• Ringan: Memungut 10 sampah di area kampus. (Pelanggaran 1x)\n"
                    "• Sedang: Menyanyikan Mars STT NF & surat permintaan maaf (15 tanda tangan panitia). (Pelanggaran 2x)\n"
                    "• Berat: Evaluasi langsung oleh Project Officer/Steering Committee. (Setelah punishment sedang, masih melanggar)\n"
                    "• Khusus: Dilaporkan ke pihak kampus. (Contoh: narkoba, minuman keras, pornografi, datang dalam pengaruh alkohol/obat, pelecehan seksual)\n\n"
                    "Ingin tahu detail punishment tertentu? Tanyakan misal: 'Punishment ringan' atau 'Punishment khusus'."
                )

        if self._has_keyword(s, ["atribut", "perlengkapan", "barang", "bawa", "perlu", "bawa apa", "apa yang dibawa"]):
            if "day 1" in s or "day1" in s:
                individu = self.get_ormik_info("atribut_perlengkapan", "individu", "day_1")
                kompi = self.get_ormik_info("atribut_perlengkapan", "kompi", "day_1")
                response = "🎒 **Atribut & Perlengkapan Day 1 ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"• {item}" for item in individu]) + "\n\n**Kompi:**\n" + "\n".join([f"• {item}" for item in kompi])
                return response + "\n\nApakah Anda ingin tahu juga atribut di Last Day?"
            elif "last" in s or "akhir" in s:
                individu = self.get_ormik_info("atribut_perlengkapan", "individu", "last_day")
                kompi = self.get_ormik_info("atribut_perlengkapan", "kompi", "last_day")
                response = "🎒 **Atribut & Perlengkapan Last Day ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"• {item}" for item in individu]) + "\n\n**Kompi:**\n" + "\n".join([f"• {item}" for item in kompi])
                return response + "\n\nApakah Anda ingin tahu juga atribut di Day 1?"
            else:
                return (
                    "🎒 **Atribut & Perlengkapan ORMIK 2025:**\n\n"
                    "**Day 1 (Individu):** Makanan (snack level up, dll), ATK, topi rimba navy, name tag, passport, kresek sepatu, sandal, alat salat, BPJS, tumbler.\n"
                    "**Per Kompi:** Trash bag.\n"
                    "**Last Day:** Item serupa + konsumsi sesuai panduan.\n\n"
                    "Ingin tahu detail atribut untuk hari tertentu? Tanyakan misal: 'Atribut Day 1' atau 'Atribut Last Day'."
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
                    {"id": "pra-ormik", "title": "PRA ORMIK", "date": "Senin, 8 September 2025", "fullDate": "2025-09-08"},
                    {"id": "day-1", "title": "DAY 1", "date": "Selasa, 16 September 2025", "fullDate": "2025-09-16"},
                    {"id": "last-day", "title": "LAST DAY", "date": "Sabtu, 20 September 2025", "fullDate": "2025-09-20"}
                ],
                "contact": {
                    "instagram": "https://www.instagram.com/ormikxplore/",
                    "instagram_handle": "@ormikxplore"
                },
                "kampus": {
                    "nama": "STT Terpadu Nurul Fikri Kampus B",
                    "alamat": "Jl. Raya Lenteng Agung No.20–21, Srengseng Sawah, Jagakarsa, Jakarta Selatan",
                    "kota": "Jakarta Selatan",
                    "provinsi": "DKI Jakarta",
                    "hotline": "021-7863191",
                    "whatsapp": "0857-1624-3174",
                    "email": "info@nurulfikri.ac.id",
                    "website": "https://nurulfikri.ac.id"
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
