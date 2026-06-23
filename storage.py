import dropbox
import pandas as pd
from io import BytesIO
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from dropbox.files import WriteMode
from config import (APP_KEY, APP_SECRET, REFRESH_TOKEN, ARQUIVO_GRADE, ARQUIVO_DF,
                    ARQUIVO_PDR, USUARIOS)
from unidecode import unidecode
import time

class Storage:
    def __init__(self):
        self.dbx = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN,
                                   app_key=APP_KEY,app_secret=APP_SECRET)

    @st.cache_data(show_spinner=False)
    def coletar_login(_self):
        metadata, response = _self.dbx.files_download(USUARIOS)
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl")
        for col in [x for x in df.columns if x != "ultima_recuperacao"]:
            df[col] = df[col].fillna("").astype(str).str.strip()
        df["ultima_recuperacao"] = pd.to_datetime(df["ultima_recuperacao"])
        return df

    @st.cache_data(show_spinner=False)
    def carregar_df(_self):
        metadata, response = _self.dbx.files_download(ARQUIVO_DF)
        return pd.read_excel(BytesIO(response.content), engine="openpyxl", dtype=str)

    def carregar_df_com_rev(self, arquivo):
        metadata, response = self.dbx.files_download(arquivo)
        df = pd.read_excel(BytesIO(response.content), engine="openpyxl", dtype=str)
        return df, metadata.rev

    @st.cache_data(show_spinner=False)
    def carregar_arquivos(_self):
        metadata, response = _self.dbx.files_download(ARQUIVO_PDR)
        pdr = pd.read_excel(BytesIO(response.content), engine="openpyxl")

        metadata, response = _self.dbx.files_download(ARQUIVO_GRADE)
        grade = pd.read_excel(BytesIO(response.content), engine="openpyxl", sheet_name="Grade")
        for col in ["Hospital (caso houver)", "Município"]:
            grade[col] = grade[col].apply(lambda x: unidecode(x.strip().upper().replace("  ", " ")) if pd.notna(x) else None)

        return pdr, grade

    def pegar_data(_self):
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

    def salvar_df(self, paciente, cpf, utils, hospital_fim, grade, df, tentativas=5):
        paciente = utils.completar_paciente(paciente, cpf, hospital_fim, grade, df)
        cpf_paciente = paciente["CPF"]
        n_internacao = paciente["Numero Internacao"]
        paciente = pd.DataFrame([paciente])

        for tentativa in range(tentativas):
            try:
                df, rev = self.carregar_df_com_rev(ARQUIVO_DF)

                if cpf_paciente in df["CPF"].values and n_internacao in df["Numero Internacao"].values:
                    indice = df[(df["CPF"] == cpf_paciente) & (df["Numero Internacao"] == n_internacao)].index[0]

                    for col, valor in paciente.iloc[0].items():
                        df.at[indice, col] = valor

                else:
                    df = pd.concat([df, paciente], ignore_index=True)

                excel = utils.converter_df_para_xlsx(df)

                self.dbx.files_upload(
                    excel,
                    ARQUIVO_DF,
                    mode=dropbox.files.WriteMode.update(rev),
                    autorename=False,
                    mute=True
                )

                self.carregar_df.clear()
                return True

            except dropbox.exceptions.ApiError:
                st.warning(f"Outro usuário também está salvando. Tentando novamente...")
                time.sleep(1)

        return False
