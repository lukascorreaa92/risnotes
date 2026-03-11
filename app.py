import streamlit as st
import pandas as pd
import os
import shutil
import unicodedata
from io import BytesIO
from openpyxl.styles import Alignment
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


st.set_page_config(page_title="RisNotes - Implantação", layout="wide")

# ==================================================
# SUPABASE
# ==================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==================================================
# AUTENTICAÇÃO
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None

def tela_login():

    st.title("🔐 Login RisNotes")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        try:
            resposta = supabase.auth.sign_in_with_password({
                "email": email,
                "password": senha
            })

            st.session_state.user = resposta.user
            st.rerun()

        except Exception as e:
            st.error("E-mail ou senha inválidos")

if st.session_state.user is None:
    tela_login()
    st.stop()

usuario_email = st.session_state.user.email
usuario_nome = usuario_email.split("@")[0]

PASTA_DADOS = "dados"

if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

ARQUIVO_EXCEL = f"{PASTA_DADOS}/historico_{usuario_nome}.xlsx"
ARQUIVO_BACKUP = f"{PASTA_DADOS}/historico_{usuario_nome}_backup.xlsx"

# ==================================================
# LISTAS GLOBAIS
# ==================================================

lista_cadastros_global = [
    # Coluna Esquerda
    "Usuários",
    "Procedimentos",
    "Honorário Médico",
    "Aparelhos",
    "Salas",
    "Escalas",
    "Indisponibilidades",
    "Restrições de Agenda",
    "Materiais e Kits",
    "Fornecedores",

    # Coluna Direita
    "Estoques",
    "Contas",
    "Formas de Pagamento",
    "Convênios",
    "Planos Convênios",
    "Tabelas de Preço",
    "Regras de Atendimento",
    "Totem",
    "Modelos de Impressão",
    "Acessos netReport"
]

lista_treinos_global = [
    # Coluna Esquerda
    "Cadastro de Colaboradores",
    "Cadastro de Procedimentos",
    "Cadastro de Honorário Médico",
    "Cadastro de Aparelhos/Salas/Escalas",
    "Cadastro de Suprimentos",
    "Cadastro de Financeiro",
    "Cadastro de Convênios",
    "Cadastro de Planos Convênios",

    # Coluna Direita
    "Cadastro de Tabelas de Preço",
    "Cadastro de Regras de Atendimento",
    "Cadastro de Modelos de Impressão",
    "Configuração de Totem",
    "Apresentação Prontuário Eletrônico",
    "Apresentação Agendamento Online",
    "Apresentação Relatórios netReport"
]

# ==================================================
# FUNÇÕES
# ==================================================

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    return texto.strip().lower()

def buscar_ultimo_registro(nome_cliente):
    if not os.path.exists(ARQUIVO_EXCEL):
        return None
    df = pd.read_excel(ARQUIVO_EXCEL)
    nome_busca = normalizar_texto(nome_cliente)
    df_filtrado = df[df['Cliente'].apply(normalizar_texto) == nome_busca]
    if not df_filtrado.empty:
        return df_filtrado.iloc[-1]
    return None

def salvar_no_excel(dados):
    if os.path.exists(ARQUIVO_EXCEL):
        shutil.copy(ARQUIVO_EXCEL, ARQUIVO_BACKUP)
        df_antigo = pd.read_excel(ARQUIVO_EXCEL)
        df_novo = pd.concat([df_antigo, pd.DataFrame([dados])], ignore_index=True)
    else:
        df_novo = pd.DataFrame([dados])

    df_novo.to_excel(ARQUIVO_EXCEL, index=False)

def excluir_registro_df(id_linha):
    df = pd.read_excel(ARQUIVO_EXCEL)
    df = df.drop(index=id_linha)
    df.to_excel(ARQUIVO_EXCEL, index=False)
    st.success("Registro excluído com sucesso!")
    st.rerun()

# ==================================================
# SESSION STATE BASE
# ==================================================

if "cliente_carregado" not in st.session_state:
    st.session_state.cliente_carregado = None

if "lista_pendencias" not in st.session_state:
    st.session_state.lista_pendencias = []

