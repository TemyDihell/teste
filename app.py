# =========================================================
# DASHBOARD COMERCIAL BI - VERSÃO FINAL ESTÁVEL
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
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


def moeda_br(valor):

    return (

        f"R$ {valor:,.2f}"

        .replace(",", "X")

        .replace(".", ",")

        .replace("X", ".")

    )


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

            response = requests.get(
                download_url,
                timeout=30
            )

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
    # LIMPAR E PADRONIZAR COLUNAS
    # =====================================================

    def padronizar_colunas(df):

        df.columns = (

            df.columns

            .str.strip()

            .str.upper()

        )

        return df

    df_meta = padronizar_colunas(df_meta)
    df_historico = padronizar_colunas(df_historico)
    df_mes = padronizar_colunas(df_mes)

    # =====================================================
    # RENOMEAR COLUNAS
    # =====================================================

    mapa_colunas = {

        "VENDA R$": "VALOR VENDA",
        "VENDA": "VALOR VENDA",
        "VALOR": "VALOR VENDA",
        "QTDE": "QUANTIDADE",
        "QTD": "QUANTIDADE"

    }

    df_historico = df_historico.rename(
        columns=mapa_colunas
    )

    df_mes = df_mes.rename(
        columns=mapa_colunas
    )

    # =====================================================
    # CONCATENAR
    # =====================================================

    df_vendas = pd.concat(
        [df_historico, df_mes],
        ignore_index=True
    )

    # =====================================================
    # VALIDAR COLUNAS
    # =====================================================

    colunas_vendas = [
        "ANO",
        "MES",
        "VENDEDOR",
        "EQUIPE",
        "CIDADE",
        "FABRICANTE",
        "PRODUTO",
        "CLIENTE",
        "VALOR VENDA",
        "QUANTIDADE"
    ]

    colunas_meta = [
        "ANO",
        "MES",
        "VENDEDOR",
        "META"
    ]

    faltando_vendas = [

        coluna

        for coluna in colunas_vendas

        if coluna not in df_vendas.columns

    ]

    faltando_meta = [

        coluna

        for coluna in colunas_meta

        if coluna not in df_meta.columns

    ]

    if faltando_vendas:

        st.error(
            f"""
            Colunas ausentes em vendas:

            {faltando_vendas}
            """
        )

        st.stop()

    if faltando_meta:

        st.error(
            f"""
            Colunas ausentes em metas:

            {faltando_meta}
            """
        )

        st.stop()

    # =====================================================
    # PADRONIZAR TEXTO
    # =====================================================

    colunas_texto = [
        "VENDEDOR",
        "EQUIPE",
        "CIDADE",
        "FABRICANTE",
        "PRODUTO",
        "CLIENTE"
    ]

    for coluna in colunas_texto:

        df_vendas[coluna] = (

            df_vendas[coluna]

            .astype(str)

            .str.upper()

            .str.strip()

        )

    df_meta["VENDEDOR"] = (

        df_meta["VENDEDOR"]

        .astype(str)

        .str.upper()

        .str.strip()

    )

    # =====================================================
    # CONVERSÕES
    # =====================================================

    df_vendas["ANO"] = pd.to_numeric(
        df_vendas["ANO"],
        errors="coerce"
    )

    df_vendas["MES"] = pd.to_numeric(
        df_vendas["MES"],
        errors="coerce"
    )

    df_vendas["VALOR VENDA"] = (
        converter_brasil_numero(
            df_vendas["VALOR VENDA"]
        )
    )

    df_vendas["QUANTIDADE"] = (
        converter_brasil_numero(
            df_vendas["QUANTIDADE"]
        )
    )

    df_meta["META"] = (
        converter_brasil_numero(
            df_meta["META"]
        )
    )

    # =====================================================
    # REMOVER INVÁLIDOS
    # =====================================================

    df_vendas = df_vendas.dropna(
        subset=["ANO", "MES"]
    )

    df_vendas["ANO"] = (
        df_vendas["ANO"]
        .astype(int)
    )

    df_vendas["MES"] = (
        df_vendas["MES"]
        .astype(int)
    )

    # =====================================================
    # MÊS NOME
    # =====================================================

    meses_br = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez"
    }

    df_vendas["NOME MES"] = (
        df_vendas["MES"]
        .map(meses_br)
    )

    # =====================================================
    # DATA ATUAL
    # =====================================================

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    # =====================================================
    # FILTROS
    # =====================================================

    st.sidebar.header("🎯 Filtros")

    vendedores = sorted(
        df_vendas["VENDEDOR"]
        .dropna()
        .unique()
    )

    equipes = sorted(
        df_vendas["EQUIPE"]
        .dropna()
        .unique()
    )

    cidades = sorted(
        df_vendas["CIDADE"]
        .dropna()
        .unique()
    )

    fabricantes = sorted(
        df_vendas["FABRICANTE"]
        .dropna()
        .unique()
    )

    produtos = sorted(
        df_vendas["PRODUTO"]
        .dropna()
        .unique()
    )

    clientes_lista = sorted(
        df_vendas["CLIENTE"]
        .dropna()
        .unique()
    )

    meses = sorted(
        df_vendas["MES"]
        .dropna()
        .unique()
    )

    # =====================================================
    # SIDEBAR
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
        default=[mes_atual]
    )

    # =====================================================
    # FILTRO PRINCIPAL
    # =====================================================

    filtro_df = (

        df_vendas["VENDEDOR"].isin(
            filtro_vendedor
        )

        &

        df_vendas["EQUIPE"].isin(
            filtro_equipe
        )

        &

        df_vendas["CIDADE"].isin(
            filtro_cidade
        )

        &

        df_vendas["FABRICANTE"].isin(
            filtro_fabricante
        )

        &

        df_vendas["PRODUTO"].isin(
            filtro_produto
        )

        &

        df_vendas["CLIENTE"].isin(
            filtro_cliente
        )

        &

        df_vendas["MES"].isin(
            filtro_mes
        )

    )

    df_filtrado = df_vendas[
        filtro_df
    ]

    # =====================================================
    # KPI SOMENTE MÊS ATUAL
    # =====================================================

    df_kpi = df_filtrado[

        (df_filtrado["ANO"] == ano_atual)

        &

        (df_filtrado["MES"] == mes_atual)

    ]

    # =====================================================
    # META
    # =====================================================

    vendedores_meta = (
        df_filtrado["VENDEDOR"]
        .dropna()
        .unique()
    )

    meta_mes_atual = df_meta[

        (df_meta["ANO"] == ano_atual)

        &

        (df_meta["MES"] == mes_atual)

        &

        (df_meta["VENDEDOR"]
         .isin(vendedores_meta))

    ]

    # =====================================================
    # KPIs
    # =====================================================

    faturamento = float(
        df_kpi["VALOR VENDA"]
        .sum()
    )

    quantidade = float(
        df_kpi["QUANTIDADE"]
        .sum()
    )

    clientes = int(
        df_kpi["CLIENTE"]
        .nunique()
    )

    mix_produtos = int(
        df_kpi["PRODUTO"]
        .nunique()
    )

    meta_total = float(

        meta_mes_atual

        .groupby("VENDEDOR")["META"]

        .max()

        .sum()

    )

    atingimento = (

        (faturamento / meta_total) * 100

        if meta_total > 0

        else 0

    )

    # =====================================================
    # DIAS ÚTEIS
    # =====================================================

    hoje = datetime.now()

    primeiro_dia_mes = datetime(
        ano_atual,
        mes_atual,
        1
    )

    if mes_atual == 12:

        ultimo_dia_mes = datetime(
            ano_atual + 1,
            1,
            1
        ) - pd.Timedelta(days=1)

    else:

        ultimo_dia_mes = datetime(
            ano_atual,
            mes_atual + 1,
            1
        ) - pd.Timedelta(days=1)

    dias_uteis_mes = pd.bdate_range(
        start=primeiro_dia_mes,
        end=ultimo_dia_mes
    )

    total_dias_uteis = len(
        dias_uteis_mes
    )

    dias_uteis_decorridos = pd.bdate_range(
        start=primeiro_dia_mes,
        end=hoje
    )

    dias_decorridos = len(
        dias_uteis_decorridos
    )

    dias_restantes = (
        total_dias_uteis
        - dias_decorridos
    )

    media_diaria = (

        faturamento / dias_decorridos

        if dias_decorridos > 0

        else 0

    )

    tendencia_final = (
        media_diaria
        * total_dias_uteis
    )

    falta_meta = (
        meta_total
        - faturamento
    )

    objetivo_dia = (

        falta_meta / dias_restantes

        if dias_restantes > 0

        else 0

    )

    # =====================================================
    # KPIs VISUAIS
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "💰 Faturamento",
        moeda_br(faturamento)
    )

    c2.metric(
        "🎯 Meta",
        moeda_br(meta_total)
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

    # =====================================================
    # KPIs AVANÇADOS
    # =====================================================

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        "📅 Dias Úteis",
        total_dias_uteis
    )

    k2.metric(
        "⏳ Dias Decorridos",
        dias_decorridos
    )

    k3.metric(
        "📌 Dias Restantes",
        dias_restantes
    )

    k4.metric(
        "📈 Tendência",
        moeda_br(tendencia_final)
    )

    k5.metric(
        "🎯 Objetivo Dia",
        moeda_br(objetivo_dia)
    )

    st.divider()

    # =====================================================
    # META X REALIZADO
    # =====================================================

    st.subheader(
        "🎯 Meta x Realizado"
    )

    vendas_mes = (
        df_filtrado
        .groupby("VENDEDOR")
        ["VALOR VENDA"]
        .sum()
        .reset_index()
    )

    meta_mes = (
        meta_mes_atual
        .groupby("VENDEDOR")
        ["META"]
        .max()
        .reset_index()
    )

    meta_realizado = pd.merge(
        vendas_mes,
        meta_mes,
        how="outer",
        on="VENDEDOR"
    ).fillna(0)

    fig_meta = px.bar(
        meta_realizado,
        x="VENDEDOR",
        y=["VALOR VENDA", "META"],
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
        df_filtrado
        .groupby("VENDEDOR")
        ["VALOR VENDA"]
        .sum()
        .reset_index()
        .sort_values(
            by="VALOR VENDA",
            ascending=False
        )
    )

    fig_rank = px.bar(
        ranking,
        x="VENDEDOR",
        y="VALOR VENDA",
        text_auto=True
    )

    st.plotly_chart(
        fig_rank,
        use_container_width=True
    )

    # =====================================================
    # DETALHAMENTO
    # =====================================================

    st.subheader(
        "📋 Detalhamento"
    )

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        height=600
    )

else:

    st.info(
        "Informe os links das planilhas."
    )
