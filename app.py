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

    st.info("Para cadastrar ou editar um paciente, digite seu CPF em qualquer formatação. Por privacidade, somente os 6 dígitos centrais "
            "(\*\*\*.456.789-\*\*) serão armazenados")

    if "cpf" not in st.session_state:
        st.session_state.cpf = ""

    def mascarar_cpf():
        cpf = utils.capturar_cpf(st.session_state.cpf)
        if cpf:
            st.session_state.cpf = cpf

    st.text_input("CPF", key="cpf", on_change=mascarar_cpf)
    cpf = utils.capturar_cpf(st.session_state.cpf)

    if cpf:

        nova_internacao = False
        n_internacao = None
        nome = None

        existencia_cpf, trecho = utils.verificar_existencia_cpf(df, cpf)

        if existencia_cpf:
            st.write("")
            st.success("Um ou mais pacientes foram encontrados para os 6 dígitos centrais do CPF. Selecione o nome ou cadastre um novo.")

            nomes = trecho["Nome do paciente"].dropna().drop_duplicates().tolist()
            nome = st.selectbox("Qual o nome do paciente?", ["-", *nomes, "novo paciente"])

            if nome in nomes:
                trecho = trecho[trecho["Nome do paciente"] == nome]
                n_internacao = st.selectbox("Deseja cadastrar dados de qual internação? (pegando a última por padrão)",
                                            ["-", *trecho["Numero Internacao"].tolist(), "nova internação"],
                                            index=len(trecho["Numero Internacao"].values),
                                            key=f"select_internacao_{cpf}_{nome}_{len(trecho)}")

                if "nova" in n_internacao:
                    nova_internacao = True
                    n_internacao = str(max([int(i) for i in trecho["Numero Internacao"]]) + 1)
                    st.warning("Gerando campos para preencher nova internação")

            elif nome == "novo paciente":
                nova_internacao = True
                nome = st.text_input("Qual o primeiro e último nome do paciente?").strip().replace(".", "").split()
                if nome and len(nome) == 2:
                    nome = nome[0] + " " + nome[-1]
                    n_internacao = "1"
                    st.warning("Gerando campos para preencher nova internação")
                elif nome:
                    st.error("Favor digitar apenas o primeiro e o último nome do paciente")

        else:
            st.info("Paciente ainda não cadastrado. Favor inserir dados.")
            nome = st.text_input("Qual o primeiro e último nome do paciente?").strip().replace(".", "").split()
            if nome and len(nome) == 2:
                nome = nome[0] + " " + nome[-1]
                n_internacao = "1"
                st.warning("Gerando campos para preencher nova internação")
                st.warning(
                    "O CPF e o nome não poderão ser alterados depois. Verifique se estão corretos antes de continuar.")
                nova_internacao = True
            elif nome:
                st.error("Favor digitar apenas o primeiro e o último nome do paciente")


        if n_internacao and n_internacao != "-":
            paciente, hospital_fim, sucesso = forms.gerar_cols(cpf, df, storage, n_internacao, nome)
            if not sucesso:
                st.error("Um dos campos preenchidos se encontra com erro. Corrija para poder prosseguir.")

            else:
                if st.button("salvar e anexar na planilha as informações"):
                    with st.spinner("Aguarde, salvando..."):
                        while not storage.salvar_df(paciente, cpf, utils, hospital_fim, grade, df, nome):
                            st.error("Outro usuário está salvando dados no momento. Tentando novamente em instantes...")
                            time.sleep(5)
                    st.success("Salvo com sucesso! Atualizando planilha...")

                    if nova_internacao and cpf not in st.session_state.nova_internacao:
                        st.session_state.nova_internacao.append(cpf)

                    time.sleep(0.5)
                    st.rerun()


    elif st.session_state.cpf.strip():
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

        tipo_internacao = st.selectbox("Qual tipo de internação deseja gerar dados sobre?",
                                       ["Provisória", "Compulsória"])

        if st.button("Produzir relatório"):
            with st.spinner("aguarde enquanto o relatório é produzido)"):

                df_relatorio = df[df["Tipo Internacao"] == tipo_internacao].reset_index(drop=True)
                estatistica = Estatistica()

                relatorio = Relatorio(estatistica.gerar_estatisticas(df_relatorio, pdr, storage, dados_usuarios))
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
