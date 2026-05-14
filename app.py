import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar
import requests
from io import BytesIO

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================

st.set_page_config(
    page_title="Dashboard Comercial BI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Comercial BI")

# =========================================================
# GOOGLE DRIVE / GOOGLE SHEETS
# =========================================================

def extrair_file_id(link):

    try:

        # GOOGLE SHEETS
        if "/spreadsheets/d/" in link:

            return (
                link
                .split("/spreadsheets/d/")[1]
                .split("/")[0]
            )

        # GOOGLE DRIVE
        elif "/file/d/" in link:

            return (
                link
                .split("/file/d/")[1]
                .split("/")[0]
            )

        # FORMATO COM ID=
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
            "Não foi possível identificar o ID da planilha."
        )

    # =====================================================
    # GOOGLE SHEETS EXPORT XLSX
    # =====================================================

    if "spreadsheets" in link:

        export_url = (
            "https://docs.google.com/"
            f"spreadsheets/d/{file_id}/export"
            "?format=xlsx"
        )

    # =====================================================
    # GOOGLE DRIVE DOWNLOAD
    # =====================================================

    else:

        export_url = (
            "https://drive.google.com/"
            f"uc?export=download&id={file_id}"
        )

    response = requests.get(export_url)

    if response.status_code != 200:

        raise Exception(
            f"Erro ao baixar arquivo "
            f"(Status {response.status_code})"
        )

    try:

        return pd.read_excel(
            BytesIO(response.content),
            engine="openpyxl"
        )

    except Exception as e:

        raise Exception(
            f"Erro ao ler Excel: {e}"
        )

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📂 Planilhas Google")

link_meta = st.sidebar.text_input(
    "🔹 Link Planilha Metas"
)

