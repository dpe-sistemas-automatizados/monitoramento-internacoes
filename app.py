#Fazer importações
import streamlit as st
import time
from storage import Storage
from utils import Utils
from auth import Auth
from config import Config
from forms import Forms
from estatisticas import Estatistica
from relatorio import Relatorio

# =========================================
# INICIAL
# =========================================

#Tela de carregamento
st.set_page_config("Monitoramento Internações", layout="centered")
config = Config()
config.definir_layout()

placeholder = st.empty()
placeholder.info("Iniciando o sistema. Favor aguardar.")

#Inicializando robôs para login
storage = Storage()
dados_usuarios = storage.coletar_login()
pdr, grade = storage.carregar_arquivos()
utils = Utils(pdr, grade, storage)
forms = Forms(config.gerar_box(pdr, grade))
auth = Auth(dados_usuarios, storage, utils)

#Setting inicial
placeholder.empty()
if not auth.logar():
    st.stop()

df = storage.carregar_df()
if not "nova_internacao" in st.session_state:
    st.session_state.nova_internacao = []

# =========================================
# INTERFACE PRINCIPAL
# =========================================

st.markdown("<h1 style='text-align: center;'>Sistema de Monitoramento de Encaminhamentos para Internação Provisória/Compulsória</h1>",
            unsafe_allow_html=True)

if not st.session_state.admin:
    aba1, aba2, aba3 = st.tabs(["planilha geral", "cadastrar/editar paciente", "seus pacientes"])

else:
    aba1, aba2, aba3, aba4, aba5 = st.tabs(["planilha geral", "cadastrar/editar paciente",
                                      "planilha completa (admin)", "relatório (admin)", "dados dos usuários (admin)"])

with aba1:
    st.markdown(
        "<h2 style='text-align: center;'>Planilha Geral</h2>",
        unsafe_allow_html=True
    )
    st.dataframe(utils.censurar(df))
    st.info("Para fins de privacidade, o CPF e os sobrenomes dos pacientes foram censurados.")

with (aba2):
    st.markdown(
        "<h2 style='text-align: center;'>Cadastrar/Editar Paciente</h2>",
        unsafe_allow_html=True)
    st.info("Preencha o CPF do paciente (qualquer formatação) e aperte enter. Se houver informações cadastradas, elas serão recuperadas")
    cpf = st.text_input("CPF").strip()
    if cpf:
        cpf = utils.capturar_cpf(cpf)

        if cpf:
            existence, idx = utils.verificar_existencia_cpf(df, cpf)
            nova_internacao = False

            if existence:
                linha = df[df["CPF"] == cpf]
                st.write("")
                st.success("Paciente localizado.")

                if cpf in st.session_state.nova_internacao: #Debuggar para novos salvamentos
                    n_internacao = st.selectbox("Deseja cadastrar dados de qual internação?", ["-"] +
                                                linha["Numero Internacao"].values.tolist() + ["nova internação"],
                                                index=len(linha["Numero Internacao"].values))

                else:
                    n_internacao = st.selectbox("Deseja cadastrar dados de qual internação?",
                                 ["-"] + linha["Numero Internacao"].values.tolist() + ["nova internação"])

                if "nova" in n_internacao:
                    nova_internacao = True
                    n_internacao = str(max([int(i) for i in linha["Numero Internacao"]]) + 1)
                    st.warning("Gerando campos para preencher nova internação")

            else:
                st.info("Paciente ainda não cadastrado. Favor inserir dados.")
                st.warning("O CPF não poderá ser alterado depois. Verifique se está correto antes de continuar.")
                n_internacao = "1"


            if n_internacao != "-" and n_internacao:
                paciente, hospital_fim, sucesso = forms.gerar_cols(cpf, df, existence, storage, n_internacao)
                if not sucesso:
                    st.error("Um dos campos preenchidos se encontra com erro. Corrija para poder prosseguir.")

                else:
                    if st.button("salvar e anexar na planilha as informações"):
                        with st.spinner("Aguarde, salvando..."):
                            while not storage.salvar_df(paciente, cpf, utils, hospital_fim, grade, df):
                                st.error("Outro usuário está salvando dados no momento. Tentando novamente em instantes...")
                                time.sleep(5)
                        st.success("Salvo com sucesso! Atualizando planilha...")

                        if nova_internacao and cpf not in st.session_state.nova_internacao:
                            st.session_state.nova_internacao.append(cpf)

                        time.sleep(0.5)
                        st.rerun()
        else:
            st.error("CPF inválido. Tente novamente.")

if not st.session_state.admin:
    with aba3:
        st.markdown(
            "<h2 style='text-align: center;'>Verificar Informações Cadastradas</h2>",
            unsafe_allow_html=True
        )
        st.info("Verifique as informações dos seus pacientes aqui.")
        df_usuario = df[df["Usuário"] == st.session_state.usuario].reset_index(drop=True)

        if len(df_usuario) > 0:
            st.dataframe(df_usuario)
            st.write("Algumas das colunas foram preenchidas automaticamente pelo sistema, conforme a grade de serviços da RAPS")

        else:
            st.error("Seu usuário ainda não tem paciente cadastrado. Cadastre e retorne nesta aba.")
        st.info('Para alterar informações, favor digitar o CPF do usuário na aba anterior, de "cadastrar/editar paciente"')

if st.session_state.admin:
    with aba3:
        st.markdown(
            "<h2 style='text-align: center;'>Planilha Completa</h2>",
            unsafe_allow_html=True
        )
        st.info("Espaço exclusivo para administradores do sistema 😎")
        filtro_aba3 = st.multiselect("filtrar usuário/regional",df["Usuário"].dropna().unique().tolist())
        df_aba3 = df[df["Usuário"].isin(filtro_aba3)].reset_index(drop=True) if filtro_aba3 else df.copy()
        st.dataframe(df_aba3)
        st.download_button(label="Baixar planilha em Excel",
            data=utils.converter_df_para_xlsx(df_aba3),
            file_name="planilha_monitoramento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with aba4:
        st.markdown(
            "<h2 style='text-align: center;'>Relatórios</h2>",
            unsafe_allow_html=True
        )
        st.info("Espaço exclusivo para administradores do sistema 😎")

        if st.button("Produzir relatório"):
            with st.spinner("aguarde enquanto o relatório é produzido)"):
                estatistica = Estatistica()

                relatorio = Relatorio(estatistica.gerar_estatisticas(df, pdr, storage, dados_usuarios))
                pdf = relatorio.gerar_relatorio()

                st.success("PDF criado com sucesso! Clique abaixo para fazer download.")
                st.download_button(
                    label="Baixar relatório em PDF",
                    data=pdf,
                    file_name="relatorio_pacientes_custodia.pdf",
                    mime="application/pdf"
                )

    with aba5:
        st.markdown(
            "<h2 style='text-align: center;'>Usuários e Senhas</h2>",
            unsafe_allow_html=True
        )
        st.info("Espaço exclusivo para administradores do sistema 😎")
        st.dataframe(dados_usuarios)
