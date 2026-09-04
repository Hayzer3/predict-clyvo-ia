import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier


class RiskModelService:

    FEATURES = [
        "idade_anos",
        "raca_predisposicao",
        "dias_ultima_vacina",
        "dias_ultimo_vermifugo",
        "variacao_peso_iot"
    ]

    def __init__(self):
        self.modelo = self._treinar_modelo()

    # =========================================================
    # TREINAMENTO DO MODELO
    # =========================================================
    def _treinar_modelo(self):

        print("Treinando modelo tabular Clyvo...")

        np.random.seed(42)

        n_samples = 3000

        df = pd.DataFrame({
            "idade_anos": np.random.randint(
                1,
                16,
                size=n_samples
            ),

            "raca_predisposicao": np.random.choice(
                [0, 1],
                size=n_samples,
                p=[0.7, 0.3]
            ),

            "dias_ultima_vacina": np.random.randint(
                0,
                500,
                size=n_samples
            ),

            "dias_ultimo_vermifugo": np.random.randint(
                0,
                200,
                size=n_samples
            ),

            "variacao_peso_iot": np.random.choice(
                [-1, 0, 1],
                size=n_samples,
                p=[0.15, 0.70, 0.15]
            )
        })

        df["nivel_risco"] = df.apply(
            self._classificar_risco_sintetico,
            axis=1
        )

        X = df[self.FEATURES]
        y = df["nivel_risco"]

        modelo = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            random_state=42
        )

        modelo.fit(
            X,
            y
        )

        print("Modelo tabular Clyvo pronto.")

        return modelo

    # =========================================================
    # REGRA USADA PARA GERAR OS DADOS SINTETICOS
    # =========================================================
    @staticmethod
    def _classificar_risco_sintetico(row):

        pontos_risco = 0

        if row["dias_ultima_vacina"] > 365:
            pontos_risco += 3

        if row["dias_ultimo_vermifugo"] > 90:
            pontos_risco += 2

        if row["variacao_peso_iot"] == -1:
            pontos_risco += 3

        if row["raca_predisposicao"] == 1:
            pontos_risco += 1

        if row["idade_anos"] > 10:
            pontos_risco += 1

        if pontos_risco <= 2:
            return 0

        if pontos_risco <= 5:
            return 1

        return 2

    # =========================================================
    # PREVISAO DE RISCO
    # =========================================================
    def prever(self, dados):

        self._validar_dados(
            dados
        )

        df_input = pd.DataFrame([{
            "idade_anos":
                int(dados["idade_anos"]),

            "raca_predisposicao":
                int(dados["raca_predisposicao"]),

            "dias_ultima_vacina":
                int(dados["dias_ultima_vacina"]),

            "dias_ultimo_vermifugo":
                int(dados["dias_ultimo_vermifugo"]),

            "variacao_peso_iot":
                int(dados["variacao_peso_iot"])
        }])

        probabilidades_modelo = (
            self.modelo.predict_proba(
                df_input
            )[0]
        )

        probabilidades = {
            int(classe): float(probabilidade)
            for classe, probabilidade
            in zip(
                self.modelo.classes_,
                probabilidades_modelo
            )
        }

        prob_saudavel = (
            probabilidades.get(
                0,
                0
            )
        )

        prob_atencao = (
            probabilidades.get(
                1,
                0
            )
        )

        prob_critico = (
            probabilidades.get(
                2,
                0
            )
        )

        # Quanto maior a probabilidade de risco,
        # menor será o Score Clyvo.
        risco_esperado = (
            prob_atencao
            +
            (
                prob_critico
                * 2
            )
        )

        score_base = round(
            100
            -
            (
                risco_esperado
                * 35
            )
        )

        score_base = max(
            0,
            min(
                100,
                score_base
            )
        )

        fatores = (
            self._identificar_fatores(
                dados
            )
        )

        nivel_predito = int(
            self.modelo.predict(
                df_input
            )[0]
        )

        return {
            "score_base":
                score_base,

            "nivel_risco_predito":
                nivel_predito,

            "classificacao_modelo":
                self._nome_classificacao(
                    nivel_predito
                ),

            "probabilidades": {
                "saudavel":
                    round(
                        prob_saudavel,
                        4
                    ),

                "atencao":
                    round(
                        prob_atencao,
                        4
                    ),

                "critico":
                    round(
                        prob_critico,
                        4
                    )
            },

            "fatores_risco":
                fatores
        }

    # =========================================================
    # VALIDACAO DO INPUT
    # =========================================================
    @classmethod
    def _validar_dados(
        cls,
        dados
    ):

        if not isinstance(
            dados,
            dict
        ):
            raise ValueError(
                "Os dados devem ser enviados em formato JSON."
            )

        for feature in cls.FEATURES:

            if feature not in dados:
                raise KeyError(
                    feature
                )

        idade = int(
            dados["idade_anos"]
        )

        predisposicao = int(
            dados["raca_predisposicao"]
        )

        dias_vacina = int(
            dados["dias_ultima_vacina"]
        )

        dias_vermifugo = int(
            dados["dias_ultimo_vermifugo"]
        )

        variacao_peso = int(
            dados["variacao_peso_iot"]
        )

        if idade < 0:
            raise ValueError(
                "idade_anos não pode ser negativa."
            )

        if predisposicao not in [
            0,
            1
        ]:
            raise ValueError(
                "raca_predisposicao deve ser 0 ou 1."
            )

        if dias_vacina < 0:
            raise ValueError(
                "dias_ultima_vacina não pode ser negativo."
            )

        if dias_vermifugo < 0:
            raise ValueError(
                "dias_ultimo_vermifugo não pode ser negativo."
            )

        if variacao_peso not in [
            -1,
            0,
            1
        ]:
            raise ValueError(
                "variacao_peso_iot deve ser -1, 0 ou 1."
            )

    # =========================================================
    # IDENTIFICACAO DOS FATORES DE RISCO
    # =========================================================
    @staticmethod
    def _identificar_fatores(
        dados
    ):

        fatores = []

        if int(
            dados[
                "dias_ultima_vacina"
            ]
        ) > 365:

            fatores.append({
                "codigo":
                    "VACINA_ATRASADA",

                "origem":
                    "HISTORICO",

                "severidade":
                    "ALTA",

                "descricao":
                    (
                        "O histórico indica vacinação "
                        "há mais de 365 dias."
                    )
            })

        if int(
            dados[
                "dias_ultimo_vermifugo"
            ]
        ) > 90:

            fatores.append({
                "codigo":
                    "VERMIFUGO_ATRASADO",

                "origem":
                    "HISTORICO",

                "severidade":
                    "MEDIA",

                "descricao":
                    (
                        "O intervalo desde a última "
                        "vermifugação está acima do "
                        "período monitorado."
                    )
            })

        if int(
            dados[
                "variacao_peso_iot"
            ]
        ) == -1:

            fatores.append({
                "codigo":
                    "PERDA_PESO",

                "origem":
                    "IOT",

                "severidade":
                    "ALTA",

                "descricao":
                    (
                        "Foi identificada redução de "
                        "peso através da telemetria."
                    )
            })

        if int(
            dados[
                "raca_predisposicao"
            ]
        ) == 1:

            fatores.append({
                "codigo":
                    "PREDISPOSICAO_RACA",

                "origem":
                    "PERFIL",

                "severidade":
                    "BAIXA",

                "descricao":
                    (
                        "O perfil informado possui "
                        "predisposição monitorada."
                    )
            })

        if int(
            dados[
                "idade_anos"
            ]
        ) > 10:

            fatores.append({
                "codigo":
                    "IDADE_AVANCADA",

                "origem":
                    "PERFIL",

                "severidade":
                    "BAIXA",

                "descricao":
                    (
                        "A idade do pet exige maior "
                        "acompanhamento preventivo."
                    )
            })

        return fatores

    # =========================================================
    # TRADUCAO DA CLASSE DO MODELO
    # =========================================================
    @staticmethod
    def _nome_classificacao(
        nivel
    ):

        mapa = {
            0:
                "SAUDAVEL",

            1:
                "ATENCAO",

            2:
                "CRITICO"
        }

        return mapa.get(
            nivel,
            "INDETERMINADO"
        )