link_historico = st.sidebar.text_input(
    "🔹 Link Histórico Ano"
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
            "Carregando planilhas..."
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
    # VALIDAÇÃO DE COLUNAS
    # =====================================================

    colunas_vendas = [
        "Data",
        "Vendedor",
        "Equipe",
        "Cidade",
        "Cliente",
        "Fabricante",
        "Produto",
        "Quantidade",
        "Valor Venda"
    ]

    colunas_meta = [
        "Ano",
        "Mes",
        "Vendedor",
        "Meta"
    ]

    faltando_vendas = [
        col for col in colunas_vendas
        if col not in df_vendas.columns
    ]

    faltando_meta = [
        col for col in colunas_meta
        if col not in df_meta.columns
    ]

    if faltando_vendas:

        st.error(
            f"Colunas faltando nas vendas: "
            f"{faltando_vendas}"
        )

        st.stop()

    if faltando_meta:

        st.error(
            f"Colunas faltando nas metas: "
            f"{faltando_meta}"
        )

        st.stop()

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

    df_vendas["Nome Mes"] = (
        df_vendas["Mes"]
        .apply(lambda x: calendar.month_abbr[x])
    )

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    # =====================================================
    # MERGE META + VENDAS
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

    anos = sorted(
        df["Ano"]
        .dropna()
        .unique()
    )

    filtro_ano = st.sidebar.multiselect(
        "Ano",
        anos,
        default=anos
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
        df["Ano"].isin(filtro_ano) &
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
    # KPIs
    # =====================================================

        
    faturamento = (
        df["Valor Venda"].sum()
    )
    
    quantidade = (
        df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
        ]["Quantidade"].sum()
    )

    clientes = (
        df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
        ]["Cliente"].nunique()
    )

    meta_total = (
        df["Vendedor"].unique()
        ["Meta").Sum()
    )

    atingimento = (
        (faturamento / meta_total) * 100
        if meta_total > 0 else 0
    )

    ticket_medio = (
        faturamento / clientes
        if clientes > 0 else 0
    )

    mix_produtos = (
        df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
        ]["Produto"].nunique()
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

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

    st.divider()

    # =====================================================
    # COMPARATIVO MENSAL
    # =====================================================

    st.subheader(
        "📈 Comparativo Ano Atual x Ano Anterior"
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
    # META X REALIZADO
    # =====================================================

    st.subheader(
        "🎯 Meta x Realizado"
    )

    meta_realizado = (
        df.groupby("Mes")
        .agg({
            "Valor Venda": "sum",
            "Meta": "sum"
        })
        .reset_index()
    )

    fig_meta = px.bar(
        meta_realizado,
        x="Mes",
        y=["Valor Venda", "Meta"],
        barmode="group"
    )

    st.plotly_chart(
        fig_meta,
        use_container_width=True
    )

    # =====================================================
    # GAUGE META
    # =====================================================

    st.subheader(
        "🚦 Indicador de Meta"
    )

    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=atingimento,
            title={
                "text": "Atingimento (%)"
            },
            gauge={
                "axis": {
                    "range": [0, 150]
                },
                "steps": [
                    {
                        "range": [0, 70],
                        "color": "red"
                    },
                    {
                        "range": [70, 100],
                        "color": "yellow"
                    },
                    {
                        "range": [100, 150],
                        "color": "green"
                    }
                ]
            }
        )
    )

    st.plotly_chart(
        fig_gauge,
        use_container_width=True
    )

    # =====================================================
    # RANKING VENDEDORES
    # =====================================================

    st.subheader(
        "🏆 Ranking de Vendedores"
    )

    ranking = (
        df.groupby("Vendedor")
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
    # TOP/FLOP CLIENTES
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "🔥 TOP 10 Clientes"
        )

        top_clientes = (
            df.groupby("Cliente")
            ["Valor Venda"]
            .sum()
            .reset_index()
            .sort_values(
                by="Valor Venda",
                ascending=False
            )
            .head(10)
        )

        fig_top = px.bar(
            top_clientes,
            x="Cliente",
            y="Valor Venda",
            text_auto=True
        )

        st.plotly_chart(
            fig_top,
            use_container_width=True
        )

    with col2:

        st.subheader(
            "❄️ FLOP 10 Clientes"
        )

        flop_clientes = (
            df.groupby("Cliente")
            ["Valor Venda"]
            .sum()
            .reset_index()
            .sort_values(
                by="Valor Venda",
                ascending=True
            )
            .head(10)
        )

        fig_flop = px.bar(
            flop_clientes,
            x="Cliente",
            y="Valor Venda",
            text_auto=True
        )

        st.plotly_chart(
            fig_flop,
            use_container_width=True
        )

    # =====================================================
    # EQUIPE
    # =====================================================

    st.subheader(
        "👥 Desempenho por Equipe"
    )

    equipe = (
        df.groupby("Equipe")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_equipe = px.pie(
        equipe,
        names="Equipe",
        values="Valor Venda"
    )

    st.plotly_chart(
        fig_equipe,
        use_container_width=True
    )

    # =====================================================
    # CIDADE
    # =====================================================

    st.subheader(
        "🏙️ Desempenho por Cidade"
    )

    cidade = (
        df.groupby("Cidade")
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_cidade = px.bar(
        cidade,
        x="Cidade",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(
        fig_cidade,
        use_container_width=True
    )

    # =====================================================
    # MIX PRODUTOS
    # =====================================================

    st.subheader(
        "📦 Mix Produtos por Cliente"
    )

    mix = (
        df.groupby("Cliente")
        ["Produto"]
        .nunique()
        .reset_index()
        .sort_values(
            by="Produto",
            ascending=False
        )
        .head(15)
    )

    fig_mix = px.bar(
        mix,
        x="Cliente",
        y="Produto",
        text_auto=True
    )

    st.plotly_chart(
        fig_mix,
        use_container_width=True
    )

    # =====================================================
    # BATALHA NAVAL
    # =====================================================

    st.subheader(
        "📌 Batalha Naval - Mês Atual"
    )

    df_batalha = df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
    ]

    top_fabricantes = (
        df_batalha.groupby(
            "Fabricante"
        )["Valor Venda"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
        .index
    )

    df_batalha = df_batalha[
        df_batalha["Fabricante"]
        .isin(top_fabricantes)
    ]

    batalha = pd.crosstab(
        df_batalha["Cliente"],
        df_batalha["Fabricante"]
    )

    batalha = batalha.map(
        lambda x:
        "✅" if x > 0 else "❌"
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
        "📋 Detalhamento Completo"
    )

    detalhamento = (
        df.groupby([
            "Ano",
            "Nome Mes",
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
        "Informe os 3 links das planilhas Google."
    )
