
import streamlit as st
import pandas as pd
import altair as alt
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Sipariş Dashboard", layout="wide")

# streamlit run .\alfa_data_analysis\alfa_analysis_streamlit.py --server.port=8305


# ----------------------------
# DATA LOAD
# ----------------------------
@st.cache_data
def load_data():

    #df = pd.read_excel(
        #r"C:\Users\erkan\Desktop\Streamlit_learn\alfa_data_analysis\dataset\alfadatas.xlsx"
    #)

    df = pd.read_excel(
        r"dataset\alfadatas.xlsx"
    )

    date_cols = [
        "sip_tarih", "sip_onaytarih", "sip_sevktarih",
        "sip_ydssiptarih", "sip_ydssevktarih",
        "sip_gumrukvaristarih", "sip_fattarih"
    ]

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    return df


df = load_data()

st.title("📊 Sipariş Analiz 2025")

# ----------------------------
# TARİH FİLTRE
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    baslangic = st.date_input(
        "Başlangıç Tarihi",
        df["sip_onaytarih"].min()
    )

with col2:
    bitis = st.date_input(
        "Bitiş Tarihi",
        df["sip_onaytarih"].max()
    )

df_filtre = df[
    (df["sip_onaytarih"] >= pd.to_datetime(baslangic)) &
    (df["sip_onaytarih"] <= pd.to_datetime(bitis))
]

# ----------------------------
# KPI
# ----------------------------
toplam_siparis = df_filtre["sip_no"].nunique()
toplam_tutar = df_filtre["sip_tutar_indirimli"].sum()
toplam_musteri = df_filtre["sip_frmunvan"].nunique()

k1, k2, k3 = st.columns(3)

k1.metric("Toplam Sipariş", f"{toplam_siparis}")
k2.metric("Toplam Tutar (€)", f"{toplam_tutar:,.0f}")
k3.metric("Müşteri Sayısı", f"{toplam_musteri}")

st.divider()


# ----------------------------
# AYLIK GRAFİK
# ----------------------------
st.subheader("📈 Sipariş Tutarı - Aylık")

aylik_df = (
    df_filtre
    .groupby(pd.Grouper(key="sip_onaytarih", freq="MS"))["sip_tutar_indirimli"]
    .sum()
    .reset_index()
)

line = alt.Chart(aylik_df).mark_line(point=True).encode(
    x=alt.X("sip_onaytarih:T", title="Ay"),
    y=alt.Y("sip_tutar_indirimli:Q", title="Sipariş Tutarı (€)"),
    tooltip=[
        alt.Tooltip("sip_onaytarih:T", title="Ay"),
        alt.Tooltip("sip_tutar_indirimli:Q", title="Tutar (€)", format=",.0f")
    ]
)

text = alt.Chart(aylik_df).mark_text(dy=-10).encode(
    x="sip_onaytarih:T",
    y="sip_tutar_indirimli:Q",
    text=alt.Text("sip_tutar_indirimli:Q", format=",.0f")
)

st.altair_chart(line + text, use_container_width=True)

st.divider()

st.write("")
st.write("")
st.write("")


# ----------------------------
# ÜRÜN GRUBU BAR
# ----------------------------
st.subheader("📊 Ürün Grubu Dağılımı")

urun_df = (
    df_filtre
    .groupby("urn_snf1")["sip_tutar_indirimli"]
    .sum()
    .reset_index()
)

toplam = urun_df["sip_tutar_indirimli"].sum()

urun_df["oran_yuzde"] = (
    urun_df["sip_tutar_indirimli"] / toplam * 100
).round(1)

bars = alt.Chart(urun_df).mark_bar().encode(
    x=alt.X("urn_snf1:N", sort="-y", title="Ürün Grubu"),
    y=alt.Y("sip_tutar_indirimli:Q", title="Sipariş Tutarı (€)"),
    tooltip=[
        alt.Tooltip("urn_snf1", title="Ürün Grubu"),
        alt.Tooltip("sip_tutar_indirimli", title="Tutar (€)", format=",.0f"),
        alt.Tooltip("oran_yuzde", title="Oran (%)")
    ]
)

