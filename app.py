import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Comercial",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Comercial Online")

st.sidebar.title("Upload de Dados")

arquivo = st.sidebar.file_uploader(
    "Selecione a planilha Excel",
    type=["xlsx", "xls"]
)

if arquivo:

    try:
        df = pd.read_excel(
            arquivo,
            engine="openpyxl"
        )

    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    colunas_necessarias = [
        "Ano",
        "Vendedor",
        "Equipe",
        "Cidade",
        "Valor Venda",
        "Quantidade",
        "Cliente",
        "Fabricante",
        "Produto"
    ]

    colunas_faltando = [
        col for col in colunas_necessarias
        if col not in df.columns
    ]

    if colunas_faltando:
        st.error(
            f"As seguintes colunas estão faltando na planilha: {colunas_faltando}"
        )
        st.stop()

    st.sidebar.header("Filtros")

    anos = sorted(df["Ano"].dropna().unique())
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

    faturamento = df["Valor Venda"].sum()
    quantidade = df["Quantidade"].sum()
    clientes = df["Cliente"].nunique()

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
    c2.metric("📦 Produtos Vendidos", f"{quantidade:,.0f}")
    c3.metric("🛒 Clientes Positivados", clientes)

    st.divider()

    st.subheader("🏆 Ranking de Vendedores")

    vendedor_df = (
        df.groupby("Vendedor")["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(by="Valor Venda", ascending=False)
    )

    fig_vendedor = px.bar(
        vendedor_df,
        x="Vendedor",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(fig_vendedor, use_container_width=True)

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

    st.plotly_chart(fig_equipe, use_container_width=True)

    st.subheader("🏙️ Desempenho por Cidade")

    cidade_df = (
        df.groupby("Cidade")["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(by="Valor Venda", ascending=False)
    )

    fig_cidade = px.bar(
        cidade_df,
        x="Cidade",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(fig_cidade, use_container_width=True)

    st.subheader("📌 Batalha Naval de Positivação")

    batalha = pd.crosstab(
        df["Cliente"],
        df["Fabricante"]
    )

    batalha = batalha.map(
        lambda x: "✅" if x > 0 else "❌"
    )

    st.dataframe(
        batalha,
        use_container_width=True
    )

    st.subheader("📋 Detalhamento Completo")

    detalhamento = (
        df.groupby(
            ["Vendedor", "Cliente", "Fabricante", "Produto"]
        )["Valor Venda"]
        .sum()
        .reset_index()
    )

    st.dataframe(
        detalhamento,
        use_container_width=True
    )

else:
    st.info(
        "Faça upload da planilha Excel para visualizar o dashboard."
    )
