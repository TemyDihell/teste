# =========================================================
# DASHBOARD COMERCIAL BI - VERSÃO ESTÁVEL
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
# SIDEBAR
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
    # CONCATENAR
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
    # CONVERSÃO NUMÉRICA
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
        .unique()
    )

    equipes = sorted(
        df["Equipe"]
        .dropna()
        .unique()
    )

    cidades = sorted(
        df["Cidade"]
        .dropna()
        .unique()
    )

    filtro_vendedor = st.sidebar.multiselect(
        "Vendedor",
        vendedores,
        default=vendedores
    )

    filtro_equipe = st.sidebar.multiselect(
        "Equipe",
        equipes,
        default=equipes
    )

    filtro_cidade = st.sidebar.multiselect(
        "Cidade",
        cidades,
        default=cidades
    )

    filtro = (
        df["Vendedor"].isin(
            filtro_vendedor
        ) &
        df["Equipe"].isin(
            filtro_equipe
        ) &
        df["Cidade"].isin(
            filtro_cidade
        )
    )

    df = df[filtro]

    # =====================================================
    # MÊS ATUAL
    # =====================================================

    df_mes_atual = df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
    ]

    meta_mes_atual = df_meta[
        (df_meta["Ano"] == ano_atual) &
        (df_meta["Mes"] == mes_atual)
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
        if clientes > 0 else 0
    )

    mix_produtos = int(
        df_mes_atual["Produto"]
        .nunique()
    )

    clientes_total = int(
        df["Cliente"].nunique()
    )

    positivacao = (
        (clientes / clientes_total) * 100
        if clientes_total > 0 else 0
    )

    faturamento_ano_passado = float(

        df[
            (df["Ano"] == ano_atual - 1) &
            (df["Mes"] == mes_atual)
        ]["Valor Venda"].sum()

    )

    crescimento = (
        (
            (
                faturamento -
                faturamento_ano_passado
            )
            /
            faturamento_ano_passado
        ) * 100
        if faturamento_ano_passado > 0
        else 0
    )

    # =====================================================
    # KPIs
    # =====================================================

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

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
        "💳 Ticket Médio",
        f"R$ {ticket_medio:,.2f}"
    )

    c6.metric(
        "📦 Mix Produtos",
        mix_produtos
    )

    c7.metric(
        "📊 Crescimento",
        f"{crescimento:.1f}%"
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

    meta_realizado["%"] = (
        meta_realizado["Valor Venda"]
        /
        meta_realizado["Meta"]
        * 100
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
    # % ATINGIMENTO
    # =====================================================

    st.subheader(
        "📈 % Atingimento por Vendedor"
    )

    fig_pct = px.bar(
        meta_realizado,
        x="Vendedor",
        y="%",
        text_auto=".1f"
    )

    st.plotly_chart(
        fig_pct,
        use_container_width=True
    )

    # =====================================================
    # EVOLUÇÃO DIÁRIA
    # =====================================================

    st.subheader(
        "📅 Evolução Diária"
    )

    diario = (
        df_mes_atual
        .groupby("Dia")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_diario = px.line(
        diario,
        x="Dia",
        y="Valor Venda",
        markers=True
    )

    st.plotly_chart(
        fig_diario,
        use_container_width=True
    )

    # =====================================================
    # COMPARATIVO ANUAL
    # =====================================================

    st.subheader(
        "📊 Comparativo Anual"
    )

    comparativo = (
        df.groupby(
            ["Ano", "Mes"]
        )["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_comp = px.line(
        comparativo,
        x="Mes",
        y="Valor Venda",
        color="Ano",
        markers=True
    )

    st.plotly_chart(
        fig_comp,
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
    # CURVA ABC
    # =====================================================

    st.subheader(
        "📦 Curva ABC Clientes"
    )

    abc = (
        df_mes_atual
        .groupby("Cliente")
        ["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor Venda",
            ascending=False
        )
    )

    abc["Acumulado"] = (
        abc["Valor Venda"]
        .cumsum()
        /
        abc["Valor Venda"].sum()
        * 100
    )

    fig_abc = px.line(
        abc,
        x="Cliente",
        y="Acumulado",
        markers=True
    )

    st.plotly_chart(
        fig_abc,
        use_container_width=True
    )

    # =====================================================
    # FABRICANTES
    # =====================================================

    st.subheader(
        "🏭 Mix Fabricantes"
    )

    fabricante = (
        df_mes_atual
        .groupby("Fabricante")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_fab = px.pie(
        fabricante,
        names="Fabricante",
        values="Valor Venda"
    )

    st.plotly_chart(
        fig_fab,
        use_container_width=True
    )

    # =====================================================
    # BATALHA NAVAL
    # =====================================================

    st.subheader(
        "📌 Batalha Naval"
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
