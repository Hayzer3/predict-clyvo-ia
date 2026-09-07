import base64
import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from config import GOOGLE_API_KEY, GEMINI_MODEL


class GeminiService:

    def __init__(self):

        self.llm = None

        if GOOGLE_API_KEY:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=GEMINI_MODEL,
                    temperature=0.1,
                    api_key=GOOGLE_API_KEY
                )

                print("Gemini inicializado com sucesso.")

            except Exception as e:
                print(
                    "Erro ao inicializar Gemini:",
                    e
                )

    # =========================================================
    # ANALISE VISUAL DE SAUDE
    # =========================================================
    def analisar_imagem(
        self,
        imagem_bytes,
        mime_type
    ):

        if self.llm is None:
            raise RuntimeError(
                "Gemini não inicializado."
            )

        image_base64 = base64.b64encode(
            imagem_bytes
        ).decode("ascii")

        image_uri = (
            f"data:{mime_type};base64,"
            f"{image_base64}"
        )

        prompt = """
Você é um componente de apoio à triagem veterinária
do sistema Clyvo.

Analise exclusivamente características visualmente
observáveis na fotografia.

Não realize diagnóstico de doenças.

Retorne ESTRITAMENTE um JSON válido:

{
  "especie": "Cao | Gato | Indeterminado",
  "raca_estimada": "string",
  "condicao_corporal": "Abaixo do peso | Ideal | Sobrepeso | Obeso | Indeterminado",
  "observacoes_visuais": [
    "string"
  ],
  "alerta_risco_visual": "string"
}

Não escreva nada fora do JSON.
"""

        mensagem = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_uri
                    }
                }
            ]
        )

        resposta = self.llm.invoke(
            [mensagem]
        )

        texto = self._extrair_texto(
            resposta.content
        )

        resultado = self._extrair_json(
            texto
        )

        condicao = resultado.get(
            "condicao_corporal",
            "Indeterminado"
        )

        penalidades = {
            "Ideal": 0,
            "Sobrepeso": 8,
            "Obeso": 15,
            "Abaixo do peso": 12,
            "Indeterminado": 0
        }

        resultado[
            "pontos_risco_visual"
        ] = penalidades.get(
            condicao,
            0
        )

        return resultado

    # =========================================================
    # ANALISE DE FOTO PARA CADASTRO AUTOMATICO
    # =========================================================
    def analisar_foto_cadastro(
        self,
        imagem_bytes,
        mime_type
    ):

        if self.llm is None:
            raise RuntimeError(
                "Gemini não inicializado."
            )

        image_base64 = base64.b64encode(
            imagem_bytes
        ).decode("ascii")

        image_uri = (
            f"data:{mime_type};base64,"
            f"{image_base64}"
        )

        prompt = """
Você é um componente de visão computacional do sistema Clyvo,
utilizado para auxiliar o tutor durante o cadastro de cães e gatos.

Analise apenas características visualmente observáveis na fotografia.

Sua função NÃO é realizar diagnóstico veterinário.

Identifique, quando possível:

- espécie;
- raça estimada;
- cor predominante;
- porte estimado;
- faixa aproximada de peso;
- condição corporal aparente;
- características visuais relevantes.

REGRAS IMPORTANTES:

1. Não invente informações quando não for possível identificar.
2. O peso NÃO deve ser apresentado como valor exato.
3. Retorne apenas uma faixa aproximada de peso.
4. A raça é apenas uma estimativa visual.
5. Se o animal aparentar ser sem raça definida, use "SRD".
6. Se não conseguir determinar algo, use "Indeterminado".
7. A confiança deve estar entre 0.0 e 1.0.
8. A confiança representa o nível geral de segurança da análise visual.
9. Não escreva nada fora do JSON.

Retorne ESTRITAMENTE este JSON:

{
  "especie": "Cao | Gato | Indeterminado",
  "raca_estimada": "string",
  "cor_predominante": "string",
  "porte_estimado": "Pequeno | Medio | Grande | Indeterminado",
  "faixa_peso_estimada_kg": {
    "min": 0.0,
    "max": 0.0
  },
  "condicao_corporal": "Abaixo do peso | Ideal | Sobrepeso | Obeso | Indeterminado",
  "caracteristicas_visuais": [
    "string"
  ],
  "confianca": 0.0
}
"""

        mensagem = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_uri
                    }
                }
            ]
        )

        resposta = self.llm.invoke(
            [mensagem]
        )

        texto = self._extrair_texto(
            resposta.content
        )

        resultado = self._extrair_json(
            texto
        )

        return self._validar_cadastro_pet(
            resultado
        )

    # =========================================================
    # GERACAO DE RECOMENDACAO PARA O TUTOR
    # =========================================================
    def gerar_recomendacao(
        self,
        nome_pet,
        score,
        status,
        fatores
    ):

        if not fatores:
            return (
                f"Os indicadores atuais de {nome_pet} "
                "não apresentam alterações relevantes "
                "dentro dos parâmetros monitorados."
            )

        if self.llm is None:
            return self._recomendacao_fallback(
                nome_pet,
                status
            )

        fatores_texto = "\n".join(
            [
                f"- {f['descricao']}"
                for f in fatores
            ]
        )

        prompt = f"""
Você é o assistente de acompanhamento preventivo
do sistema veterinário Clyvo.

Pet: {nome_pet}
Score de saúde: {score}/100
Classificação: {status}

Fatores identificados:
{fatores_texto}

Crie uma orientação curta para o tutor.

Regras:

- máximo 3 frases;
- linguagem simples;
- não diagnostique doenças;
- não afirme que o animal possui uma doença;
- quando houver risco relevante, recomende avaliação
  de um médico-veterinário;
- deixe claro que o sistema é preventivo;
- não use markdown.
"""

        try:

            resposta = self.llm.invoke(
                [
                    HumanMessage(
                        content=prompt
                    )
                ]
            )

            return self._extrair_texto(
                resposta.content
            ).strip()

        except Exception:

            return self._recomendacao_fallback(
                nome_pet,
                status
            )

    # =========================================================
    # FALLBACK DA RECOMENDACAO
    # =========================================================
    @staticmethod
    def _recomendacao_fallback(
        nome_pet,
        status
    ):

        if status == "CRITICO":

            return (
                f"Os indicadores de {nome_pet} "
                "apresentaram alterações relevantes. "
                "Considere procurar orientação de um "
                "médico-veterinário. O alerta é "
                "preventivo e não representa diagnóstico."
            )

        return (
            f"Alguns indicadores de {nome_pet} "
            "merecem acompanhamento. Continue "
            "monitorando o pet e considere orientação "
            "veterinária caso as alterações persistam."
        )

    # =========================================================
    # EXTRACAO DE TEXTO DA RESPOSTA GEMINI
    # =========================================================
    @staticmethod
    def _extrair_texto(content):

        if isinstance(
            content,
            str
        ):
            return content

        if isinstance(
            content,
            list
        ):

            textos = []

            for item in content:

                if isinstance(
                    item,
                    str
                ):
                    textos.append(
                        item
                    )

                elif isinstance(
                    item,
                    dict
                ):

                    texto = (
                        item.get("text")
                        or item.get("content")
                    )

                    if texto:
                        textos.append(
                            str(texto)
                        )

            return "\n".join(
                textos
            )

        return str(
            content
        )

    # =========================================================
    # EXTRACAO DE JSON DA RESPOSTA GEMINI
    # =========================================================
    @staticmethod
    def _extrair_json(texto):

        texto = texto.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        match = re.search(
            r"\{.*\}",
            texto,
            re.DOTALL
        )

        if not match:
            raise ValueError(
                "Gemini não retornou JSON válido."
            )

        try:
            return json.loads(
                match.group()
            )

        except json.JSONDecodeError as e:

            raise ValueError(
                f"JSON inválido retornado pelo Gemini: {e}"
            )

    # =========================================================
    # VALIDACAO DA RESPOSTA DO CADASTRO
    # =========================================================
    @staticmethod
    def _validar_cadastro_pet(
        resultado
    ):

        especies_validas = {
            "Cao",
            "Gato",
            "Indeterminado"
        }

        portes_validos = {
            "Pequeno",
            "Medio",
            "Grande",
            "Indeterminado"
        }

        condicoes_validas = {
            "Abaixo do peso",
            "Ideal",
            "Sobrepeso",
            "Obeso",
            "Indeterminado"
        }

        especie = resultado.get(
            "especie",
            "Indeterminado"
        )

        if especie not in especies_validas:
            especie = "Indeterminado"

        porte = resultado.get(
            "porte_estimado",
            "Indeterminado"
        )

        if porte not in portes_validos:
            porte = "Indeterminado"

        condicao = resultado.get(
            "condicao_corporal",
            "Indeterminado"
        )

        if condicao not in condicoes_validas:
            condicao = "Indeterminado"

        confianca = resultado.get(
            "confianca",
            0
        )

        try:
            confianca = float(
                confianca
            )

        except (
            TypeError,
            ValueError
        ):
            confianca = 0

        confianca = max(
            0,
            min(
                1,
                confianca
            )
        )

        faixa_peso = resultado.get(
            "faixa_peso_estimada_kg",
            {}
        )

        if not isinstance(
            faixa_peso,
            dict
        ):
            faixa_peso = {}

        try:
            peso_min = float(
                faixa_peso.get(
                    "min",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):
            peso_min = 0

        try:
            peso_max = float(
                faixa_peso.get(
                    "max",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):
            peso_max = 0

        if peso_min < 0:
            peso_min = 0

        if peso_max < peso_min:
            peso_max = peso_min

        caracteristicas = resultado.get(
            "caracteristicas_visuais",
            []
        )

        if not isinstance(
            caracteristicas,
            list
        ):
            caracteristicas = []

        raca = resultado.get(
            "raca_estimada",
            "Indeterminado"
        )

        cor = resultado.get(
            "cor_predominante",
            "Indeterminado"
        )

        return {
            "especie":
                especie,

            "raca_estimada":
                str(raca),

            "cor_predominante":
                str(cor),

            "porte_estimado":
                porte,

            "faixa_peso_estimada_kg": {
                "min":
                    round(
                        peso_min,
                        1
                    ),

                "max":
                    round(
                        peso_max,
                        1
                    )
            },

            "condicao_corporal":
                condicao,

            "caracteristicas_visuais":
                caracteristicas,

            "confianca":
                round(
                    confianca,
                    2
                )
        }