import altair as alt
import pandas as pd
import streamlit as st
from pymongo import MongoClient


# ============================================================
# KONEKSI MONGODB
# ============================================================
@st.cache_resource
def koneksi_mongodb():
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")

    db = client["dashboard_thermal"]
    return db["konten_dashboard"]


# ============================================================
# MENGAMBIL KONTEN DARI MONGODB
# ============================================================
def ambil_konten(id_konten):
    collection = koneksi_mongodb()
    return collection.find_one({"_id": id_konten})


# ============================================================
# MENAMPILKAN KONTEN
# ============================================================
def tampilkan_konten(id_konten):
    try:
        data = ambil_konten(id_konten)

        if data is None:
            st.warning("Konten belum ditemukan di MongoDB.")
            return

        st.subheader(data["judul"])
        st.write(data["isi"])

        # Menampilkan poin-poin
        if "poin" in data:
            for poin in data["poin"]:
                st.markdown(f"- {poin}")

        # Menampilkan tabel perbandingan
        if "perbandingan" in data:
            st.dataframe(
                pd.DataFrame(data["perbandingan"]),
                hide_index=True,
                use_container_width=True
            )

        # Menampilkan pembahasan hasil analisis
        if "pembahasan" in data:
            for bagian in data["pembahasan"]:
                st.markdown(f"**{bagian['judul']}**")
                st.write(bagian["isi"])

    except Exception as e:
        st.error(f"Gagal mengambil data dari MongoDB: {e}")


# ============================================================
# LOGIKA JAWABAN CHATBOT

# ============================================================
# LOGIKA JAWABAN CHATBOT
# ============================================================
def jawab_chatbot(pertanyaan):
    teks = pertanyaan.lower().strip()
    teks = teks.strip("!?., ")

    # 1. Sapaan awal
    sapaan = [
        "hai", "halo", "hi", "hello", "helo",
        "p", "assalamualaikum", "selamat pagi",
        "selamat siang", "selamat sore", "selamat malam"
    ]

    if teks in sapaan:
        id_konten = "sapaan_awal"

    # 2. Perbedaan WBGT dan Heat Index
    elif any(k in teks for k in [
        "perbedaan", "beda", "bandingkan", "dibandingkan"
    ]):
        id_konten = "perbedaan"

    # 3. Hasil analisis
    elif any(k in teks for k in [
        "hasil analisis", "hasil penelitian",
        "pembahasan", "hasil pengamatan", "temuan"
    ]):
        id_konten = "hasil_analisis"

    # 4. Heat Index
    elif any(k in teks for k in [
        "heat index", "heat-index", "indeks panas"
    ]):
        id_konten = "heat_index"

    # 5. WBGT
    elif any(k in teks for k in [
        "wbgt", "tekanan panas", "heat stress"
    ]):
        id_konten = "wbgt"

    else:
        return (
            "Maaf, aku belum menemukan topik yang sesuai. 😊\n\n"
            "Kamu bisa bertanya tentang WBGT, Heat Index, "
            "perbedaan keduanya, atau hasil analisis."
        )

    # Ambil dokumen dari MongoDB
    data = ambil_konten(id_konten)

    if data is None:
        return (
            f"Maaf, dokumen '{id_konten}' belum ditemukan "
            "di MongoDB."
        )

    # Susun jawaban
    jawaban = f"**{data['judul']}**\n\n{data['isi']}"

    if "poin" in data:
        jawaban += "\n\n" + "\n".join(
            f"- {poin}" for poin in data["poin"]
        )

    if "perbandingan" in data:
        for item in data["perbandingan"]:
            jawaban += (
                f"\n\n**{item['aspek']}**\n"
                f"- WBGT: {item['wbgt']}\n"
                f"- Heat Index: {item['heat_index']}"
            )

    if "pembahasan" in data:
        for bagian in data["pembahasan"]:
            jawaban += (
                f"\n\n**{bagian['judul']}**\n"
                f"{bagian['isi']}"
            )

    return jawaban

# ============================================================
# TAMPILAN CHATBOT

