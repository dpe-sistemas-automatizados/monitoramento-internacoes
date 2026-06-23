import dropbox
import streamlit as st
from unidecode import unidecode

cols_censurar = ["CPF"]
cols_esconder = ["Usuário"]
preenchimento_automatico = ["Usuário", "Data", "CPF", "encaminhamento conforme grade de referência?", "hospital final",
                            "hospital final é psiquiátrico?", "RAPS conforme grade de referência?"]

hospitais_psi = ["MARIA MODESTO CRAVO (UBERABA)", "SANATORIO ESPIRITA JOSE DIAS MACHADO (ITUITABA)",
                 "INSTITUTO RAUL SOARES (BELO HORIZONTE)", "HOSPITAL GEDOR SILVEIRA (SAO SEBASTIAO DO PARAISO)"]

APP_KEY = st.secrets["APP_KEY"]
APP_SECRET = st.secrets["APP_SECRET"]
REFRESH_TOKEN = st.secrets["REFRESH_TOKEN"]
EMAIL = st.secrets["EMAIL"]
EMAIL_SENHA = st.secrets["EMAIL_SENHA"]

ARQUIVO_DF = "/planilha monitoramento.xlsx"
ARQUIVO_PDR = "/pdr.xlsx"
ARQUIVO_GRADE = "/grade.xlsx"
USUARIOS = "/usuarios_dados.xlsx"

dbx = dropbox.Dropbox(
    oauth2_refresh_token=REFRESH_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)

