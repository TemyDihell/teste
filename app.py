# =========================================================
# DASHBOARD COMERCIAL BI - VERSÃO FINAL ESTÁVEL
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar
import requests
from io import BytesIO

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Dashboard Comercial BI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Comercial BI")

# =========================================================
# FUNÇÕES
# =========================================================

def converter_brasil_numero(serie):

    return pd.to_numeric(

        serie.astype(str)

        .str.replace("R$", "", regex=False)

        .str.replace(".", "", regex=False)

        .str.replace(",", ".", regex=False)

        .str.strip(),

        errors="coerce"

    ).fillna(0)


def extrair_file_id(link):

    try:

        if "/spreadsheets/d/" in link:

            return (
                link
                .split("/spreadsheets/d/")[1]
                .split("/")[0]
            )

        elif "/file/d/" in link:

            return (
                link
                .split("/file/d/")[1]
                .split("/")[0]
            )

        elif "id=" in link:

            return (
                link
                .split("id=")[1]
                .split("&")[0]
            )

        return None

    except:

        return None


@st.cache_data
def carregar_excel_google(link):

    file_id = extrair_file_id(link)

    if not file_id:

        raise Exception(
            "Não foi possível identificar o ID."
        )

    try:

        # =================================================
        # GOOGLE SHEETS
        # =================================================

        if "spreadsheets" in link:

            csv_url = (
                "https://docs.google.com/"
                f"spreadsheets/d/{file_id}/export"
                "?format=csv"
            )

            return pd.read_csv(csv_url)

        # =================================================
        # GOOGLE DRIVE XLSX
        # =================================================

        else:

            download_url = (
                "https://drive.google.com/"
                f"uc?export=download&id={file_id}"
            )

            response = requests.get(download_url)

            return pd.read_excel(
                BytesIO(response.content),
                engine="openpyxl"
            )

    except Exception as e:

        raise Exception(
            f"Erro ao carregar planilha: {e}"
        )

# =========================================================
# SIDEBAR LINKS
# =========================================================

st.sidebar.header("📂 Planilhas Google")

link_meta = st.sidebar.text_input(
    "🔹 Link Metas"
)

link_historico = st.sidebar.text_input(
    "🔹 Link Histórico"
)

link_mes = st.sidebar.text_input(
    "🔹 Link Mês Atual"
)

# =========================================================
# PROCESSAMENTO
# =========================================================