# ============================================================
# TAMPILAN CHATBOT
# ============================================================
def render_chatbot():
    st.title("Chatbot")

    st.write(
        "Tanyakan sesuatu tentang WBGT, Heat Index, "
        "perbedaan keduanya, atau hasil analisis."
    )

    # Sapaan awal diambil dari MongoDB
    if "riwayat_chat" not in st.session_state:
        try:
            data_sapaan = ambil_konten("sapaan_awal")

            if data_sapaan:
                pesan_awal = data_sapaan["isi"]
            else:
                pesan_awal = (
                    "Hai! 👋 Ada yang ingin kamu tanyakan?"
                )

        except Exception:
            pesan_awal = (
                "Hai! 👋 Ada yang ingin kamu tanyakan?"
            )

        st.session_state.riwayat_chat = [
            {
                "role": "assistant",
                "content": pesan_awal
            }
        ]

    # Tampilkan riwayat percakapan
    for pesan in st.session_state.riwayat_chat:
        with st.chat_message(pesan["role"]):
            st.markdown(pesan["content"])

    # Input pengguna
    pertanyaan = st.chat_input(
        "Ketik pertanyaanmu di sini..."
    )

    if pertanyaan:
        st.session_state.riwayat_chat.append({
            "role": "user",
            "content": pertanyaan
        })

        with st.chat_message("user"):
            st.markdown(pertanyaan)

        try:
            jawaban = jawab_chatbot(pertanyaan)
        except Exception as e:
            jawaban = (
                "Maaf, terjadi kendala saat mengambil data "
                f"dari MongoDB: {e}"
            )

        st.session_state.riwayat_chat.append({
            "role": "assistant",
            "content": jawaban
        })

        with st.chat_message("assistant"):
            st.markdown(jawaban)

# ---------------------------------------------------------------
# DATA (hasil agregasi dari analisis)
# ---------------------------------------------------------------
BULAN = ["Mei", "Juni", "Juli", "Agustus"]
FASE = ["La Niña", "Netral", "El Niño"]

ZONA_LABEL = {
    "Semarang": "Dataran rendah utara (Semarang)",
    "Kutoarjo": "Dataran rendah selatan (Kutoarjo)",
    "Wonosobo": "Dataran tinggi tengah (Wonosobo)",
}

WARNA_ZONA = {"Semarang": "#4c72b0", "Kutoarjo": "#dd8452", "Wonosobo": "#55a868"}
WARNA_ENSO = {"La Niña": "#2a78d6", "Netral": "#9a9a9a", "El Niño": "#d03b3b"}

# Rata-rata bulanan: indikator -> zona -> tahun -> [Mei, Juni, Juli, Agustus]
BULANAN = {
    "Heat Index": {
        "Semarang": {
            2022: [32.33, 30.51, 30.21, 30.16],
            2024: [34.57, 32.36, 30.33, 31.16],
            2026: [33.27, 32.59, 30.61, 31.21],
        },
        "Kutoarjo": {
            2022: [32.88, 30.70, 29.56, 30.76],
            2024: [29.56, 29.95, 27.19, 27.09],
            2026: [33.87, 30.88, 28.19, 28.95],
        },
        "Wonosobo": {
            2022: [20.05, 19.07, 18.34, 18.32],
            2024: [19.49, 19.00, 17.79, 18.13],
            2026: [19.39, 18.38, 17.02, 17.63],
        },
    },
    "WBGT": {
        "Semarang": {
            2022: [31.09, 30.57, 30.89, 31.49],
            2024: [33.12, 31.41, 30.93, 32.07],
            2026: [32.05, 31.97, 31.34, 32.05],
        },
        "Kutoarjo": {
            2022: [31.33, 29.89, 28.72, 29.10],
            2024: [30.42, 30.36, 28.93, 28.67],
            2026: [32.18, 30.94, 29.95, 30.28],
        },
        "Wonosobo": {
            2022: [21.73, 20.60, 20.15, 20.04],
            2024: [21.95, 21.14, 20.50, 20.42],
            2026: [21.40, 21.22, 20.06, 21.74],
        },
    },
}

# Rata-rata per fase ENSO: indikator -> zona -> fase -> nilai
ENSO = {
    "Heat Index": {
        "Semarang": {"La Niña": 30.67, "Netral": 32.25, "El Niño": 31.79},
        "Kutoarjo": {"La Niña": 30.76, "Netral": 28.42, "El Niño": 30.20},
        "Wonosobo": {"La Niña": 18.82, "Netral": 18.64, "El Niño": 18.00},
    },
    "WBGT": {
        "Semarang": {"La Niña": 31.01, "Netral": 32.01, "El Niño": 31.83},
        "Kutoarjo": {"La Niña": 29.58, "Netral": 29.59, "El Niño": 30.73},
        "Wonosobo": {"La Niña": 20.52, "Netral": 21.05, "El Niño": 21.07},
    },
}


