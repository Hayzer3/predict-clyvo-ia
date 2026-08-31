from datetime import datetime, timezone


class HealthScoreService:

    def __init__(
        self,
        risk_service,
        gemini_service
    ):

        self.risk_service = risk_service
        self.gemini_service = gemini_service

    def calcular(
        self,
        pet,
        historico,
        analise_visual=None
    ):

        resultado_modelo = (
            self.risk_service.prever(
                historico
            )
        )

        score_base = resultado_modelo[
            "score_base"
        ]

        fatores = list(
            resultado_modelo[
                "fatores_risco"
            ]
        )

        penalidade_visual = 0

        if analise_visual:

            penalidade_visual = int(
                analise_visual.get(
                    "pontos_risco_visual",
                    0
                )
            )

            penalidade_visual = max(
                0,
                min(20, penalidade_visual)
            )

            if penalidade_visual > 0:

                fatores.append({
                    "codigo":
                        "ALTERACAO_VISUAL",

                    "origem":
                        "IA_VISUAL",

                    "severidade":
                        (
                            "ALTA"
                            if penalidade_visual >= 12
                            else "MEDIA"
                        ),

                    "descricao":
                        (
                            "A análise visual identificou "
                            f"condição corporal classificada "
                            f"como "
                            f"{analise_visual.get('condicao_corporal')}."
                        )
                })

        score_final = (
            score_base
            -
            penalidade_visual
        )

        score_final = max(
            0,
            min(100, score_final)
        )

        status = self._classificar_status(
            score_final
        )

        prioridade = (
            self._definir_prioridade(
                status
            )
        )

        necessita_alerta = (
            status != "SAUDAVEL"
        )

        nome_pet = pet.get(
            "nome",
            "Pet"
        )

        recomendacao = (
            self.gemini_service
            .gerar_recomendacao(
                nome_pet=nome_pet,
                score=score_final,
                status=status,
                fatores=fatores
            )
        )

        alerta = self._montar_alerta(
            nome_pet=nome_pet,
            score=score_final,
            status=status,
            prioridade=prioridade,
            recomendacao=recomendacao,
            necessario=necessita_alerta
        )

        return {
            "versao": "2.0",

            "pet": {
                "id": pet.get("id"),
                "nome": nome_pet
            },

            "score_saude": score_final,

            "score_base_modelo":
                score_base,

            "penalidade_visual":
                penalidade_visual,

            "status_saude":
                status,

            "prioridade":
                prioridade,

            "fatores_risco":
                fatores,

            "probabilidades_modelo":
                resultado_modelo[
                    "probabilidades"
                ],

            "recomendacao":
                recomendacao,

            "alerta":
                alerta,

            "processado_em":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "modelo": {
                "tipo":
                    "RandomForestClassifier",

                "dados_treinamento":
                    "SINTETICOS",

                "finalidade":
                    "PROTOTIPO_ACADEMICO"
            }
        }

    @staticmethod
    def _classificar_status(score):

        if score >= 80:
            return "SAUDAVEL"

        if score >= 60:
            return "ATENCAO"

        return "CRITICO"

    @staticmethod
    def _definir_prioridade(status):

        mapa = {
            "SAUDAVEL": "BAIXA",
            "ATENCAO": "MEDIA",
            "CRITICO": "ALTA"
        }

        return mapa[status]

    @staticmethod
    def _montar_alerta(
        nome_pet,
        score,
        status,
        prioridade,
        recomendacao,
        necessario
    ):

        if not necessario:

            return {
                "necessario": False,
                "evento":
                    "PET_HEALTH_STABLE",

                "codigo":
                    "HEALTH_SCORE_OK",

                "prioridade":
                    prioridade,

                "mensagem_sugerida":
                    None
            }

        if status == "CRITICO":

            codigo = (
                "HEALTH_SCORE_CRITICAL"
            )

        else:

            codigo = (
                "HEALTH_SCORE_ATTENTION"
            )

        mensagem = (
            f"Alerta de saúde - {nome_pet}\n\n"
            f"Score Clyvo: {score}/100\n"
            f"Status: {status}\n\n"
            f"{recomendacao}"
        )

        return {
            "necessario": True,

            "evento":
                "PET_HEALTH_RISK_DETECTED",

            "codigo":
                codigo,

            "prioridade":
                prioridade,

            "mensagem_sugerida":
                mensagem
        }