if link_meta and link_historico and link_mes:

    try:

        with st.spinner(
            "Carregando dados..."
        ):

            df_meta = carregar_excel_google(
                link_meta
            )

            df_historico = carregar_excel_google(
                link_historico
            )

            df_mes = carregar_excel_google(
                link_mes
            )

    except Exception as e:

        st.error(
            f"Erro ao carregar planilhas: {e}"
        )

        st.stop()

    # =====================================================
    # CONCATENAR VENDAS
    # =====================================================

    df_vendas = pd.concat(
        [df_historico, df_mes],
        ignore_index=True
    )

    # =====================================================
    # TRATAMENTO
    # =====================================================

    df_vendas["Data"] = pd.to_datetime(
        df_vendas["Data"],
        errors="coerce"
    )

    df_vendas = df_vendas.dropna(
        subset=["Data"]
    )

    df_vendas["Ano"] = (
        df_vendas["Data"].dt.year
    )

    df_vendas["Mes"] = (
        df_vendas["Data"].dt.month
    )

    df_vendas["Dia"] = (
        df_vendas["Data"].dt.day
    )

    df_vendas["Nome Mes"] = (
        df_vendas["Mes"]
        .apply(lambda x: calendar.month_abbr[x])
    )

    # =====================================================
    # CONVERSÕES
    # =====================================================

    df_vendas["Valor Venda"] = (
        converter_brasil_numero(
            df_vendas["Valor Venda"]
        )
    )

    df_vendas["Quantidade"] = (
        converter_brasil_numero(
            df_vendas["Quantidade"]
        )
    )

    df_meta["Meta"] = (
        converter_brasil_numero(
            df_meta["Meta"]
        )
    )

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    # =====================================================
    # MERGE
    # =====================================================

    df = pd.merge(
        df_vendas,
        df_meta,
        how="left",
        on=["Ano", "Mes", "Vendedor"]
    )

    df["Meta"] = (
        df["Meta"]
        .fillna(0)
    )

    # =====================================================
    # FILTROS
    # =====================================================

    st.sidebar.header("🎯 Filtros")

    vendedores = sorted(
        df["Vendedor"]
        .dropna()
        .astype(str)
        .unique()
    )

    equipes = sorted(
        df["Equipe"]
        .dropna()
        .astype(str)
        .unique()
    )

    cidades = sorted(
        df["Cidade"]
        .dropna()
        .astype(str)
        .unique()
    )

    fabricantes = sorted(
        df["Fabricante"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    clientes_lista = sorted(
        df["Cliente"]
        .dropna()
        .astype(str)
        .unique()
    )

    meses = sorted(
        df["Mes"]
        .dropna()
        .unique()
    )

    # =====================================================
    # SIDEBAR FILTROS
    # =====================================================

    filtro_vendedor = st.sidebar.multiselect(
        "👤 Vendedor",
        vendedores,
        default=vendedores
    )

    filtro_equipe = st.sidebar.multiselect(
        "👥 Equipe",
        equipes,
        default=equipes
    )

    filtro_cidade = st.sidebar.multiselect(
        "🏙️ Cidade",
        cidades,
        default=cidades
    )

    filtro_fabricante = st.sidebar.multiselect(
        "🏭 Fabricante",
        fabricantes,
        default=fabricantes
    )

    filtro_produto = st.sidebar.multiselect(
        "📦 Produto",
        produtos,
        default=produtos
    )

    filtro_cliente = st.sidebar.multiselect(
        "🛒 Cliente",
        clientes_lista,
        default=clientes_lista
    )

    filtro_mes = st.sidebar.multiselect(
        "📅 Mês",
        meses,
        default=meses
    )

    # =====================================================
    # FILTRO PRINCIPAL
    # =====================================================

    filtro_df = (

        df["Vendedor"].isin(
            filtro_vendedor
        )

        &

        df["Equipe"].isin(
            filtro_equipe
        )

        &

        df["Cidade"].isin(
            filtro_cidade
        )

        &

        df["Fabricante"].isin(
            filtro_fabricante
        )

        &

        df["Produto"].isin(
            filtro_produto
        )

        &

        df["Cliente"].isin(
            filtro_cliente
        )

        &

        df["Mes"].isin(
            filtro_mes
        )

    )

    df = df[filtro_df]

    # =====================================================
    # FILTRO META
    # =====================================================

    filtro_meta = (

        df_meta["Vendedor"]
        .astype(str)
        .isin(filtro_vendedor)

    )

    df_meta = df_meta[
        filtro_meta
    ]

    # =====================================================
    # MÊS ATUAL
    # =====================================================

    df_mes_atual = df[

        (df["Ano"] == ano_atual)

        &

        (df["Mes"] == mes_atual)

    ]

    # =====================================================
    # META MÊS ATUAL
    # =====================================================

    meta_mes_atual = df_meta[

        (df_meta["Ano"] == ano_atual)

        &

        (df_meta["Mes"] == mes_atual)

    ]

    # =====================================================
    # SINCRONIZAR META COM FILTROS
    # =====================================================

    vendedores_filtrados = (

        df_mes_atual["Vendedor"]

        .dropna()

        .astype(str)

        .unique()

    )

    meta_mes_atual = meta_mes_atual[

        meta_mes_atual["Vendedor"]

        .astype(str)

        .isin(vendedores_filtrados)

    ]

    # =====================================================
    # KPIs
    # =====================================================

    faturamento = float(
        df_mes_atual["Valor Venda"]
        .sum()
    )

    quantidade = float(
        df_mes_atual["Quantidade"]
        .sum()
    )

    clientes = int(
        df_mes_atual["Cliente"]
        .nunique()
    )

    meta_total = float(

        meta_mes_atual

        .drop_duplicates(
            subset=["Vendedor"]
        )["Meta"]

        .sum()

    )

    if meta_total > 0:

        atingimento = (
            faturamento / meta_total
        ) * 100

    else:

        atingimento = 0

    ticket_medio = (

        faturamento / clientes

        if clientes > 0

        else 0

    )

    mix_produtos = int(
        df_mes_atual["Produto"]
        .nunique()
    )

    # =====================================================
    # KPIs VISUAIS
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Faturamento",
        f"R$ {faturamento:,.2f}"
    )

    c2.metric(
        "🎯 Meta",
        f"R$ {meta_total:,.2f}"
    )

    c3.metric(
        "📈 Atingimento",
        f"{atingimento:.1f}%"
    )

    c4.metric(
        "🛒 Clientes",
        clientes
    )

    c5.metric(
        "📦 Mix Produtos",
        mix_produtos
    )

    st.divider()

    # =====================================================
    # META X REALIZADO
    # =====================================================

    st.subheader(
        "🎯 Meta x Realizado"
    )

    vendas_mes = (
        df_mes_atual
        .groupby("Vendedor")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    meta_mes = (
        meta_mes_atual
        .groupby("Vendedor")
        ["Meta"]
        .sum()
        .reset_index()
    )

    meta_realizado = pd.merge(
        vendas_mes,
        meta_mes,
        how="outer",
        on="Vendedor"
    ).fillna(0)

    fig_meta = px.bar(
        meta_realizado,
        x="Vendedor",
        y=["Valor Venda", "Meta"],
        barmode="group",
        text_auto=True
    )

    st.plotly_chart(
        fig_meta,
        use_container_width=True
    )

    # =====================================================
    # RANKING
    # =====================================================

    st.subheader(
        "🏆 Ranking Vendedores"
    )

    ranking = (
        df_mes_atual
        .groupby("Vendedor")
        ["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor Venda",
            ascending=False
        )
    )

    fig_rank = px.bar(
        ranking,
        x="Vendedor",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(
        fig_rank,
        use_container_width=True
    )

    # =====================================================
    # BATALHA NAVAL
    # =====================================================

    st.subheader(
        "📌 Batalha Naval"
    )

    fabricante = (
        df_mes_atual
        .groupby("Fabricante")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    top_fabricantes = (
        fabricante
        .sort_values(
            by="Valor Venda",
            ascending=False
        )
        .head(10)
        ["Fabricante"]
    )

    df_batalha = df_mes_atual[
        df_mes_atual["Fabricante"]
        .isin(top_fabricantes)
    ]

    batalha = pd.crosstab(
        df_batalha["Cliente"],
        df_batalha["Fabricante"]
    )

    batalha = batalha.map(
        lambda x:
        "✅" if x > 0 else ""
    )

    st.dataframe(
        batalha,
        use_container_width=True,
        height=500
    )

    # =====================================================
    # DETALHAMENTO
    # =====================================================

    st.subheader(
        "📋 Detalhamento"
    )

    detalhamento = (
        df_mes_atual
        .groupby([
            "Vendedor",
            "Cliente",
            "Fabricante",
            "Produto"
        ])
        .agg({
            "Quantidade": "sum",
            "Valor Venda": "sum"
        })
        .reset_index()
    )

    st.dataframe(
        detalhamento,
        use_container_width=True,
        height=600
    )

else:

    st.info(
        "Informe os links das planilhas."
    )