class Config:

    @st.cache_data(show_spinner=False)
    def gerar_box(_self, pdr, grade):
        return {
    "autuação para quem?": ["geral", "estado", "município", "prestador"],
    "município de origem": pdr["municipios_formatados"].tolist(),
    "hospitais encaminhados": ["-"] + [unidecode(str(x).strip().upper()) for x in grade[
        grade["Modalidade de serviço"]=="LEITO SM HG"]["Hospital (caso houver)"].unique().tolist()],
    "Acompanhamento RAPS? (se sim, colocar o município)": ["Não"] + pdr["municipios_formatados"].tolist(),
    "Qual o tipo de serviço da RAPS?": ["-"] + sorted(grade["Modalidade de serviço"].unique().tolist()),
    "Tipo Internacao": ["Provisória", "Compulsória"]
}

    def definir_layout(self):
        st.markdown("""
        <style>

        /* ==========================
           FUNDO PRINCIPAL
        ========================== */
        .stApp {
            background: linear-gradient(
                135deg,
                #0F172A 0%,
                #1E293B 50%,
                #334155 100%
            );
        }

        /* ==========================
           TÍTULOS
        ========================== */

        h1 {
            color: #F8FAFC !important;
            font-weight: 750 !important;
            text-align: center;
            letter-spacing: 0.6px;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.28);
            margin-bottom: 0.8rem !important;
        }

        h2, h3 {
            color: #F8FAFC !important;
            font-weight: 700;
        }

        /* Texto normal fora do dialog */
        .stApp p,
        .stApp label {
            color: #E2E8F0 !important;
        }

        /* ==========================
           INPUTS
        ========================== */

        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        .stNumberInput input {
            background-color: rgba(255,255,255,0.94) !important;
            color: #111827 !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
        }

        .stSelectbox div[data-baseweb="select"] > div {
            background-color: rgba(255,255,255,0.94) !important;
            color: #111827 !important;
            border-radius: 12px !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #6B7280 !important;
        }

        /* ==========================
           TABELAS
        ========================== */

        [data-testid="stDataFrame"] {
            background-color: rgba(230, 230, 230, 0.92) !important;
            border-radius: 16px !important;
            padding: 8px;
        }

        [data-testid="stDataFrame"] div {
            color: #111827 !important;
        }

        [data-testid="stDataFrame"] thead tr th {
            background-color: #D1D5DB !important;
            color: #111827 !important;
            font-weight: 700 !important;
        }

        [data-testid="stDataFrame"] tbody tr {
            background-color: rgba(240,240,240,0.95) !important;
        }

        [data-testid="stDataFrame"] tbody tr:hover {
            background-color: rgba(220,220,220,0.95) !important;
        }

        /* ==========================
           REMOVER CARD GLOBAL BUGADO
           Sem afetar dialog
        ========================== */

        .stApp div[data-testid="stVerticalBlock"] > div:not([data-testid="stDialog"]) {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            backdrop-filter: none !important;
        }

        /* ==========================
           BOTÕES GERAIS
        ========================== */

        .stButton > button,
        .stDownloadButton > button {
            background-color: #F8FAFC !important;
            color: #111827 !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            border: none !important;
            padding: 0.6rem 1.2rem !important;
        }

        .stButton > button *,
        .stDownloadButton > button *,
        .stButton > button span,
        .stDownloadButton > button span,
        .stButton > button p,
        .stDownloadButton > button p {
            color: #111827 !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background-color: #E2E8F0 !important;
            color: #111827 !important;
        }

        .stButton > button:hover *,
        .stDownloadButton > button:hover *,
        .stButton > button:hover span,
        .stDownloadButton > button:hover span,
        .stButton > button:hover p,
        .stDownloadButton > button:hover p {
            color: #111827 !important;
        }

        /* ==========================
           SIDEBAR
        ========================== */

        section[data-testid="stSidebar"] {
            background-color: rgba(15,23,42,0.96);
        }

        section[data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }

        /* ==========================
           ABAS
        ========================== */

        div[data-testid="stTabs"] div[role="tablist"] {
            justify-content: center;
        }

        div[data-testid="stTabs"] button[role="tab"] p {
            text-align: center;
        }

        /* ==========================
           CORREÇÃO DO ST.DIALOG
        ========================== */

        div[data-testid="stDialog"] {
            background-color: #FFFFFF !important;
            border-radius: 18px !important;
            color: #111827 !important;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35) !important;
        }

        div[data-testid="stDialog"] > div {
            background-color: #FFFFFF !important;
            border-radius: 18px !important;
            padding: 1.2rem !important;
        }

        div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: initial !important;
            backdrop-filter: none !important;
        }

        div[data-testid="stDialog"] h1,
        div[data-testid="stDialog"] h2,
        div[data-testid="stDialog"] h3,
        div[data-testid="stDialog"] p,
        div[data-testid="stDialog"] label,
        div[data-testid="stDialog"] span,
        div[data-testid="stDialog"] div {
            color: #111827 !important;
        }

        div[data-testid="stDialog"] input,
        div[data-testid="stDialog"] textarea {
            background-color: #FFFFFF !important;
            color: #111827 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
        }

        div[data-testid="stDialog"] input::placeholder,
        div[data-testid="stDialog"] textarea::placeholder {
            color: #6B7280 !important;
        }

        div[data-testid="stDialog"] div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #111827 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
        }

        div[data-testid="stDialog"] .stButton > button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            padding: 0.6rem 1.2rem !important;
            opacity: 1 !important;
        }

        div[data-testid="stDialog"] .stButton > button *,
        div[data-testid="stDialog"] .stButton > button span,
        div[data-testid="stDialog"] .stButton > button p {
            color: #FFFFFF !important;
        }

        div[data-testid="stDialog"] .stButton > button:hover {
            background-color: #1D4ED8 !important;
            color: #FFFFFF !important;
            opacity: 1 !important;
        }

        div[data-testid="stDialog"] .stButton > button:hover *,
        div[data-testid="stDialog"] .stButton > button:hover span,
        div[data-testid="stDialog"] .stButton > button:hover p {
            color: #FFFFFF !important;
        }

        div[data-testid="stDialog"] .stButton > button:disabled {
            background-color: #94A3B8 !important;
            color: #FFFFFF !important;
            opacity: 0.85 !important;
        }

        div[data-testid="stDialog"] .stButton > button:disabled *,
        div[data-testid="stDialog"] .stButton > button:disabled span,
        div[data-testid="stDialog"] .stButton > button:disabled p {
            color: #FFFFFF !important;
        }

        div[data-testid="stDialog"] div[data-testid="stAlert"] {
            border-radius: 12px !important;
        }

        div[data-testid="stDialog"] div[data-testid="stAlert"] * {
            color: inherit !important;
        }

        </style>
        """, unsafe_allow_html=True)
