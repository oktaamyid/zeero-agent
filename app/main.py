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
            "tentang_ormik": {
                "nama_lengkap": "Orientasi Mahasiswa Baru",
                "institusi": "Sekolah Tinggi Teknologi Terpadu Nurul Fikri",
                "deskripsi": "Kegiatan yang bertujuan untuk memperkenalkan mahasiswa baru dengan sistem perkuliahan dan lingkungan kampus.",
                "nama_acara": "Ormik Explore",
                "tahun": "2025",
                "visi": "ORMIK EXPLORE 2025 memiliki visi menjadi titik mulai eksplorasi mahasiswa baru STT-NF dalam membangun semangat akademik, budaya positif, dan kesiapan diri di era modern."
            },
            "divisi": {
                "steering_committee": {
                    "name": "Steering Committee",
                "position": "STEERING COMMITTEE",
                    "description": "Steering Committee bertanggung jawab mengendalikan seluruh proses kegiatan, mulai dari tahap perencanaan hingga evaluasi akhir, guna memastikan kegiatan berjalan sesuai tujuan dan harapan."
                },
                "project_officer": {
                    "name": "Project Officer",
                    "position": "PROJECT OFFICER", 
                    "description": "Individu yang memegang tanggung jawab penuh atas pelaksanaan kegiatan ORMIK. Project Officer bertugas mengawasi secara langsung seluruh elemen di bawahnya, antara lain Sekretaris, Bendahara, dan divisi-divisi lainnya."
                },
                "sekretaris": {
                    "name": "Sekretaris",
                    "position": "SEKRETARIS",
                    "description": "Membantu Project officer dalam menjalankan fungsi administrasi, dengan tanggung jawab utama meliputi pengelolaan dokumen, surat-menyurat, proposal, serta pembuatan notulen rapat."
                },
                "bendahara": {
                    "name": "Bendahara", 
                    "position": "BENDAHARA",
                    "description": "Bendahara bertugas untuk menyusun rencana anggaran, mencatat transaksi keuangan, dan membuat laporan pertanggungjawaban keuangan, serta berkoordinasi dengan pihak Kemahasiswaan terkait dana kegiatan."
                },
                "public_relation": {
                    "name": "Public Relation",
                    "position": "PUBLIC RELATION",
                    "description": "Bertanggung jawab untuk mengelola komunikasi, membangun citra positif, serta menjalin hubungan antara ORMIK dengan eksternal di lingkup STT NF."
                },
                "liaison_officer": {
                    "name": "Liaison Officer",
                    "position": "LIAISON OFFICER", 
                    "description": "Divisi ini akan berkomunikasi dengan publik eksternal maupun internal kampus. LO juga bertindak sebagai contact person bagi pihak internal maupun eksternal. Serta membantu briefing pihak internal maupun eksternal."
                },
                "event": {
                    "name": "Event",
                    "position": "EVENT",
                    "description": "Bertanggung jawab atas perencanaan, koordinasi, dan pelaksanaan seluruh rangkaian acara ORMIK, termasuk acara puncak."
                },
                "media": {
                    "name": "Media",
                    "position": "MEDIA",
                    "description": "Bertugas untuk memproduksi, mengelola, dan mengabadikan seluruh momen kegiatan ORMIK dalam bentuk dokumentasi serta memastikan seluruh kebutuhan visual dan desain terpenuhi."
                },
                "kreatif": {
                    "name": "Kreatif",
                    "position": "KREATIF",
                    "description": "Divisi Kreatif bertugas menciptakan suasana acara yang menarik, interaktif, dan berkesan melalui berbagai elemen hiburan, visual, dan partisipatif."
                },
                "kedisiplinan": {
                    "name": "Kedisiplinan",
                    "position": "KEDISIPLINAN",
                    "description": "Bertugas memastikan seluruh rangkaian kegiatan ORMIK berjalan dengan tertib, tepat waktu, dan sesuai aturan yang telah ditetapkan."
                },
                "mentor": {
                    "name": "Mentor",
                    "position": "MENTOR",
                    "description": "Bertugas untuk membimbing, mengarahkan, mendampingi, dan memberikan dukungan kepada peserta ORMIK selama kegiatan berlangsung."
                },
                "logistik": {
                    "name": "Logistik",
                    "position": "LOGISTIK",
                    "description": "Bertanggung jawab untuk mengatur seluruh kebutuhan perlengkapan, peralatan, dan sarana prasarana yang diperlukan dalam mendukung kelancaran kegiatan ORMIK."
                },
                "konsumsi": {
                    "name": "Konsumsi",
                    "position": "KONSUMSI",
                    "description": "Bertugas untuk menyiapkan menu makanan, camilan, serta menjadwalkan waktu makan selama kegiatan ORMIK. Divisi ini juga harus mampu mengatur persediaan makanan dengan cermat untuk memastikan kelancaran acara."
                },
                "medis": {
                    "name": "Medis",
                    "position": "MEDIS",
                    "description": "Bertugas untuk memastikan keselamatan dan kesehatan seluruh peserta dan panitia selama kegiatan ORMIK berlangsung."
                },
                "it_support": {
                    "name": "IT Support",
                    "position": "IT SUPPORT",
                    "description": "Fokus utama divisi ini mencakup instalasi perangkat, live streaming, serta pengawasan terhadap tiga objek utama, komputer, software, dan sistem jaringan (network)."
                }
            },
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
            "ormik sttnf", "ormik explore", "ormik 2025", "apa itu ormik", "ormik apa", "tentang ormik", "pengertian ormik",
            "guidebook", "guide book", "buku panduan", "rundown", "download", "unduh",
            "stt nurul fikri", "stt nf", "nurul fikri", "zeero",
            "jadwal", "schedule", "tanggal", "waktu", "kapan", "jam", "hari",
            "divisi", "organisasi", "panitia", "steering", "project officer", "po", "sekretaris", "bendahara", "public relation", "pr", "liaison", "lo", "event", "media", "kreatif", "kedisiplinan", "kedis", "mentor", "logistik", "konsumsi", "konsum", "medis", "it support", "it",
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
        intent = self._resolve_intent(s)
        if intent == "guidebook":
            k = self.context['ormikData']['kampus']
            return (
                "📖 **Guidebook ORMIK Explore 2025**\n\n"
                "**Download Guidebook Lengkap:**\n"
                f"{k['guidebook_url']}\n\n"
                "🔗 **Cara Download:**\n"
                "• Klik link di atas untuk langsung mengunduh guidebook\n"
                "• File akan otomatis terdownload ke perangkat Anda\n"
                "• Guidebook berisi rundown lengkap, aturan, dan panduan ORMIK\n\n"
                "📋 **Isi Guidebook:**\n"
                "• Jadwal kegiatan detail\n"
                "• Aturan dan tata tertib\n"
                "• Dress code dan atribut\n"
                "• Tugas dan penugasan\n"
                "• Informasi penting lainnya\n\n"
                "Pastikan baca guidebook sebelum mengikuti ORMIK ya! 📚\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal atau tips persiapan?"
            )
        if intent == "ormik":
            ormik_info = self.get_ormik_info("tentang_ormik")
            return (
                "🎓 **Apa itu ORMIK?**\n\n"
                f"**{ormik_info['nama_lengkap']}**\n"
                f"**Institusi:** {ormik_info['institusi']}\n\n"
                f"**Deskripsi:** {ormik_info['deskripsi']}\n\n"
                f"**Nama Acara:** {ormik_info['nama_acara']} {ormik_info['tahun']}\n"
                f"**Visi:** {ormik_info['visi']}\n\n"
                "ORMIK adalah kegiatan wajib yang harus diikuti oleh semua mahasiswa baru STT Terpadu Nurul Fikri untuk beradaptasi dengan lingkungan kampus dan sistem perkuliahan.\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal ORMIK atau persyaratan peserta?"
            )
        
        if intent == "creator":
            return (
                "👨‍💻 **Tentang Pembuat ZEERO Agent**\n\n"
                "**Developer:** Tim Pengembang IT Support ORMIK EXPLORE 2025\n\n"
                "🚀 **ZEERO Agent** adalah AI assistant yang dikembangkan khusus untuk membantu mahasiswa baru STT Terpadu Nurul Fikri dalam memperoleh informasi lengkap tentang ORMIK Explore 2025.\n\n"
                "💡 **Fitur Unggulan:**\n"
                "• Respons cepat dan akurat 24/7\n"
                "• Informasi lengkap tentang ORMIK 2025\n"
                "• Interface yang user-friendly\n"
                "• Pemahaman konteks yang baik\n\n"
                "� **Dikembangkan oleh:** Tim IT Support ORMIK EXPLORE 2025\n\n"
                "Terima kasih telah menggunakan ZEERO Agent! 😊\n"
                "Ada yang ingin Anda tanyakan tentang ORMIK?"
            )
        
        if intent == "hak":
            hak_list = self.get_ormik_info("hak_peserta")
            return (
                "🎓 **Hak Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(hak_list)]) +
                "\n\nApakah Anda ingin tahu juga kewajiban peserta?"
            )
        if intent == "kewajiban":
            kewajiban_list = self.get_ormik_info("kewajiban_peserta")
            return (
                "📘 **Kewajiban Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(kewajiban_list)]) +
                "\n\nApakah Anda ingin tahu juga hak peserta?"
            )
        if intent == "ketentuan":
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
        if intent == "perizinan":
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
        if intent == "tugas":
            if "day 1" in s or "day1" in s:
                individu = self.get_ormik_info("tugas", "individu", "day_1")
                kompi = self.get_ormik_info("tugas", "kompi", "day_1")
                response = "📝 **Tugas Day 1 ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx2+1}. {item}" for idx2, item in enumerate(kompi)])
                return response + "\n\nApakah Anda ingin tahu juga tugas di Pra ORMIK atau Last Day?"
            elif "last" in s or "akhir" in s:
                individu = self.get_ormik_info("tugas", "individu", "last_day")
                kompi = self.get_ormik_info("tugas", "kompi", "last_day")
                response = "📝 **Tugas Last Day ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx2+1}. {item}" for idx2, item in enumerate(kompi)])
                return response + "\n\nApakah Anda ingin tahu juga tugas di Pra ORMIK atau Day 1?"
            elif "pra" in s or "ormik" in s:
                individu = self.get_ormik_info("tugas", "individu", "pra_ormik")
                kompi = self.get_ormik_info("tugas", "kompi", "pra_ormik")
                response = "📝 **Tugas Pra ORMIK 2025:**\n\n**Individu:**\n" + "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(individu)]) + "\n\n**Kompi:**\n" + "\n".join([f"{idx2+1}. {item}" for idx2, item in enumerate(kompi)])
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
        if intent == "greetings":
            # Check if it's the first interaction or user is asking about ZEERO specifically
            if "zeero" in s.lower() or "siapa kamu" in s.lower() or "kamu siapa" in s.lower():
                return (
                    "Halo! Saya **ZEERO** 🤖 - **Z**one **E**ducational **E**xploration **R**obot **O**rganizer!\n\n"
                    "🎯 **Saya adalah AI Assistant khusus untuk ORMIK Explore 2025** yang dikembangkan oleh **Tim Pengembang IT Support ORMIK EXPLORE 2025**.\n\n"
                    "✨ **Yang bisa saya bantu:**\n"
                    "• 📅 **Jadwal** lengkap kegiatan ORMIK\n"
                    "• 👥 **Divisi & Organisasi** panitia\n"
                    "• 📍 **Lokasi** kampus & fasilitas\n"
                    "• 📞 **Kontak** informasi penting\n"
                    "• 💡 **Tips & Panduan** persiapan\n"
                    "• 👔 **Dress Code** & atribut\n"
                    "• 📚 **Guidebook** & materi\n"
                    "• ⚖️ **Aturan & Tata Tertib**\n\n"
                    "🚀 **Saya siap membantu 24/7 dengan respons yang cepat dan akurat!**\n\n"
                    "Tanya dengan kata kunci seperti `jadwal`, `divisi`, `lokasi`, `kontak`, atau `tips`! 😊"
                )
            else:
                # Simple greeting response
                return (
                    "Halo! Saya **ZEERO** 🤖, AI Assistant untuk ORMIK Explore 2025!\n\n"
                    "Saya siap bantu info tentang:\n"
                    "• 📅 **Jadwal** kegiatan ORMIK\n"
                    "• 👥 **Struktur organisasi** dan divisi\n"
                    "• 📍 **Lokasi** & fasilitas kampus\n"
                    "• 📞 **Kontak** informasi\n"
                    "• 💡 **Tips** & panduan\n"
                    "• 👔 **Dress code** & persiapan\n\n"
                    "Tanya dengan kata kunci seperti `jadwal`, `divisi`, `lokasi`, atau `tips`! 😊"
                )

        if intent == "jadwal":
            lines = [f"• **{x['title']}** - {x['date']}" for x in self.context['ormikData']['schedule']]
            k = self.context['ormikData']['kampus']
            
            # Check if user is asking about specific time-related aspects
            current_date = "11 September 2025"  # Current date context
            s_lower = s.lower()
            
            base_response = "📅 **Jadwal ORMIK Explore 2025:**\n\n" + "\n".join(lines) + "\n\n"
            
            if "jam" in s_lower or "waktu" in s_lower or "berapa" in s_lower:
                base_response += (
                    "⏰ **Detail Waktu:**\n"
                    "• **Jam Kedatangan:** 06:30 WIB (WAJIB tepat waktu)\n"
                    "• **Registrasi Ulang:** 06:00 WIB (30 menit sebelumnya)\n"
                    "• **Kegiatan Dimulai:** 07:00 WIB\n"
                    "• **Durasi:** Full day (06:30 - selesai)\n\n"
                    "⚠️ **PENTING:** Keterlambatan akan dikenakan sanksi sesuai tata tertib!\n\n"
                )
            else:
                base_response += (
                    "⏰ **Waktu:**\n• Peserta wajib datang tepat waktu pada pukul **06:30 WIB** sesuai tata tertib.\n"
                    "• Registrasi ulang 30 menit sebelumnya\n"
                    "• Pastikan datang tepat waktu ya!\n\n"
                )
            
            if "download" in s_lower or "unduh" in s_lower or "guidebook" in s_lower:
                base_response += (
                    f"📖 **Guidebook & Rundown Lengkap:**\n"
                    f"🔗 {k['guidebook_url']}\n"
                    "*(Klik link di atas untuk langsung mengunduh guidebook PDF)*\n\n"
                    "📋 **Isi Guidebook:**\n"
                    "• Rundown detail setiap hari\n"
                    "• Informasi lokasi dan ruangan\n"
                    "• Aturan dan ketentuan lengkap\n\n"
                )
            else:
                base_response += (
                    f"📖 **Guidebook:** Unduh guidebook ORMIK untuk rundown lengkap di: {k['guidebook_url']}\n"
                    "*(Klik link di atas untuk langsung mengunduh guidebook)*\n\n"
                )
            
            base_response += "💡 **Ingin tahu lebih lanjut?** Tanyakan tentang lokasi kampus, tips persiapan, atau divisi panitia!"
            
            return base_response

        if intent == "divisi":
            # Check if user is asking for specific division
            s_lower = s.lower()
            
            # Check for specific division keywords
            division_keywords = {
                "steering": "steering_committee",
                "project officer": "project_officer",
                "po": "project_officer",
                "sekretaris": "sekretaris",
                "bendahara": "bendahara",
                "public relation": "public_relation",
                "pr": "public_relation",
                "liaison": "liaison_officer",
                "lo": "liaison_officer",
                "event": "event",
                "media": "media",
                "kreatif": "kreatif",
                "kedisiplinan": "kedisiplinan",
                "kedis": "kedisiplinan",
                "mentor": "mentor",
                "logistik": "logistik",
                "konsumsi": "konsumsi",
                "konsum": "konsumsi",
                "medis": "medis",
                "it support": "it_support",
                "it": "it_support"
            }
            
            # Find specific division being asked - prioritize longer matches first
            specific_division = None
            # Sort keywords by length (longest first) to prioritize exact matches
            sorted_keywords = sorted(division_keywords.items(), key=lambda x: len(x[0]), reverse=True)
            
            for keyword, division_key in sorted_keywords:
                # Use word boundary matching for short keywords to avoid false positives
                if len(keyword) <= 2:
                    # For very short keywords, check if they appear as separate words
                    import re
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, s_lower):
                        specific_division = division_key
                        break
                else:
                    # For longer keywords, use substring matching
                    if keyword in s_lower:
                        specific_division = division_key
                        break
            
            # If specific division is asked, show detailed info
            if specific_division:
                div_info = self.get_ormik_info("divisi", specific_division)
                return (
                    f"👥 **{div_info['position']} - ORMIK 2025**\n\n"
                    f"**📋 Deskripsi Tugas:**\n"
                    f"{div_info['description']}\n\n"
                    "Ingin tahu tentang divisi lain? Tanyakan nama divisinya!\n\n"
                    "Apakah Anda ingin tahu juga tentang jadwal kegiatan atau kontak panitia?"
                )
            
            # If general question, show overview
            return (
                "👥 **Struktur Organisasi ORMIK 2025:**\n\n"
                "**🏆 Core Team:**\n"
                "• Steering Committee\n• Project Officer (PO)\n• Sekretaris\n• Bendahara\n• Public Relation (PR)\n• Liaison Officer (LO)\n\n"
                "**⚡ Divisi Operasional:**\n"
                "• Event\n• Media\n• Kreatif\n• Kedisiplinan\n• Mentor\n• Logistik\n• Konsumsi\n• Medis\n• IT Support\n\n"
                "💡 **Ingin tahu detail divisi tertentu?**\n"
                "Tanyakan dengan menyebut nama divisinya, contoh:\n"
                "• 'Divisi Event'\n• 'Tugas Media'\n• 'Apa itu Mentor?'\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal kegiatan atau lokasi kampus?"
            )

        if intent == "lokasi":
            k = self.context['ormikData']['kampus']
            return (
                "🏫 **Lokasi Kegiatan ORMIK:**\n\n"
                f"**{k['nama']}**\n"
                f"📍 {k['alamat']}, {k['kota']}, {k['provinsi']}\n\n"
                "🗺️ **Fasilitas:** Auditorium, ruang kelas ber-AC, lab komputer, Masjid Al-Hikmah, kantin, area parkir.\n\n"
                "🚌 **Akses:** TransJakarta (Lenteng Agung), KRL (Stasiun Lenteng Agung), angkot Pasar Minggu–Bogor.\n"
                f"📍 **Google Maps:** {k['maps_url']}\n\n"
                "Apakah Anda ingin tahu juga tentang jadwal kegiatan atau kontak panitia?"
            )

        if intent == "kontak":
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
                f"• Website: {k['website']}\n"
                f"• YouTube: {k['youtube']}\n\n"
                "Apakah Anda ingin tahu juga tentang lokasi kampus atau jadwal kegiatan?"
            )

        if intent == "tips":
            k = self.context['ormikData']['kampus']
            s_lower = s.lower()
            
            # Contextual tips based on user's specific question
            if "persiapan" in s_lower or "sebelum" in s_lower:
                return (
                    "🎯 **Tips Persiapan ORMIK 2025:**\n\n"
                    "📚 **H-3 sampai H-1:**\n"
                    "• Download & baca guidebook lengkap\n"
                    "• Siapkan dress code sesuai ketentuan\n"
                    "• Cek ulang jadwal dan lokasi\n"
                    "• Istirahat cukup (min. 7-8 jam)\n"
                    "• Siapkan mental positif & semangat!\n\n"
                    "⏰ **Malam sebelumnya:**\n"
                    "• Siapkan tas dengan atribut lengkap\n"
                    "• Set alarm untuk bangun lebih pagi\n"
                    "• Cek kondisi cuaca untuk antisipasi\n"
                    "• Charge HP dan power bank\n\n"
                    f"📖 **Guidebook:** {k['guidebook_url']}\n"
                    "💡 **Next:** Tanyakan tentang `dress code` atau `atribut`!"
                )
            elif "selama" in s_lower or "saat" in s_lower:
                return (
                    "🚀 **Tips Selama ORMIK 2025:**\n\n"
                    "⏰ **Kedatangan:**\n"
                    "• Datang TEPAT WAKTU pukul 06:30 WIB\n"
                    "• Registrasi ulang 30 menit sebelumnya\n"
                    "• Bawa semua atribut yang diperlukan\n\n"
                    "🤝 **Interaksi:**\n"
                    "• Aktif berpartisipasi dalam kegiatan\n"
                    "• Ramah dengan sesama peserta\n"
                    "• Hormati mentor dan panitia\n"
                    "• Berani bertanya jika ada yang bingung\n\n"
                    "✨ **Mindset Positif:**\n"
                    "• Terbuka dengan hal-hal baru\n"
                    "• Nikmati setiap proses pembelajaran\n"
                    "• Jaga kebersihan dan ketertiban\n"
                    "• Bangun networking yang baik\n\n"
                    "� **Ingin tips spesifik lainnya?** Tanyakan tentang `dress code` atau `punishment`!"
                )
            else:
                # Comprehensive tips response
                return (
                    "💡 **Tips Sukses ORMIK 2025:**\n\n"
                    "🎯 **Sebelum Kegiatan:**\n"
                    "• 📚 Baca guidebook dari awal sampai akhir\n"
                    "• 👔 Siapkan dress code sesuai ketentuan\n"
                    "• 😴 Istirahat cukup (min. 7-8 jam)\n"
                    "• 📅 Cek jadwal dan lokasi dengan teliti\n"
                    "• 🎒 Siapkan tas dengan atribut lengkap\n\n"
                    "🚀 **Selama Kegiatan:**\n"
                    "• ⏰ Datang TEPAT WAKTU pukul 06:30 WIB\n"
                    "• 🤝 Aktif, ramah, dan hormati semua orang\n"
                    "• 🙋‍♀️ Berani bertanya jika ada yang bingung\n"
                    "• 🧹 Jaga kebersihan dan ketertiban\n"
                    "• 📱 Dokumentasikan momen-momen penting\n\n"
                    "✨ **Mindset Positif:**\n"
                    "• Terbuka dengan pengalaman baru 🌟\n"
                    "• Nikmati setiap proses pembelajaran 📈\n"
                    "• Bangun networking yang baik 🤝\n\n"
                    f"📖 **Guidebook Lengkap:** {k['guidebook_url']}\n"
                    "💡 **Mau tips spesifik?** Tanyakan `tips persiapan` atau `tips selama ormik`!"
                )

        if intent == "dress":
            return (
                "👔 **Dress Code ORMIK 2025:**\n\n"
                "**Putra:** Kemeja putih (dimasukkan), celana hitam/dongker, ikat pinggang hitam, kaos kaki putih, sepatu hitam. Rambut rapi, tanpa cat.\n"
                "**Putri:** Kemeja putih longgar, rok bahan hingga mata kaki, kaos kaki putih, sepatu hitam. Muslim jilbab segiempat+ciput; non‑Muslim rambut diikat.\n"
                "**Dilarang:** Aksesori berlebihan, make up berlebih, softlens berwarna.\n\n"
                "Apakah Anda ingin tahu juga tentang tips persiapan atau atribut yang perlu dibawa?"
            )

        if intent == "tata_tertib":
            tertib_list = self.get_ormik_info("tata_tertib")
            return (
                "📋 **Tata Tertib Peserta ORMIK 2025:**\n" +
                "\n".join([f"{idx+1}. {item}" for idx, item in enumerate(tertib_list)]) +
                "\n\nApakah Anda ingin tahu juga tentang punishment atau hak peserta?"
            )

        if intent == "punishment":
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

        if intent == "atribut":
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
        text_lower = text.lower().strip()
        
        # Normalize text - remove extra spaces and special characters for better matching
        normalized_text = re.sub(r'[^\w\s]', ' ', text_lower)
        normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()
        
        # Sort keywords by length (longest first) for better phrase matching
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        
        # Check for exact phrase matches first (highest priority)
        for keyword in sorted_keywords:
            keyword_lower = keyword.lower().strip()
            normalized_keyword = re.sub(r'[^\w\s]', ' ', keyword_lower)
            normalized_keyword = re.sub(r'\s+', ' ', normalized_keyword).strip()
            
            # Exact phrase match in original text
            if keyword_lower in text_lower:
                return True
            
            # Exact phrase match in normalized text
            if normalized_keyword in normalized_text:
                return True
        
        # For single word keywords, check if they appear as whole words
        text_words = re.findall(r'\b\w+\b', normalized_text)
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            # If keyword is a single word, check for exact word match
            if ' ' not in keyword_lower and keyword_lower in text_words:
                return True
        
        # Fuzzy matching for common typos (only for longer keywords to avoid false positives)
        for keyword in sorted_keywords:
            if len(keyword) > 4:  # Only apply fuzzy matching to longer keywords
                keyword_lower = keyword.lower().strip()
                # Check if keyword appears with minor variations (1 character difference)
                if self._fuzzy_match(normalized_text, keyword_lower):
                    return True
                    
        return False
    
    def _fuzzy_match(self, text: str, keyword: str) -> bool:
        """Check for fuzzy match with edit distance of 1 for keywords > 4 characters"""
        import difflib
        text_words = text.split()
        
        # Check if any word in text is similar to keyword
        for word in text_words:
            if len(word) > 3 and len(keyword) > 3:
                # Calculate similarity ratio
                similarity = difflib.SequenceMatcher(None, word, keyword).ratio()
                if similarity >= 0.8:  # 80% similarity threshold
                    return True
        
        # Check if keyword appears in text with minor variations
        close_matches = difflib.get_close_matches(keyword, text_words, n=1, cutoff=0.8)
        return len(close_matches) > 0

    def _resolve_intent(self, text: str) -> str | None:
        intents = {
            "creator": ["tim pengembang", "pembuat", "developer", "creator", "pencipta", "siapa yang buat", "who created", "who made", "it support ormik"],
            "greetings": ["halo", "hai", "hello", "zeero apa", "siapa kamu", "kamu siapa", "perkenalan", "intro"],
            "jadwal": ["jadwal", "schedule", "tanggal", "waktu", "kapan", "jam", "hari", "berapa", "mulai", "selesai"],
            "divisi": ["divisi", "struktur", "organisasi", "tim", "steering", "project officer", "po", "sekretaris", "bendahara", "public relation", "pr", "liaison", "lo", "event", "media", "kreatif", "kedisiplinan", "kedis", "mentor", "logistik", "konsumsi", "konsum", "medis", "it support", "it"],
            "lokasi": ["lokasi", "kampus", "tempat", "alamat", "fasilitas", "dimana", "di mana", "gedung", "ruangan", "parkir"],
            "kontak": ["kontak", "contact", "hubungi", "telepon", "whatsapp", "email", "instagram", "cp", "nomor", "wa"],
            "tips": ["tips", "saran", "panduan", "cara", "bagaimana", "strategi", "persiapan", "advice"],
            "dress": ["dress", "pakaian", "baju", "seragam", "outfit", "kostum", "berpakaian"],
            "tata_tertib": ["tata tertib", "peraturan", "tertib", "tata", "aturan", "rule"],
            "punishment": ["punishment", "hukuman", "sanksi", "pelanggaran", "hukum", "sanksi apa", "denda"],
            "atribut": ["atribut", "perlengkapan", "barang", "bawa", "perlu", "bawa apa", "apa yang dibawa", "kelengkapan"],
            "tugas": ["tugas", "assignment", "kerjaan", "kerja", "tugas apa", "pekerjaan", "job"],
            "ketentuan": ["ketentuan", "putra", "putri", "dress code", "syarat", "requirement"],
            "perizinan": ["perizinan", "izin", "izinan", "tidak hadir", "absen"],
            "kewajiban": ["kewajiban", "wajib", "kewajiban peserta", "harus", "must"],
            "hak": ["hak", "hak peserta", "boleh", "dapat", "bisa"],
            "guidebook": ["guidebook", "guide book", "buku panduan", "panduan", "rundown", "download", "unduh", "pdf"],
            "ormik": ["ormik sttnf", "ormik explore", "ormik 2025", "apa itu ormik", "tentang ormik", "pengertian ormik", "definisi ormik", "orientasi"],
        }
        
        matches = []
        for cat, words in intents.items():
            if self._has_keyword(text, words):
                matches.append(cat)
        
        if not matches:
            return None
        
        # Handle specific combinations and context first
        text_lower = text.lower()
        
        # Helper function for whole word matching in combinations
        def has_whole_word(text: str, words: list) -> bool:
            import re
            for word in words:
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, text):
                    return True
            return False
        
        # Creator-specific combinations
        if "creator" in matches and has_whole_word(text_lower, ["pembuat", "developer", "creator", "tim pengembang"]):
            return "creator"
            
        # Contact-specific combinations (use whole word matching to avoid false positives)
        if "kontak" in matches and (has_whole_word(text_lower, ["panitia", "whatsapp"]) or "nomor" in text_lower or "cp " in text_lower):
            return "kontak"
            
        # Schedule-specific combinations  
        if "jadwal" in matches and has_whole_word(text_lower, ["hari", "tanggal", "kapan", "jam", "waktu", "berapa", "mulai", "selesai"]):
            return "jadwal"
            
        # Division-specific combinations
        if "divisi" in matches and has_whole_word(text_lower, ["struktur", "organisasi", "tim", "panitia"]):
            return "divisi"
            
        # Location-specific combinations
        if "lokasi" in matches and has_whole_word(text_lower, ["kampus", "alamat", "gedung", "parkir", "fasilitas"]):
            return "lokasi"
            
        # Tips-specific combinations
        if "tips" in matches and has_whole_word(text_lower, ["persiapan", "strategi", "cara", "panduan"]):
            return "tips"
            
        # Dress code combinations
        if ("dress" in matches or "ketentuan" in matches) and has_whole_word(text_lower, ["pakaian", "baju", "seragam", "outfit"]):
            return "dress"
            
        # Priority order - more specific intents first
        priority = [
            "creator",    # Highest priority for creator information
            "greetings",
            "guidebook",
            "jadwal", 
            "kontak",
            "lokasi", 
            "divisi",
            "tips",
            "dress",
            "tata_tertib",
            "punishment", 
            "atribut",
            "tugas",
            "ketentuan",
            "perizinan",
            "kewajiban",
            "hak",
            "ormik",  # Put ormik at the end with lowest priority
        ]
        
        # Sort matches by priority
        matches.sort(key=lambda c: priority.index(c))
        return matches[0]

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
                    "website": "https://nurulfikri.ac.id",
                    "maps_url": "https://maps.app.goo.gl/jnG4mhZV8QJDLdbNA",
                    "youtube": "https://www.youtube.com/@STTNF",
                    "guidebook_url": "https://drive.usercontent.google.com/u/1/uc?id=1dicryzEqjhbPcSGXx02x9t2ULLRTb7oT&export=download"
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
