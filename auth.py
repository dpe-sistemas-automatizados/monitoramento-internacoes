import streamlit as st
import time
from config import EMAIL, EMAIL_SENHA, USUARIOS
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import dropbox
from config import USUARIOS

class Auth:
    def __init__(self, usuarios, storage, utils):
        self.storage = storage
        self.dados = usuarios
        self.email = EMAIL
        self.email_senha = EMAIL_SENHA
        self.utils = utils
        self.link = "https://monitoramento-pacientes-custodia.streamlit.app/"

    def atualizar_login(self, usuario, hoje, tentativas=5):
        for tentativa in range(tentativas):
            try:
                df, rev = self.storage.carregar_df_com_rev(USUARIOS)
                df = self.dados.copy()
                df.loc[df["usuario"]==usuario, "ultima_recuperacao"] = hoje
                excel = self.utils.converter_df_para_xlsx(df)
                self.storage.dbx.files_upload(
                    excel,
                    USUARIOS,
                    mode=dropbox.files.WriteMode.update(rev),
                    autorename=False,
                    mute=True
                )
                self.storage.coletar_login.clear()

            except dropbox.exceptions.ApiError:
                time.sleep(2)

    def encontrar_usuario(self, df, email):
        for i, principais, copias in zip(df.index, df["email_principal"], df["email_copia"]):
            emails = []
            if pd.notna(principais):
                emails = [x.strip() for x in principais.split(",")]
            if pd.notna(copias):
                emails = emails + [x.strip() for x in copias.split(",")]
            if email.strip() in emails:
                return True, df.at[i, "usuario"]
        return False, None

    @st.dialog("Recuperar senha")
    def popup_esqueci_senha(self, df):
        st.markdown("""
        Digite o endereço de e-mail da instituição <br>
        (geralmente: cras.[municipio]@saude.mg.gov.br ou <br>
        saudemental.[municipio]@saude.mg.gov.br.) <br>
        <br>
        Se existir na base de dados, enviaremos um e-mail de recuperação.
        """, unsafe_allow_html=True)

        email = st.text_input("E-mail")
        if st.button("Enviar e-mail de recuperação") and email:
            with st.spinner("carregando..."):
                sucesso, usuario = self.encontrar_usuario(df, email)
                if sucesso:
                    if self.enviar_email(usuario):
                        st.success("E-mail enviado com sucesso. Verificar caixa de entrada.")
                else:
                    st.error("E-mail não cadastrado. Tente novamente.")

    def verificar_recente(self, df, usuario):
        ultima = df[df["usuario"]==usuario]["ultima_recuperacao"].iloc[0]
        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None, microsecond=0)
        if pd.isna(ultima):
            return True
        else:
            if hoje - ultima > timedelta(days=1):
                return True
            else:
                return False

    def enviar_email(self, usuario):
        df = self.dados
        origem = self.email

        linha = df.loc[df["usuario"] == usuario].iloc[0]
        usuario_senha = linha["senha"]
        principais = linha["email_principal"]
        copias = linha["email_copia"]

        if pd.isna(principais) or not str(principais).strip():
            return False

        if not self.verificar_recente(df, usuario):
            st.error("E-mail de recuperação já enviado nas últimas 24 horas. Favor verificar caixa de entrada.")
            st.stop()
            return False

        mensagem = EmailMessage()
        mensagem["Subject"] = "Recuperação de login e senha do Sistema de Monitoramento de Encaminhamentos para Internação Provisória"
        mensagem["from"] = origem
        mensagem["to"] = principais
        if pd.notna(copias) and str(copias).strip() and str(copias).strip().lower() != "nan":
            mensagem["Cc"] = str(copias).strip()
        texto = f"Olá. Foi requisitada uma recuperação de login para este e-mail. Seguem os dados: \n\n"
        texto += f"Usuário: {usuario}\nSenha: {usuario_senha}\n\n"
        texto += f"O sistema pode ser acessado por esse link: {self.link}\n\n"
        texto += ("Para evitar spam, foi configurado que somente pode ser recuperado login uma vez por dia. "
                  "Evite apagar este e-mail.\n\n")
        texto += "Favor não responder este e-mail automático.\n\n"
        texto += "DPE | SAE | SUBRAS | SES"
        mensagem.set_content(texto)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.email, self.email_senha)
            server.send_message(mensagem)

        hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None, microsecond=0)
        self.atualizar_login(usuario, hoje)

        return True

    def sucesso(self):
        st.session_state.logado = True
        time.sleep(0.5)
        st.rerun()

    def logar(self):
        df = self.dados
        #Verificar logado ou admin
        if "admin" in st.session_state:
            if st.session_state.admin:
                return True
        st.session_state.admin = False

        if "logado" in st.session_state:
            if st.session_state.logado:
                return True
        st.session_state.logado = False

        st.title("AUTENTICAÇÃO")
        for _ in range(2):
            st.write("")

        usuario = st.text_input("Digite seu usuário")
        senha = st.text_input("Digite sua senha", type="password")

        st.session_state.usuario = usuario
        st.session_state.senha = senha

        if st.button("Entrar"):
            if usuario in df["usuario"].tolist() and senha == df.loc[df["usuario"] == usuario].iloc[0]["senha"]:
                if df[df["usuario"]==usuario].iloc[0]["nivel"] == "adm":
                    st.success("Bem-vindo(a), administrador(a). Carregando...")
                    st.session_state.admin = True
                else:
                    st.success("Sucesso! Carregando...")
                self.sucesso()

            st.error("Usuário e/ou senha inválido(s)")
            return False

        for _ in range(5):
            st.write("")

        if st.button("Esqueceu o login ou a senha? Clique aqui"):
            self.popup_esqueci_senha(df)
