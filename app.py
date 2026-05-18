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
    # LIMPAR COLUNAS
    # =====================================================

    df_meta.columns = (
        df_meta.columns
        .str.strip()
    )

    df_historico.columns = (
        df_historico.columns
        .str.strip()
    )

    df_mes.columns = (
        df_mes.columns
        .str.strip()
    )

    # =====================================================
    # CONCATENAR VENDAS
    # =====================================================

    df_vendas = pd.concat(
        [df_historico, df_mes],
        ignore_index=True
    ).drop_duplicates()

    # =====================================================
    # NORMALIZAR TEXTO
    # =====================================================

    colunas_texto = [
        "Vendedor",
        "Equipe",
        "Cidade",
        "Fabricante",
        "Produto",
        "Cliente"
    ]

    for coluna in colunas_texto:

        if coluna in df_vendas.columns:

            df_vendas[coluna] = (
                df_vendas[coluna]
                .astype(str)
                .str.upper()
                .str.strip()
            )

    if "Vendedor" in df_meta.columns:

        df_meta["Vendedor"] = (
            df_meta["Vendedor"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

    # =====================================================
    # TRATAMENTO DATA (NOVO MODELO SEM CAMPO DATA)
    # =====================================================

    # AGORA O SISTEMA UTILIZA DIRETAMENTE:
    # ✅ Ano
    # ✅ Mes
    #
    # NÃO PRECISA MAIS DA COLUNA "Data"

    # =====================================================
    # GARANTIR NUMÉRICOS
    # =====================================================

    df_vendas["Ano"] = pd.to_numeric(
        df_vendas["Ano"],
        errors="coerce"
    )

    df_vendas["Mes"] = pd.to_numeric(
        df_vendas["Mes"],
        errors="coerce"
    )

    # =====================================================
    # REMOVER LINHAS INVÁLIDAS
    # =====================================================

    df_vendas = df_vendas.dropna(
        subset=["Ano", "Mes"]
    )

    # =====================================================
    # CONVERTER PARA INT
    # =====================================================

    df_vendas["Ano"] = (
        df_vendas["Ano"]
        .astype(int)
    )

    df_vendas["Mes"] = (
        df_vendas["Mes"]
        .astype(int)
    )

    # =====================================================
    # NOME DOS MESES
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

    df_vendas["Nome Mes"] = (
        df_vendas["Mes"]
        .map(meses_br)
    )

    # =====================================================
    # ANO E MÊS ATUAL
    # =====================================================

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month


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
    # FILTROS
    # =====================================================

    st.sidebar.header("🎯 Filtros")

    vendedores = sorted(
        df_vendas["Vendedor"]
        .dropna()
        .unique()
    )

    equipes = sorted(
        df_vendas["Equipe"]
        .dropna()
        .unique()
    )

    cidades = sorted(
        df_vendas["Cidade"]
        .dropna()
        .unique()
    )

    fabricantes = sorted(
        df_vendas["Fabricante"]
        .dropna()
        .unique()
    )

    produtos = sorted(
        df_vendas["Produto"]
        .dropna()
        .unique()
    )

    clientes_lista = sorted(
        df_vendas["Cliente"]
        .dropna()
        .unique()
    )

    meses = sorted(
        df_vendas["Mes"]
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
        default=meses
    )

    # =====================================================
    # FILTRO PRINCIPAL
    # =====================================================

    filtro_df = (

        df_vendas["Vendedor"].isin(
            filtro_vendedor
        )

        &

        df_vendas["Equipe"].isin(
            filtro_equipe
        )

        &

        df_vendas["Cidade"].isin(
            filtro_cidade
        )

        &

        df_vendas["Fabricante"].isin(
            filtro_fabricante
        )

        &

        df_vendas["Produto"].isin(
            filtro_produto
        )

        &

        df_vendas["Cliente"].isin(
            filtro_cliente
        )

        &

        df_vendas["Mes"].isin(
            filtro_mes
        )

    )

    df_filtrado = df_vendas[
        filtro_df
    ]

    # =====================================================
    # FILTRO META
    # =====================================================

    # META RESPEITA SOMENTE:
    # ✅ VENDEDOR
    # ✅ EQUIPE

    df_base_meta = df_vendas[

        df_vendas["Vendedor"].isin(
            filtro_vendedor
        )

        &

        df_vendas["Equipe"].isin(
            filtro_equipe
        )

    ]

    vendedores_meta = (

        df_base_meta["Vendedor"]

        .dropna()

        .unique()

    )

    df_meta_filtrado = df_meta[

        df_meta["Vendedor"]

        .isin(vendedores_meta)

    ]

    # =====================================================
    # MÊS ATUAL
    # =====================================================

    df_mes_atual = df_filtrado[

        (df_filtrado["Ano"] == ano_atual)

        &

        (df_filtrado["Mes"] == mes_atual)

    ]

    # =====================================================
    # META MÊS ATUAL
    # =====================================================

    meta_mes_atual = df_meta_filtrado[

        (df_meta_filtrado["Ano"] == ano_atual)

        &

        (df_meta_filtrado["Mes"] == mes_atual)

    ]

    # =====================================================
    # KPIs PRINCIPAIS
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

        .groupby("Vendedor")["Meta"]

        .max()

        .sum()

    )

    atingimento = (

        (faturamento / meta_total) * 100

        if meta_total > 0

        else 0

    )

    mix_produtos = int(
        df_mes_atual["Produto"]
        .nunique()
    )

    # =====================================================
    # KPI DIAS ÚTEIS / TENDÊNCIA / OBJETIVO DIA
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

    # =====================================================
    # DIAS ÚTEIS
    # =====================================================

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

    if dias_restantes < 0:

        dias_restantes = 0

    # =====================================================
    # MÉDIA DIÁRIA
    # =====================================================

    media_diaria = (

        faturamento / dias_decorridos

        if dias_decorridos > 0

        else 0

    )

    # =====================================================
    # TENDÊNCIA
    # =====================================================

    tendencia_final = (
        media_diaria
        * total_dias_uteis
    )

    percentual_tendencia = (

        (tendencia_final / meta_total) * 100

        if meta_total > 0

        else 0

    )

    # =====================================================
    # OBJETIVO DIA
    # =====================================================

    falta_meta = (
        meta_total
        - faturamento
    )

    if falta_meta < 0:

        falta_meta = 0

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

    # =====================================================
    # STATUS META
    # =====================================================

    if atingimento >= 100:

        st.success(
            "✅ Meta Batida"
        )

    elif atingimento >= 80:

        st.warning(
            "⚠️ Atenção"
        )

    else:

        st.error(
            "❌ Abaixo da Meta"
        )

    # =====================================================
    # STATUS TENDÊNCIA
    # =====================================================

    if percentual_tendencia >= 100:

        st.success(
            f"🚀 Tendência de fechamento em "
            f"{percentual_tendencia:.1f}% da meta"
        )

    elif percentual_tendencia >= 90:

        st.warning(
            f"⚠️ Tendência de fechamento em "
            f"{percentual_tendencia:.1f}% da meta"
        )

    else:

        st.error(
            f"❌ Tendência de fechamento em "
            f"{percentual_tendencia:.1f}% da meta"
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
        .max()
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
    # EVOLUÇÃO MENSAL
    # =====================================================

    st.subheader(
        "📈 Evolução Mensal"
    )

    evolucao = (
        df_filtrado
        .groupby(["Ano", "Mes"])
        ["Valor Venda"]
        .sum()
        .reset_index()
    )

    fig_evolucao = px.line(
        evolucao,
        x="Mes",
        y="Valor Venda",
        color="Ano",
        markers=True
    )

    st.plotly_chart(
        fig_evolucao,
        use_container_width=True
    )

    # =====================================================
    # TOP PRODUTOS
    # =====================================================

    st.subheader(
        "📦 Top Produtos"
    )

    top_produtos = (
        df_mes_atual
        .groupby("Produto")
        ["Valor Venda"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor Venda",
            ascending=False
        )
        .head(10)
    )

    fig_produtos = px.bar(
        top_produtos,
        x="Produto",
        y="Valor Venda",
        text_auto=True
    )

    st.plotly_chart(
        fig_produtos,
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

    # =====================================================
    # EXPORTAÇÃO CSV
    # =====================================================

    @st.cache_data
    def gerar_csv(df_export):

        return df_export.to_csv(
            index=False
        ).encode("utf-8")

    st.download_button(
        "📥 Baixar Detalhamento CSV",
        gerar_csv(detalhamento),
        "detalhamento.csv",
        "text/csv"
    )

else:

    st.info(
        "Informe os links das planilhas."
    )