@st.cache_data
def muat_bulanan() -> pd.DataFrame:
    baris = []
    for ind, per_zona in BULANAN.items():
        for zona, per_tahun in per_zona.items():
            for tahun, nilai in per_tahun.items():
                for b, v in zip(BULAN, nilai):
                    baris.append(
                        {
                            "Indikator": ind,
                            "Zona": zona,
                            "Tahun": str(tahun),
                            "Bulan": b,
                            "Nilai": v,
                        }
                    )
    return pd.DataFrame(baris)


@st.cache_data
def muat_enso() -> pd.DataFrame:
    baris = []
    for ind, per_zona in ENSO.items():
        for zona, per_fase in per_zona.items():
            for fase, v in per_fase.items():
                baris.append(
                    {
                        "Indikator": ind,
                        "Zona": zona,
                        "Fase ENSO": fase,
                        "Nilai": v,
                    }
                )
    return pd.DataFrame(baris)


# ---------------------------------------------------------------
# TAB DASHBOARD
# ---------------------------------------------------------------
def render_dashboard():
    df_bulanan = muat_bulanan()
    df_enso = muat_enso()

    st.title("Dashboard Heat Index dan WBGT")
    st.caption(
        "Perbandingan tiga zona topografi, Mei sampai Agustus "
        "(2022, 2024, 2026)"
    )

    # ---------- Filter (di dalam tab, bukan sidebar) ----------
    with st.container(border=True):
        st.markdown("**Filter**")

        f1, f2 = st.columns([1, 2])
        indikator = f1.radio(
            "Indikator",
            ["Heat Index", "WBGT"],
            horizontal=True,
            key="dash_indikator",
        )
        zona_pilih = f2.multiselect(
            "Zona topografi",
            options=list(ZONA_LABEL),
            default=list(ZONA_LABEL),
            format_func=lambda z: ZONA_LABEL[z],
            key="dash_zona",
        )

        f3, f4, f5 = st.columns(3)
        tahun_opsi = sorted(df_bulanan["Tahun"].unique())
        tahun_pilih = f3.multiselect(
            "Tahun",
            options=tahun_opsi,
            default=tahun_opsi,
            key="dash_tahun",
        )
        bulan_pilih = f4.multiselect(
            "Bulan",
            options=BULAN,
            default=BULAN,
            key="dash_bulan",
        )
        fase_pilih = f5.multiselect(
            "Fase ENSO",
            options=FASE,
            default=FASE,
            key="dash_fase",
        )

        st.caption(
            "Tahun dan bulan berlaku di sub-tab Per bulan. "
            "Fase ENSO berlaku di sub-tab Fase ENSO. "
            "Indikator dan zona berlaku di semua sub-tab."
        )

    if not zona_pilih:
        st.warning("Pilih minimal satu zona pada filter di atas.")
        return

    # ---------- Data terfilter ----------
    d_bulan = df_bulanan[
        (df_bulanan["Indikator"] == indikator)
        & (df_bulanan["Zona"].isin(zona_pilih))
        & (df_bulanan["Tahun"].isin(tahun_pilih))
        & (df_bulanan["Bulan"].isin(bulan_pilih))
    ]

    d_enso = df_enso[
        (df_enso["Indikator"] == indikator)
        & (df_enso["Zona"].isin(zona_pilih))
        & (df_enso["Fase ENSO"].isin(fase_pilih))
    ]

    sub1, sub2, sub3 = st.tabs(
        ["Per bulan", "Fase ENSO", "Tabel data"]
    )

    # ---------- Sub-tab 1: per bulan ----------
    with sub1:
        if d_bulan.empty:
            st.warning(
                "Tidak ada data untuk kombinasi tahun dan bulan yang dipilih."
            )
        else:
            # PERUBAHAN HANYA DI BAGIAN METRIK:
            # Cari maksimum dan minimum langsung dari nilai yang terfilter,
            # bukan dari rata-rata yang dikelompokkan berdasarkan zona.
            nilai_rata = d_bulan["Nilai"].mean()
            nilai_tertinggi = d_bulan.loc[d_bulan["Nilai"].idxmax()]
            nilai_terendah = d_bulan.loc[d_bulan["Nilai"].idxmin()]

            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Rata-rata terpilih",
                f"{nilai_rata:.2f} °C",
            )
            c2.metric(
                f"Tertinggi: {nilai_tertinggi['Zona']}",
                f"{nilai_tertinggi['Nilai']:.2f} °C",
            )
            c3.metric(
                f"Terendah: {nilai_terendah['Zona']}",
                f"{nilai_terendah['Nilai']:.2f} °C",
            )

            jenis = st.radio(
                "Jenis grafik",
                ["Batang", "Garis"],
                horizontal=True,
                key="dash_jenis",
            )

            warna = alt.Scale(
                domain=list(WARNA_ZONA),
                range=list(WARNA_ZONA.values()),
            )
            encode_umum = dict(
                x=alt.X(
                    "Bulan:N",
                    sort=BULAN,
                    title=None,
                    axis=alt.Axis(labelAngle=0),
                ),
                color=alt.Color(
                    "Zona:N",
                    scale=warna,
                    legend=alt.Legend(
                        title="Zona topografi",
                        orient="bottom",
                    ),
                ),
                tooltip=[
                    alt.Tooltip("Zona:N"),
                    alt.Tooltip("Tahun:N"),
                    alt.Tooltip("Bulan:N"),
                    alt.Tooltip(
                        "Nilai:Q",
                        title=f"{indikator} (°C)",
                        format=".2f",
                    ),
                ],
            )
            judul_y = f"{indikator} rata-rata (°C)"

            if jenis == "Batang":
                chart = alt.Chart(d_bulan).mark_bar().encode(
                    y=alt.Y("Nilai:Q", title=judul_y),
                    xOffset=alt.XOffset("Zona:N"),
                    **encode_umum,
                )
            else:
                chart = alt.Chart(d_bulan).mark_line(
                    point=True,
                    strokeWidth=2.5,
                ).encode(
                    y=alt.Y(
                        "Nilai:Q",
                        title=judul_y,
                        scale=alt.Scale(zero=False),
                    ),
                    **encode_umum,
                )

            chart = chart.properties(
                width=230,
                height=340,
            ).facet(
                column=alt.Column("Tahun:N", title=None)
            )
            st.altair_chart(chart)

    # ---------- Sub-tab 2: fase ENSO ----------
    with sub2:
        if d_enso.empty:
            st.warning("Pilih minimal satu fase ENSO pada filter di atas.")
        else:
            warna_enso = alt.Scale(
                domain=list(WARNA_ENSO),
                range=list(WARNA_ENSO.values()),
            )
            dasar = alt.Chart(d_enso).encode(
                x=alt.X(
                    "Zona:N",
                    title=None,
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y(
                    "Nilai:Q",
                    title=f"{indikator} rata-rata (°C)",
                ),
                xOffset=alt.XOffset(
                    "Fase ENSO:N",
                    sort=FASE,
                ),
                color=alt.Color(
                    "Fase ENSO:N",
                    scale=warna_enso,
                    sort=FASE,
                    legend=alt.Legend(
                        title="Fase ENSO",
                        orient="bottom",
                    ),
                ),
                tooltip=[
                    alt.Tooltip("Zona:N"),
                    alt.Tooltip("Fase ENSO:N"),
                    alt.Tooltip(
                        "Nilai:Q",
                        title=f"{indikator} (°C)",
                        format=".2f",
                    ),
                ],
            )
            batang = dasar.mark_bar()
            label = dasar.mark_text(
                dy=-8,
                fontSize=12,
            ).encode(
                text=alt.Text("Nilai:Q", format=".2f")
            )
            st.altair_chart(
                (batang + label).properties(height=420)
            )

            st.caption(
                "Nilai fase ENSO adalah ringkasan per zona, jadi tidak bisa dipecah "
                "lagi menurut tahun atau bulan. Selisih antar-fase relatif kecil, "
                "sehingga perlu hati-hati menyimpulkan adanya pengaruh ENSO."
            )

    # ---------- Sub-tab 3: tabel data ----------
    with sub3:
        st.subheader(f"Rata-rata bulanan ({indikator})")
        tabel_bulan = d_bulan.drop(columns="Indikator").rename(
            columns={"Nilai": f"{indikator} (°C)"}
        )
        st.dataframe(tabel_bulan, hide_index=True)
        st.download_button(
            "Unduh tabel bulanan (CSV)",
            data=tabel_bulan.to_csv(index=False).encode("utf-8"),
            file_name=f"{indikator.lower().replace(' ', '_')}_bulanan.csv",
            mime="text/csv",
            key="dash_unduh_bulanan",
        )

        st.subheader(f"Rata-rata per fase ENSO ({indikator})")
        tabel_enso = d_enso.drop(columns="Indikator").rename(
            columns={"Nilai": f"{indikator} (°C)"}
        )
        st.dataframe(tabel_enso, hide_index=True)
        st.download_button(
            "Unduh tabel ENSO (CSV)",
            data=tabel_enso.to_csv(index=False).encode("utf-8"),
            file_name=f"{indikator.lower().replace(' ', '_')}_enso.csv",
            mime="text/csv",
            key="dash_unduh_enso",
        )




# ============================================================
# LOGIKA JAWABAN CHATBOT
# ============================================================
def jawab_chatbot(pertanyaan):
    teks = pertanyaan.lower().strip()

    if any(k in teks for k in [
        "perbedaan", "beda", "bandingkan", "dibandingkan"
    ]):
        id_konten = "perbedaan"

    elif any(k in teks for k in [
        "hasil analisis", "hasil penelitian",
        "pembahasan", "hasil pengamatan", "temuan"
    ]):
        id_konten = "hasil_analisis"

    elif any(k in teks for k in [
        "heat index", "heat-index", "indeks panas"
    ]):
        id_konten = "heat_index"

    elif any(k in teks for k in [
        "wbgt", "tekanan panas", "heat stress"
    ]):
        id_konten = "wbgt"

    else:
        return (
            "Maaf, aku belum menemukan topik yang sesuai. "
            "Coba tanyakan tentang WBGT, Heat Index, "
            "perbedaan keduanya, atau hasil analisis."
        )

    data = ambil_konten(id_konten)

    if data is None:
        return "Maaf, informasi tersebut belum tersedia di MongoDB."

    jawaban = f"**{data['judul']}**\n\n{data['isi']}"

    if "poin" in data:
        jawaban += "\n\n" + "\n".join(
            f"- {poin}" for poin in data["poin"]
        )

    if "perbandingan" in data:
        for item in data["perbandingan"]:
            jawaban += (
                f"\n\n**{item['aspek']}**\n"
                f"- WBGT: {item['wbgt']}\n"
                f"- Heat Index: {item['heat_index']}"
            )

    if "pembahasan" in data:
        for bagian in data["pembahasan"]:
            jawaban += (
                f"\n\n**{bagian['judul']}**\n"
                f"{bagian['isi']}"
            )

    return jawaban


# ============================================================
# TAMPILAN CHATBOT
# ============================================================
def render_chatbot():
    st.title("Chatbot")
    st.write(
        "Tanyakan sesuatu tentang WBGT, Heat Index, "
        "perbedaan keduanya, atau hasil analisis."
    )

    if "riwayat_chat" not in st.session_state:
        st.session_state.riwayat_chat = [
            {
                "role": "assistant",
                "content": (
                    "Halo! 👋 Ada yang ingin kamu tanyakan? "
                    "Silakan ketik pertanyaanmu di bawah."
                )
            }
        ]

    for pesan in st.session_state.riwayat_chat:
        with st.chat_message(pesan["role"]):
            st.markdown(pesan["content"])

    pertanyaan = st.chat_input("Ketik pertanyaanmu di sini...")

    if pertanyaan:
        st.session_state.riwayat_chat.append({
            "role": "user",
            "content": pertanyaan
        })

        with st.chat_message("user"):
            st.markdown(pertanyaan)

        try:
            jawaban = jawab_chatbot(pertanyaan)
        except Exception as e:
            jawaban = f"Terjadi kendala saat mengambil data: {e}"

        st.session_state.riwayat_chat.append({
            "role": "assistant",
            "content": jawaban
        })

        with st.chat_message("assistant"):
            st.markdown(jawaban)

# ============================================================
# APLIKASI UTAMA
# ============================================================
tab_dashboard, tab_chatbot = st.tabs(
    ["Dashboard", "Chatbot"]
)

with tab_dashboard:
    render_dashboard()

with tab_chatbot:
    render_chatbot()