if "lista_notas" not in st.session_state:
    st.session_state.lista_notas = []

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    col1, col2, col3 = st.columns([1,4,1])
    with col2:
        st.image("logo_risnotes.png", width=200)

        # Espaçamento uniforme
        st.markdown("<br>", unsafe_allow_html=True)

        # Linha divisória
        st.markdown(
            """
            <hr style="margin: 10px 0 20px 0;">
            """,
            unsafe_allow_html=True
        )

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stDateInput {
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.header("📍 Identificação")

    nome_input = st.text_input("Cliente")
    registro = None

    if nome_input:
        registro = buscar_ultimo_registro(nome_input)

        if registro is not None:
            st.success("Histórico encontrado!")

            if st.session_state.cliente_carregado != nome_input:
                st.session_state.cliente_carregado = nome_input

                # Reidratar Pendências
                if pd.notna(registro.get("Pendências")):
                    st.session_state.lista_pendencias = registro["Pendências"].split(" | ")
                else:
                    st.session_state.lista_pendencias = []

                # Reidratar Particularidades
                if pd.notna(registro.get("Particularidades")):
                    st.session_state.lista_notas = registro["Particularidades"].split(" | ")
                else:
                    st.session_state.lista_notas = []

                # Reidratar Cadastros
                cad_salvos = registro.get("Cadastros_Implantador", "")
                cad_salvos = cad_salvos.split(", ") if pd.notna(cad_salvos) and cad_salvos else []

                for i, nome in enumerate(lista_cadastros_global):
                    st.session_state[f"cad_{i}"] = nome in cad_salvos

                # Reidratar Treinamentos
                tre_salvos = registro.get("Treinamentos", "")
                tre_salvos = tre_salvos.split(", ") if pd.notna(tre_salvos) and tre_salvos else []

                for i, nome in enumerate(lista_treinos_global):
                    st.session_state[f"tre_{i}"] = nome in tre_salvos

                st.session_state["amb_net"] = registro.get("Ambiente_netReport") == "OK"
                st.session_state["homolog"] = registro.get("Homologacao_Agendada") == "OK"
                st.session_state["rel_val"] = registro.get("Relatorios_Validacao") == "OK"
                st.session_state["prec"] = registro.get("Precificacao") == "OK"

        else:
            st.warning("Cliente novo.")

    uf = st.selectbox("UF", [
        "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
        "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
        "RS","RO","RR","SC","SP","SE","TO"
    ])


    url_deip = st.text_input("URL DEIP")
    url_infra = st.text_input("URL Infra")
    data_visita = st.date_input("Data Acompanhamento")

    st.write("")  # pequeno espaçamento

    if st.button("🚪 Logout", use_container_width=False):
        st.session_state.user = None
        st.rerun()

st.title("📋 RisNotes - Implantação RIS")

# ==================================================
# CADASTROS
# ==================================================

with st.expander("🧾 Cadastros Implantador", expanded=True):

    status_cadastros = {}

    col_esq, col_dir = st.columns(2)

    with col_esq:
        for i in range(10):
            nome = lista_cadastros_global[i]
            status_cadastros[nome] = st.checkbox(nome, key=f"cad_{i}")

    with col_dir:
        for i in range(10, len(lista_cadastros_global)):
            nome = lista_cadastros_global[i]
            status_cadastros[nome] = st.checkbox(nome, key=f"cad_{i}")

# ==================================================
# TREINAMENTOS
# ==================================================

with st.expander("🎓 Treinamentos Realizados", expanded=True):

    status_treinos = {}

    col_esq, col_dir = st.columns(2)

    with col_esq:
        for i in range(8):
            nome = lista_treinos_global[i]
            status_treinos[nome] = st.checkbox(nome, key=f"tre_{i}")

    with col_dir:
        for i in range(8, len(lista_treinos_global)):
            nome = lista_treinos_global[i]
            status_treinos[nome] = st.checkbox(nome, key=f"tre_{i}")

# ==================================================
# VALIDAÇÕES DA IMPLANTAÇÃO
# ==================================================

with st.expander("📌 Validações da Implantação", expanded=True):

    col_esq, col_dir = st.columns(2)

    with col_esq:
        precificacao = st.checkbox("Precificação de Exames", key="prec")
        r_validacao = st.checkbox("Relatórios de Validação", key="rel_val")

    with col_dir:
        amb_net = st.checkbox("Ambiente netReport", key="amb_net")
        homolog = st.checkbox("Homologação Agendada", key="homolog")

# ==================================================
# PENDÊNCIAS + PARTICULARIDADES (LAYOUT ORGANIZADO)
# ==================================================

col_esq, col_dir = st.columns(2)

# ------------------------
# PENDÊNCIAS (ESQUERDA)
# ------------------------

with col_esq:

    st.subheader("⚠️ Pendências")

    if st.button("➕ Adicionar Pendência"):
        st.session_state.lista_pendencias.append("")

    for i, p in enumerate(st.session_state.lista_pendencias):
        c1, c2 = st.columns([0.85, 0.15])
        st.session_state.lista_pendencias[i] = c1.text_input(
            f"Pendência {i+1}",
            value=p,
            key=f"pen_{i}"
        )
        if c2.button("❌", key=f"del_pen_{i}"):
            st.session_state.lista_pendencias.pop(i)
            st.rerun()


# ------------------------
# PARTICULARIDADES (DIREITA)
# ------------------------

with col_dir:

    st.subheader("🔦 Particularidades")

    if st.button("➕ Adicionar Particularidade"):
        st.session_state.lista_notas.append("")

    for i, n in enumerate(st.session_state.lista_notas):
        c1, c2 = st.columns([0.85, 0.15])
        st.session_state.lista_notas[i] = c1.text_area(
            f"Nota {i+1}",
            value=n,
            key=f"not_{i}",
            height=80
        )
        if c2.button("❌", key=f"del_not_{i}"):
            st.session_state.lista_notas.pop(i)
            st.rerun()


st.divider()

# ==================================================
# BOTÃO PRINCIPAL CUSTOMIZADO
# ==================================================

st.markdown(
    """
    <style>
    div.stButton > button {
        height: 65px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

salvar_click = st.button("💾 Gravar Informações", width="content")


# ==================================================
# SALVAR
# ==================================================

if salvar_click:

    concluidos = (
        sum(status_cadastros.values()) +
        sum(status_treinos.values()) +
        int(r_validacao) +
        int(precificacao) +
        int(amb_net) +
        int(homolog)
    )

    total = len(lista_cadastros_global) + len(lista_treinos_global) + 4

    dados = {
        "Data": data_visita.strftime("%d/%m/%Y"),
        "Cliente": nome_input,
        "UF": uf,
        "Status %": int((concluidos / total) * 100),
        "Cadastros_Implantador": ", ".join([c for c, s in status_cadastros.items() if s]),
        "Treinamentos": ", ".join([t for t, s in status_treinos.items() if s]),
        "Relatorios_Validacao": "OK" if r_validacao else "Pendente",
        "Precificacao": "OK" if precificacao else "Pendente",
        "Ambiente_netReport": "OK" if amb_net else "Pendente",
        "Homologacao_Agendada": "OK" if homolog else "Pendente",
        "Pendências": " | ".join(st.session_state.lista_pendencias),
        "Particularidades": " | ".join(st.session_state.lista_notas),
        "DEIP": url_deip,
        "Infra": url_infra
    }

    salvar_no_excel(dados)
    st.success("Salvo com sucesso e atualizado!")
    st.balloons()

# ==================================================
# HISTÓRICO COMPLETO RESTAURADO
# ==================================================

if os.path.exists(ARQUIVO_EXCEL):

    st.divider()
    st.subheader("📚 Histórico de Registros")

    df_view = pd.read_excel(ARQUIVO_EXCEL)

    if not df_view.empty:

        busca = st.text_input("🔍 Pesquisar na tabela")

        if busca:
            df_view = df_view[
                df_view['Cliente'].str.contains(busca, case=False, na=False) |
                df_view['UF'].str.contains(busca, case=False, na=False)
            ]

        st.dataframe(df_view, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_view.to_excel(writer, index=False)
            ws = writer.sheets['Sheet1']
            for idx, col in enumerate(df_view.columns):
                largura = 50 if col in ["Pendências", "Particularidades"] else 20
                ws.column_dimensions[chr(65 + idx)].width = largura
                for cell in ws[chr(65 + idx)]:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')

        st.download_button(
            label="📥 Baixar Histórico como Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Historico_Formatado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        with st.expander("🗑️ Painel de Exclusão"):
            id_del = st.number_input(
                "ID da linha:",
                min_value=0,
                max_value=max(0, len(df_view) - 1)
            )
            if st.button("Confirmar Exclusão Definitiva"):
                excluir_registro_df(id_del)