text = alt.Chart(urun_df).mark_text(dy=-10).encode(
    x=alt.X("urn_snf1:N", sort="-y"),
    y="sip_tutar_indirimli:Q",
    text=alt.Text("oran_yuzde:Q", format=".1f")
)

st.altair_chart(bars + text, use_container_width=True)

#####################################################################vv



urun_tablo = urun_df.copy()

urun_tablo["Tutar (€)"] = urun_tablo["sip_tutar_indirimli"].map(lambda x: f"{x:,.0f}")
urun_tablo["Oran (%)"] = urun_tablo["oran_yuzde"]

# Orana göre azalan sıralama
urun_tablo = urun_tablo.sort_values("oran_yuzde", ascending=False)

urun_tablo = urun_tablo[["urn_snf1","Tutar (€)","Oran (%)"]]
urun_tablo.columns = ["Ürün Grubu","Tutar (€)","Oran (%)"]

st.dataframe(urun_tablo, use_container_width=True)














##########################################################################v
# ----------------------------
# ÜRÜN DETAY ANALİZ
# ----------------------------
st.subheader("🏢 Ürün Grubu Ürün Detay")

secili_urun = st.selectbox(
    "Ürün Grubu Seç",
    sorted(df_filtre["urn_snf1"].dropna().unique()),
    key="urun1"
)

urun_detay_df = (
    df_filtre[df_filtre["urn_snf1"] == secili_urun]
    .groupby("sip_urnadisinif")
    .agg(
        Toplam_Tutar=("sip_tutar_indirimli", "sum"),
        Urun_Sayisi=("sip_adet", "sum")
    )
    .reset_index()
)

toplam = urun_detay_df["Toplam_Tutar"].sum()

urun_detay_df["Oran (%)"] = (
    urun_detay_df["Toplam_Tutar"] / toplam * 100
).round(1)

urun_detay_df = urun_detay_df.sort_values(
    "Toplam_Tutar",
    ascending=False
)

urun_detay_df["Tutar (€)"] = urun_detay_df["Toplam_Tutar"].map(
    lambda x: f"{x:,.0f}"
)

st.dataframe(
    urun_detay_df[
        ["sip_urnadisinif", "Urun_Sayisi", "Tutar (€)", "Oran (%)"]
    ].rename(columns={
        "sip_urnadisinif": "Ürün",
        "Urun_Sayisi": "Ürün Sayısı"
    }),
    use_container_width=True
)


#################################################################################


st.subheader("🏢 Ürün Grubu  - Müşteri ")

secili_urun = st.selectbox(
    "Ürün Grubu Seç",
    sorted(df_filtre["sip_urnadisinif"].dropna().unique()),
    key="urun3"
)

urun_detay_df = (
    df_filtre[df_filtre["sip_urnadisinif"] == secili_urun]
    .groupby("sip_frmunvan")
    .agg(
        Toplam_Tutar=("sip_tutar_indirimli", "sum"),
        Urun_Sayisi=("sip_adet", "sum")
    )
    .reset_index()
)

toplam = urun_detay_df["Toplam_Tutar"].sum()

urun_detay_df["Oran (%)"] = (
    urun_detay_df["Toplam_Tutar"] / toplam * 100
).round(1)

urun_detay_df = urun_detay_df.sort_values(
    "Toplam_Tutar",
    ascending=False
)

urun_detay_df["Tutar (€)"] = urun_detay_df["Toplam_Tutar"].map(
    lambda x: f"{x:,.0f}"
)

st.dataframe(
    urun_detay_df[
        ["sip_frmunvan", "Urun_Sayisi", "Tutar (€)", "Oran (%)"]
    ].rename(columns={
        "sip_frmunvan": "Firma Ünvanı",
        "Urun_Sayisi": "Ürün Sayısı"
    }),
    use_container_width=True
)

