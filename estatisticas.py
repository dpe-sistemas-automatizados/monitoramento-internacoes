import pandas as pd

class Estatistica:
    def __init__(self):
        self.cols_str = ["Nome do paciente", "CPF", "município de origem", "autuação para quem?",
                    "hospitais encaminhados", "encaminhamento conforme grade de referência?", "hospital final",
                    "Acompanhamento RAPS? (se sim, colocar o município)", "Usuário",
                    "Observações (sinalizar fatores como dificuldades de infraestrutura, de negativa de hospitais etc.)"]
        self.cols_data = ["Data", "data da internação", "data da alta médica", "data de envio do caso para juiz articulador",
                     "data da decisão judicial  expressa da cessação da internação", "data da desospitalização do paciente"]


    def formatar_df(self, df):
        for col in df.columns:
            if col in self.cols_str:
                df[col] = df[col].astype("string")
            elif col in self.cols_data:
                df[col] = pd.to_datetime(df[col], dayfirst=True)
        return df

    def reformatar_df(self, df):
        df = df.copy()
        for col in df.columns:
            if col in self.cols_data:
                df[col] = df[col].apply(lambda x: x.date().strftime("%d/%m/%Y") if pd.notna(x) else "")
        return df

    def fazer_iter(self, df, pdr):
        recusados = []
        estao_internados = []
        alta_nao_desosp = []
        cessado_nao_desosp = []
        sem_raps = []
        desops = []
        pacientes_macro = pdr.copy()
        pacientes_macro["qnt pacientes"] = 0

        for i, row in df.iterrows():
            #Pegar recusados
            cpf = row["CPF"]
            hospitais = row["hospitais encaminhados"]
            hosp_fim = pd.notna(row["hospital final"])
            if pd.notna(hospitais) and ((len(hospitais.split(", ")) > 1) or (len(hospitais.split(", ")) == 1 and not hosp_fim)):
                recusados.append(cpf)

            #Pegar internados
            data_internacao = row["data da internação"]
            data_desosp = row["data da desospitalização do paciente"]
            if pd.notna(data_internacao) and pd.isna(data_desosp):
                estao_internados.append(cpf)

            #Pegar alta não desosp
            data_alta = row["data da alta médica"]
            if pd.notna(data_alta) and pd.isna(data_desosp):
                alta_nao_desosp.append(cpf)

            #cessado não desosp
            data_cessado = row["data da decisão judicial  expressa da cessação da internação"]
            if pd.notna(data_cessado) and pd.isna(data_desosp):
                cessado_nao_desosp.append(cpf)

            #pegar sem raps
            raps = row["Acompanhamento RAPS? (se sim, colocar o município)"]
            if "-" in raps or "não" in raps.lower() or "nao" in raps.lower():
                sem_raps.append(cpf)

            if pd.notna(data_desosp):
                desops.append(cpf)

            #Pegar macro
            munic = row["município de origem"]
            macro_idx = pacientes_macro[pacientes_macro["municipios_formatados"]==munic].index[0]
            pacientes_macro.at[macro_idx, "qnt pacientes"] += 1

        return recusados, estao_internados, alta_nao_desosp, cessado_nao_desosp, sem_raps, desops, pacientes_macro

    def gerar_estatisticas(self, df, pdr, storage, dados_usuarios):
        df = self.formatar_df(df)

        """ ==== INFORMAÇÕES GERAIS ==== """

        recusados, estao_internados, alta_nao_desosp, cessado_nao_desosp, sem_raps, desops, pacientes_macro = self.fazer_iter(df, pdr)

        total_pacientes = len(df)

        def perc(x):
            return x / total_pacientes

        pacientes_nao_grade = df[df["encaminhamento conforme grade de referência?"] == "Não"].reset_index(drop=True)
        pacientes_nao_grade = pacientes_nao_grade[["Nome do paciente", "CPF", "município de origem",
                               "autuação para quem?", "hospitais encaminhados", "hospital final", "municipio do hospital final"]]
        pacientes_sim_grade = df[df["encaminhamento conforme grade de referência?"] == "Sim"].reset_index(drop=True)

        total_nao_grade = len(pacientes_nao_grade)
        total_sim_grade = len(pacientes_sim_grade)

        pacientes_grade = pd.concat([pacientes_nao_grade, pacientes_sim_grade], ignore_index=True)
        total_grade = len(pacientes_grade)

        total_munics = len(df["município de origem"].unique())
        total_micros = len(
            pdr[pdr["municipios_formatados"].isin(df["município de origem"].tolist())]["Microrregião de Saúde"].unique())
        total_macros = len(
            pdr[pdr["municipios_formatados"].isin(df["município de origem"].tolist())]["Macrorregião de Saúde"].unique())

        pdr_macros = len(pdr["Macrorregião de Saúde"].unique())
        pdr_micros = len(pdr["Microrregião de Saúde"].unique())

        total_recusados = len(recusados)

        total_sem_raps = len(sem_raps)

        pacientes_macro = pacientes_macro[["Macrorregião de Saúde", "qnt pacientes"]].groupby("Macrorregião de Saúde", as_index=False).sum()

        dados_gerais = [total_pacientes, total_grade, total_sim_grade, total_nao_grade, total_macros, pdr_macros,
              total_micros, pdr_micros, total_munics, total_recusados, total_sem_raps]

        """ === DADOS DE INTERNAÇÕES === """

        internados = df[df["data da internação"].notna()].reset_index(drop=True)
        total_internados = len(internados)

        nao_internados = df[df["data da internação"].isna()].reset_index(drop=True)
        total_nao_internados = len(nao_internados)

        total_estao_internados = len(estao_internados)

        total_alta_nao_desosp = len(alta_nao_desosp)

        total_cessado_nao_desosp = len(cessado_nao_desosp)

        df_internados = df[df["CPF"].isin(estao_internados)].reset_index(drop=True)
        df_internados["tempo_internacao"] = pd.to_datetime(storage.pegar_data(), dayfirst=True) - df_internados[
            "data da internação"]
        df_internados["tempo_internacao"] = df_internados["tempo_internacao"].apply(lambda x: x.days)
        df_internados = df_internados[["Nome do paciente", "CPF", "tempo_internacao"]].sort_values("tempo_internacao",
                                                                                                   ascending=False)

        internados_7dias = df_internados[df_internados["tempo_internacao"] >= 7]
        internados_14dias = df_internados[df_internados["tempo_internacao"] >= 14]
        internados_28dias = df_internados[df_internados["tempo_internacao"] >= 28]

        total_internados_7dias = len(internados_7dias)
        total_internados_14dias = len(internados_14dias)
        total_internados_28dias = len(internados_28dias)

        df_altados = df[df["CPF"].isin(alta_nao_desosp)].reset_index(drop=True)
        df_altados["tempo_internado"] = pd.to_datetime(storage.pegar_data(), dayfirst=True) - df_altados["data da internação"]
        df_altados["tempo desde alta"] = pd.to_datetime(storage.pegar_data(), dayfirst=True) - df_altados["data da alta médica"]
        df_altados["tempo_internado"] = df_altados["tempo_internado"].apply(lambda x: x.days)
        df_altados["tempo desde alta"] = df_altados["tempo desde alta"].apply(lambda x: x.days)
        df_altados = df_altados[["Nome do paciente", "CPF", "tempo_internado", "tempo desde alta"]].sort_values("tempo desde alta", ascending=False)

        altados_7dias = df_altados[df_altados["tempo desde alta"] >= 7]
        altados_14dias = df_altados[df_altados["tempo desde alta"] >= 14]
        altados_28dias = df_altados[df_altados["tempo desde alta"] >= 28]

        total_altados_7dias = len(altados_7dias)
        total_altados_14dias = len(altados_14dias)
        total_altados_28dias = len(altados_28dias)

        df_cessados = df[df["CPF"].isin(cessado_nao_desosp)].reset_index(drop=True)
        df_cessados["tempo desde decisão"] = pd.to_datetime(storage.pegar_data(), dayfirst=True) - (
            df_cessados["data da decisão judicial  expressa da cessação da internação"])
        df_cessados["tempo desde decisão"] = df_cessados["tempo desde decisão"].apply(lambda x: x.days)
        df_cessados = df_cessados.merge(df_altados[["CPF", "tempo_internado", "tempo desde alta"]], on="CPF", how="left")
        df_cessados = df_cessados[["Nome do paciente", "CPF", "tempo_internado", "tempo desde alta", "tempo desde decisão"]].sort_values(
            "tempo desde decisão",ascending=False)

        df_sem_raps = df[df["CPF"].isin(sem_raps)].reset_index(drop=True)

        df_desops = df[df["CPF"].isin(desops)].reset_index(drop=True)
        df_desops["tempo_desospitalizado"] = pd.to_datetime(storage.pegar_data(), dayfirst=True) - (
            df_desops["data da desospitalização do paciente"])
        df_desops["tempo_desospitalizado"] = df_desops["tempo_desospitalizado"].apply(lambda x: x.days)

        df_desops["tempo_total_internado"] = df_desops["data da desospitalização do paciente"] - (
            df_desops["data da internação"])
        df_desops["tempo_total_internado"] = df_desops["tempo_total_internado"].apply(lambda x: x.days)
        df_desops = df_desops[["Nome do paciente", "CPF", "tempo_desospitalizado", "tempo_total_internado",
                           "Acompanhamento RAPS? (se sim, colocar o município)", "RAPS conforme grade de referência?"]].sort_values("tempo_desospitalizado", ascending=False)
        df_desops = df_desops.merge(df[["CPF", "município de origem", "Qual o tipo de serviço da RAPS?"]], on="CPF", how="left")

        df_desops_sem_raps = df_desops[df_desops["Acompanhamento RAPS? (se sim, colocar o município)"]=="Não"]
        df_desops_sem_raps = df_desops_sem_raps.drop(["Acompanhamento RAPS? (se sim, colocar o município)",
                                         "RAPS conforme grade de referência?"], axis=1)

        df_desops_fora_grade = df_desops[df_desops["RAPS conforme grade de referência?"]=="Não"]
        df_desops_fora_grade = df_desops_fora_grade.drop(["RAPS conforme grade de referência?"], axis=1)

        df_desops_dentro_grade = df_desops[df_desops["RAPS conforme grade de referência?"]!="Não"]
        df_desops_dentro_grade = df_desops_dentro_grade.drop(["RAPS conforme grade de referência?"], axis=1)

        pacientes_sum = df.groupby("Usuário").size().reset_index(name="qtd")[["Usuário", "qtd"]]
        pacientes_usuarios = dados_usuarios.merge(pacientes_sum, left_on="usuario", right_on="Usuário", how="left")[["usuario", "qtd"]]
        pacientes_usuarios["qtd"] = pacientes_usuarios["qtd"].fillna(0).astype(int)

        dados_internados = [total_internados, total_nao_internados, total_estao_internados, total_alta_nao_desosp,
              total_cessado_nao_desosp, total_internados_7dias, total_internados_14dias, total_internados_28dias,
              total_altados_7dias, total_altados_14dias, total_altados_28dias]


        """ === ANEXOS === """
        anexos = [pacientes_macro, pacientes_usuarios, pacientes_nao_grade, df_internados, df_altados, df_cessados,
                  df_desops_sem_raps, df_desops_fora_grade, df_desops_dentro_grade]

        anexos = [self.reformatar_df(x) for x in anexos]

        """ === TRANSFORMAR ESTATÍSTICAS EM LISTAS PARA NOME NO RELATÓRIO === """
        #Escolhi fazer aqui nas estatisticas para, se caso eu mudar as variáveis, ficar mais fácil de localizar no mesmo .py

        dados_gerais = [f"Total de pacientes: {total_pacientes}", f"Pacientes encaminhados conforme a grade: {total_sim_grade}",
                f"Pacientes cujo primeiro hospital enviado estava em desacordo com a grade: {total_nao_grade}",
                f"Pacientes recusados em ao menos um hospital: "
                f"{total_recusados}", f"Pacientes desospitalizados sem acompanhamento RAPS: {len(df_desops_sem_raps)}",
                f"Regionais/usuários com informações preenchidas: {len(df["Usuário"].unique())}/{len(dados_usuarios)}",
                f"Pacientes provindos de {str(total_munics)} municípios, de {str(total_micros)} microrregiões, em "
                f"{str(total_macros)} macrorregiões diferentes"]

        dados_internados = [f"Pacientes desospitalizados: {len(df_desops)}", f"Pacientes que estão internados: {total_estao_internados}",
                f"Pacientes com alta, mas ainda internados: {total_alta_nao_desosp}", "Pacientes com internação cessada por autoridade "
                "judicial, mas ainda internados: "f"{total_cessado_nao_desosp}", f"Pacientes internados 7+ dias: {total_internados_7dias}",
                f"Pacientes internados 14+ dias: {total_internados_14dias}", f"Pacientes internados 28+ dias: {total_internados_28dias}",
                f"Pacientes com alta ainda internados 7+ dias: {total_altados_7dias}", f"Pacientes com alta ainda internados "  
                f"14+ dias: {total_altados_14dias}", f"Pacientes com alta ainda internados 28+ dias: {total_altados_28dias}"]

        anexos_nomes = ["PACIENTES POR MACRO", "PACIENTES POR USUÁRIO (REGIONAL/HOSPITAL PSIQUIÁTRICO)",
                        "PACIENTES CUJO PRIMEIRO HOSPITAL ENCAMINHADO FOI EM DESACORDO COM A GRADE",
                        "PACIENTES AINDA INTERNADOS", "PACIENTES COM ALTA AINDA INTERNADOS",
                        "PACIENTES COM INTERNAÇÃO CESSADA POR AUTORIDADE JUDICIAL, MAS AINDA INTERNADOS",
                        "PACIENTES DESOSPITALIZADOS SEM RAPS", "PACIENTES DESOSPITALIZADOS COM RAPS FORA DA GRADE",
                        "PACIENTES COM RAPS DE ACORDO COM A GRADE (SUCESSO)"]

        anexos = {anexos_nomes[i]: x for i, x in enumerate(anexos)}

        return dados_gerais, dados_internados, anexos
