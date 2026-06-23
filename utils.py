import pandas as pd
import streamlit as st
import re
from io import BytesIO
from config import cols_censurar, cols_esconder, hospitais_psi

class Utils:
    def __init__(self, pdr, grade, storage):
        self.pdr = pdr
        self.grade = grade
        self.storage = storage

    def censurar(self, df):
        df = df.copy()
        for col in df.columns:
            if col in cols_censurar:
                df[col] = "[CENSURADO]"
        for i, nome in df["Nome do paciente"].items():
            nomes = nome.strip().split(" ")
            nome_final = nomes[0]
            if len(nomes) > 1:
                for nome in nomes[1:]:
                    nome_final += " " + nome[0] + "[...]"
            df.at[i, "Nome do paciente"] = nome_final

        return df.drop(cols_esconder, axis=1)

    def validar_cpf(self, cpf):
        return bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))

    def verificar_existencia_cpf(self, df, cpf):
        values = df["CPF"].values.tolist()
        if cpf in values:
            return True, values.index(cpf)
        else:
            return False, None

    def verificar_colunas_para_grade(self, paciente):
        if paciente.get("município de origem") and paciente.get("hospitais encaminhados") and paciente.get("hospitais encaminhados") != "-":
            return True
        return False

    def munic_hospital_final(self, paciente, df):
        grade = self.grade
        hosp = paciente.get("hospital final")
        munic = grade.loc[(grade["Hospital (caso houver)"]==hosp) & (grade["Modalidade de serviço"]=="LEITO SM HG"), "Município"].iloc[0]
        return munic if munic else "Não encontrado"

    def raps_grade(self, paciente, grade):
        raps_munic = paciente["Acompanhamento RAPS? (se sim, colocar o município)"]
        if raps_munic.lower() not in ["não", "-"]:
            servico = paciente["Qual o tipo de serviço da RAPS?"]
            paciente_munic = paciente["município de origem"]
            munics = []
            for municipio in grade[(grade["Município"]==raps_munic) & (grade["Modalidade de serviço"]==servico)]["Municipios Referenciados "]:
                if pd.notna(municipio):
                    munics.extend([x.strip() for x in municipio.split(",")])
            if paciente_munic in munics:
                return "Sim"
            else:
                return "Não"
        else:
            return None

    def verificar_encaminhamento_grade(self, paciente):
        hospital = [x for x in paciente["hospitais encaminhados"].split(", ")][0]
        origem = paciente["município de origem"]
        grade = self.grade.copy()
        grade = grade[grade["Hospital (caso houver)"] == hospital]
        referenciados = []
        for municipio in grade["Municipios Referenciados "].dropna():
            referenciados.extend([y.strip() for y in municipio.split(",")])
        return origem in referenciados

    def completar_paciente(self, paciente, cpf, hospital_fim, grade, df):
        paciente["CPF"] = cpf
        paciente["Data"] = self.storage.pegar_data()
        paciente["Usuário"] = st.session_state.usuario
        paciente["RAPS conforme grade de referência?"] = self.raps_grade(paciente, grade)

        if hospital_fim:
            paciente["hospital final"] = [x.strip() for x in paciente["hospitais encaminhados"].split(",")][-1]
            paciente["municipio do hospital final"] = self.munic_hospital_final(paciente, df)
            if paciente["hospital final"] in hospitais_psi:
                paciente["hospital final é psiquiátrico?"] = "Sim"
            else:
                paciente["hospital final é psiquiátrico?"] = "Não"
        else:
            paciente["hospital final"] = None
            paciente["hospital final é psiquiátrico?"] = None
            paciente["municipio do hospital final"] = None

        if self.verificar_colunas_para_grade(paciente):
            grade_bool = self.verificar_encaminhamento_grade(paciente)
            if grade_bool:
                paciente["encaminhamento conforme grade de referência?"] = "Sim"
            else:
                paciente["encaminhamento conforme grade de referência?"] = "Não"
        else:
            paciente["encaminhamento conforme grade de referência?"] = "Sem informações"

        return paciente

    def converter_df_para_xlsx(self, df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output.getvalue()

    def capturar_cpf(self, cpf):
        cpf = re.sub(r"\D", "", cpf)
        if len(cpf) == 11:
            cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        else:
            cpf = None
        return cpf
