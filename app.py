import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar

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
# GOOGLE DRIVE
# =========================================================

st.sidebar.header("📂 Google Drive")

link_drive = st.sidebar.text_input(
    "Cole o link da planilha"
)

def converter_link_drive(link):

    if "drive.google.com" not in link:
        return None

    try:
        file_id = link.split("/d/")[1].split("/")[0]

        return f"https://drive.google.com/uc?id={file_id}"

    except:
        return None


# =========================================================
# LEITURA DOS DADOS
# =========================================================

if link_drive:

    url_excel = converter_link_drive(link_drive)

    if not url_excel:
        st.error("Link inválido.")
        st.stop()

    try:

        df = pd.read_excel(
            url_excel,
            engine="openpyxl"
        )

    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        st.stop()

    # =====================================================
    # COLUNAS NECESSÁRIAS
    # =====================================================

    colunas_necessarias = [
        "Data",
        "Vendedor",
        "Equipe",
        "Cidade",
        "Valor Venda",
        "Quantidade",
        "Cliente",
        "Fabricante",
        "Produto",
        "Meta"
    ]

    faltando = [
        col for col in colunas_necessarias
        if col not in df.columns
    ]

    if faltando:
        st.error(f"Colunas faltando: {faltando}")
        st.stop()

    # =====================================================
    # TRATAMENTO
    # =====================================================

    df["Data"] = pd.to_datetime(df["Data"])

    df["Ano"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month
    df["Dia"] = df["Data"].dt.day

    df["Nome Mes"] = df["Mes"].apply(
        lambda x: calendar.month_abbr[x]
    )

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    # =====================================================
    # FILTROS
    # =====================================================

    st.sidebar.header("🎯 Filtros")

    anos = sorted(df["Ano"].unique())
    vendedores = sorted(df["Vendedor"].dropna().unique())
    equipes = sorted(df["Equipe"].dropna().unique())
    cidades = sorted(df["Cidade"].dropna().unique())

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
        df["Vendedor"].isin(filtro_vendedor) &
        df["Equipe"].isin(filtro_equipe) &
        df["Cidade"].isin(filtro_cidade)
    )

    df = df[filtro]

    # =====================================================
    # KPIs PRINCIPAIS
    # =====================================================

    faturamento = df["Valor Venda"].sum()

    quantidade = df["Quantidade"].sum()

    clientes = df["Cliente"].nunique()

    meta_total = df["Meta"].sum()

    atingimento = (
        (faturamento / meta_total) * 100
        if meta_total > 0 else 0
    )

    ticket_medio = (
        faturamento / clientes
        if clientes > 0 else 0
    )

    mix_produtos = df["Produto"].nunique()

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
    # FATURAMENTO MENSAL
    # =====================================================

    st.subheader("📈 Comparativo Ano Atual x Ano Anterior")

    comparativo = (
        df[df["Ano"].isin([ano_atual, ano_atual - 1])]
        .groupby(["Ano", "Mes"])["Valor Venda"]
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

    st.subheader("🎯 Meta x Realizado")

    meta_df = (
        df.groupby("Mes")
        .agg({
            "Valor Venda": "sum",
            "Meta": "sum"
        })
        .reset_index()
    )

    fig_meta = px.bar(
        meta_df,
        x="Mes",
        y=["Valor Venda", "Meta"],
        barmode="group"
    )

    st.plotly_chart(
        fig_meta,
        use_container_width=True
    )

    # =====================================================
    # GAUGE KPI
    # =====================================================

    st.subheader("🚦 Indicador de Meta")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=atingimento,
        title={"text": "Atingimento da Meta (%)"},
        gauge={
            "axis": {"range": [0, 150]},
            "bar": {"thickness": 0.3},
            "steps": [
                {"range": [0, 70], "color": "red"},
                {"range": [70, 100], "color": "yellow"},
                {"range": [100, 150], "color": "green"}
            ]
        }
    ))

    st.plotly_chart(
        fig_gauge,
        use_container_width=True
    )

    # =====================================================
    # RANKING VENDEDORES
    # =====================================================

    st.subheader("🏆 Ranking Vendedores")

    vendedor_df = (
        df.groupby("Vendedor")["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor Venda",
            ascending=False
        )
    )

    fig_vendedor = px.bar(
        vendedor_df,
        x="Vendedor",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(
        fig_vendedor,
        use_container_width=True
    )

    # =====================================================
    # TOP E FLOP
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🔥 TOP 10 Clientes")

        top_clientes = (
            df.groupby("Cliente")["Valor Venda"]
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

        st.subheader("❄️ FLOP 10 Clientes")

        flop_clientes = (
            df.groupby("Cliente")["Valor Venda"]
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

    st.subheader("👥 Desempenho por Equipe")

    equipe_df = (
        df.groupby("Equipe")["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_equipe = px.pie(
        equipe_df,
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

    st.subheader("🏙️ Desempenho por Cidade")

    cidade_df = (
        df.groupby("Cidade")["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_cidade = px.bar(
        cidade_df,
        x="Cidade",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(
        fig_cidade,
        use_container_width=True
    )

    # =====================================================
    # MIX POR CLIENTE
    # =====================================================

    st.subheader("📦 Mix de Produtos por Cliente")

    mix_df = (
        df.groupby("Cliente")["Produto"]
        .nunique()
        .reset_index()
        .sort_values(
            by="Produto",
            ascending=False
        )
        .head(15)
    )

    fig_mix = px.bar(
        mix_df,
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

    st.subheader("📌 Batalha Naval - Mês Atual")

    df_mes = df[
        (df["Ano"] == ano_atual) &
        (df["Mes"] == mes_atual)
    ]

    top_fabricantes = (
        df_mes.groupby("Fabricante")["Valor Venda"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
        .index
    )

    df_mes = df_mes[
        df_mes["Fabricante"].isin(top_fabricantes)
    ]

    batalha = pd.crosstab(
        df_mes["Cliente"],
        df_mes["Fabricante"]
    )

    batalha = batalha.map(
        lambda x: "✅" if x > 0 else ""
    )

    st.dataframe(
        batalha,
        use_container_width=True,
        height=500
    )

    # =====================================================
    # DETALHAMENTO
    # =====================================================

    st.subheader("📋 Detalhamento Completo")

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
            "Valor Venda": "sum",
            "Quantidade": "sum"
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
        "Cole o link compartilhado do Google Drive."
    )