from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    LongTable,
    Spacer,
    PageBreak,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from io import BytesIO


class Relatorio:
    def __init__(self, estatisticas):
        self.dados_gerais = estatisticas[0]
        self.dados_internados = estatisticas[1]
        self.anexos = estatisticas[2]

    def estilos(self):
        azul_escuro = colors.HexColor("#0F172A")
        azul_medio = colors.HexColor("#1E3A8A")
        cinza_texto = colors.HexColor("#334155")
        cinza_sutil = colors.HexColor("#64748B")

        titulo_style = ParagraphStyle(
            "Titulo",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=28,
            textColor=azul_escuro,
            spaceAfter=24,
            alignment=1
        )

        subtitulo_relatorio_style = ParagraphStyle(
            "SubtituloRelatorio",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=cinza_sutil,
            alignment=1,
            spaceAfter=22
        )

        header1_style = ParagraphStyle(
            "Header1",
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=azul_medio,
            spaceBefore=10,
            spaceAfter=14,
            alignment=0
        )

        header_anexo_style = ParagraphStyle(
            "HeaderAnexo",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=azul_escuro,
            spaceBefore=4,
            spaceAfter=12,
            alignment=0
        )

        texto_style = ParagraphStyle(
            "Texto",
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=cinza_texto,
            spaceAfter=7
        )

        celula_style = ParagraphStyle(
            "Celula",
            fontName="Helvetica",
            fontSize=7,
            leading=8.5,
            textColor=cinza_texto,
            alignment=1,
            wordWrap="CJK"
        )

        celula_header_style = ParagraphStyle(
            "CelulaHeader",
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=colors.white,
            alignment=1,
            wordWrap="CJK"
        )

        return {
            "titulo": titulo_style,
            "subtitulo_relatorio": subtitulo_relatorio_style,
            "header1": header1_style,
            "header_anexo": header_anexo_style,
            "texto": texto_style,
            "celula": celula_style,
            "celula_header": celula_header_style
        }

    def adicionar_rodape(self, canvas, doc):
        canvas.saveState()

        largura_pagina, _ = canvas._pagesize

        margem_direita_visual = 0.8 * cm
        margem_inferior_visual = 0.65 * cm

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))

        canvas.drawRightString(
            largura_pagina - margem_direita_visual,
            margem_inferior_visual,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    def limpar_texto(self, valor):
        if valor is None:
            return ""

        texto = str(valor).strip()

        if texto.lower() in ["nan", "nat", "none"]:
            return ""

        return texto

    def calcular_col_widths(self, df, largura_util):
        colunas = df.columns.tolist()

        if len(colunas) == 0:
            return None

        pesos = []

        for col in colunas:
            nome = str(col).lower()

            if "observ" in nome:
                pesos.append(4.0)
            elif "hospitais" in nome:
                pesos.append(3.4)
            elif "acompanhamento" in nome:
                pesos.append(3.0)
            elif "autuação" in nome or "autuacao" in nome:
                pesos.append(2.6)
            elif "encaminhamento" in nome:
                pesos.append(2.6)
            elif "município" in nome or "municipio" in nome:
                pesos.append(2.1)
            elif "nome" in nome:
                pesos.append(2.2)
            elif "cpf" in nome:
                pesos.append(1.5)
            elif "usuário" in nome or "usuario" in nome:
                pesos.append(1.5)
            elif "data" in nome:
                pesos.append(1.45)
            else:
                pesos.append(2.0)

        soma_pesos = sum(pesos)

        return [
            largura_util * peso / soma_pesos
            for peso in pesos
        ]

    def montar_dados_tabela(self, df):
        celula_style = self.styles["celula"]
        header_style = self.styles["celula_header"]

        dados = []

        cabecalho = [
            Paragraph(self.limpar_texto(col), header_style)
            for col in df.columns
        ]

        dados.append(cabecalho)

        for _, row in df.iterrows():
            linha = [
                Paragraph(self.limpar_texto(valor), celula_style)
                for valor in row.tolist()
            ]

            dados.append(linha)

        return dados

    def formatar_tabela(self, df, largura_util):
        dados = self.montar_dados_tabela(df)

        col_widths = self.calcular_col_widths(
            df,
            largura_util=largura_util
        )

        tabela = LongTable(
            dados,
            colWidths=col_widths,
            repeatRows=1,
            splitByRow=True
        )

        header_color = colors.HexColor("#1E293B")
        linha_alternada = colors.HexColor("#F8FAFC")
        grid_color = colors.HexColor("#CBD5E1")
        linha_header = colors.HexColor("#0F172A")

        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                linha_alternada
            ]),

            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

            ("GRID", (0, 0), (-1, -1), 0.3, grid_color),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, linha_header),

            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2.2),
        ]))

        tabela.hAlign = "CENTER"

        return tabela

    def gerar_relatorio(self):
        buffer = BytesIO()

        self.styles = self.estilos()

        margem = 1.3 * cm
        margem_superior = 1.4 * cm
        margem_inferior = 1.4 * cm

        largura_util = A4[0] - (2 * margem)

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=margem,
            rightMargin=margem,
            topMargin=margem_superior,
            bottomMargin=margem_inferior
        )

        story = []

        story.append(Paragraph(
            "RELATÓRIO DO SISTEMA DE MONITORAMENTO DE ENCAMINHAMENTOS PARA INTERNAÇÃO PROVISÓRIA EM MINAS GERAIS",
            self.styles["titulo"]
        ))

        story.append(Paragraph(
            "Relatório executivo gerado a partir dos registros consolidados no sistema de monitoramento.",
            self.styles["subtitulo_relatorio"]
        ))

        story.append(Paragraph(
            "DADOS GERAIS SOBRE OS PACIENTES",
            self.styles["header1"]
        ))

        story.append(Spacer(1, 6))

        for quote in self.dados_gerais:
            story.append(Paragraph(quote, self.styles["texto"]))

        story.append(PageBreak())

        story.append(Paragraph(
            "DADOS SOBRE INTERNAÇÕES",
            self.styles["header1"]
        ))

        story.append(Spacer(1, 6))

        for quote in self.dados_internados:
            story.append(Paragraph(quote, self.styles["texto"]))

        for texto, df in self.anexos.items():
            story.append(PageBreak())

            story.append(Paragraph(texto, self.styles["header_anexo"]))
            story.append(Spacer(1, 6))

            if len(df) > 0:
                story.append(self.formatar_tabela(
                    df,
                    largura_util=largura_util
                ))
            else:
                story.append(Paragraph(
                    "Nenhum registro encontrado.",
                    self.styles["texto"]
                ))

        doc.build(
            story,
            onFirstPage=self.adicionar_rodape,
            onLaterPages=self.adicionar_rodape
        )

        pdf = buffer.getvalue()
        buffer.close()

        return pdf