#####################################################################################



st.subheader("🏢 Ürün Grubu Ürün Detay ")

# Ürün grubu seçimi
secili_urun4 = st.selectbox(
    "Ürün Grubu Seç",
    ["Dalgıç Atıksu Pompası", "İzleme&Kontrol", "Kolon Pompası"],
    key="urun5"
)

# seçilen ürün grubuna göre alt sınıfları getir
alt_siniflar = (
    df_filtre[df_filtre["urn_snf1"] == secili_urun4]["sip_urnadisinif"]
    .dropna()
    .unique()
)

# ürün alt sınıfı seçimi
secili_alt_sinif = st.selectbox(
    "Ürün Alt Sınıfı Seç",
    sorted(alt_siniflar),
    key="urun5_alt"
)

# filtreleme
urun_detay_df = (
    df_filtre[
        (df_filtre["urn_snf1"] == secili_urun4) &
        (df_filtre["sip_urnadisinif"] == secili_alt_sinif)
    ]
    .groupby("sip_urnadi")
    .agg(
        Toplam_Tutar=("sip_tutar_indirimli", "sum"),
        Urun_Sayisi=("sip_adet", "sum")
    )
    .reset_index()
)

toplam = urun_detay_df["Toplam_Tutar"].sum()

urun_detay_df["Oran (%)"] = (
    urun_detay_df["Toplam_Tutar"] / toplam * 100
).round(1)

urun_detay_df = urun_detay_df.sort_values(
    "Toplam_Tutar",
    ascending=False
)

urun_detay_df["Tutar (€)"] = urun_detay_df["Toplam_Tutar"].map(
    lambda x: f"{x:,.0f}"
)

st.dataframe(
    urun_detay_df[
        ["sip_urnadi", "Urun_Sayisi", "Tutar (€)", "Oran (%)"]
    ].rename(columns={
        "sip_urnadi": "Ürün Adı",
        "Urun_Sayisi": "Ürün Sayısı"
    }),
    use_container_width=True
)





















# ----------------------------
# ÜRÜN SINIF ANALİZ
# ----------------------------
st.subheader("🏢 Ürün Grubu Alt Sınıf ")
secili_urun2 = st.selectbox(
    "Ürün Grubu Seç",
    ["Dalgıç Atıksu Pompası", "İzleme&Kontrol", "Kolon Pompası"],
    key="urun2"
)

urun_sinif_df = (
    df_filtre[df_filtre["urn_snf1"] == secili_urun2]
    .groupby("sip_urnsinifm")
    .agg(
        Toplam_Tutar=("sip_tutar_indirimli", "sum"),
        Urun_Sayisi=("sip_adet", "sum")
    )
    .reset_index()
)

toplam2 = urun_sinif_df["Toplam_Tutar"].sum()

urun_sinif_df["Oran (%)"] = (
    urun_sinif_df["Toplam_Tutar"] / toplam2 * 100
).round(1)

urun_sinif_df = urun_sinif_df.sort_values(
    "Toplam_Tutar",
    ascending=False
)

urun_sinif_df["Tutar (€)"] = urun_sinif_df["Toplam_Tutar"].map(
    lambda x: f"{x:,.0f}"
)

st.dataframe(
    urun_sinif_df[
        ["sip_urnsinifm", "Urun_Sayisi", "Tutar (€)", "Oran (%)"]
    ].rename(columns={
        "sip_urnsinifm": "Ürün",
        "Urun_Sayisi": "Ürün Sayısı"
    }),
    use_container_width=True
)




# ----------------------------
# MÜŞTERİ BAZLI LİSTE
# ----------------------------
st.subheader("🏢 Sipariş Tutar - Müşteri Bazlı")

musteri_df = (
    df_filtre.groupby("sip_frmunvan")["sip_tutar_indirimli"]
    .sum()
    .reset_index()
    .sort_values(by="sip_tutar_indirimli", ascending=False)
)

st.dataframe(musteri_df, use_container_width=True)
