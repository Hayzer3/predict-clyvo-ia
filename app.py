import os
import tempfile

from flask import (
    Flask,
    request,
    jsonify
)

from config import MAX_IMAGE_SIZE

from services.risk_model_service import (
    RiskModelService
)

from services.gemini_service import (
    GeminiService
)

from services.health_score_service import (
    HealthScoreService
)


app = Flask(__name__)


# =========================================================
# SERVICES
# =========================================================

risk_service = RiskModelService()

gemini_service = GeminiService()

health_score_service = (
    HealthScoreService(
        risk_service=risk_service,
        gemini_service=gemini_service
    )
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/api/v2/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "service":
            "clyvo-ai",

        "status":
            "online",

        "version":
            "2.0"
    }), 200


# =========================================================
# SCORE HISTORICO / RANDOM FOREST
# =========================================================

@app.route(
    "/api/v2/score/historico",
    methods=["POST"]
)
def score_historico():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({
                "erro":
                    "JSON não informado."
            }), 400

        resultado = (
            risk_service.prever(
                dados
            )
        )

        return jsonify(
            resultado
        ), 200

    except KeyError as e:

        return jsonify({
            "erro":
                "Campo obrigatório ausente.",

            "campo":
                str(e)
        }), 400

    except ValueError as e:

        return jsonify({
            "erro":
                "Valor inválido.",

            "detalhes":
                str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "erro":
                "Falha ao calcular risco.",

            "detalhes":
                str(e)
        }), 500


# =========================================================
# ANALISE VISUAL DE SAUDE
# =========================================================

@app.route(
    "/api/v2/score/visual",
    methods=["POST"]
)
def score_visual():

    arquivo, erro = (
        _validar_imagem_request()
    )

    if erro:
        return erro

    tmp_path = None

    try:

        tmp_path = (
            _salvar_imagem_temporaria(
                arquivo
            )
        )

        erro_tamanho = (
            _validar_tamanho_imagem(
                tmp_path
            )
        )

        if erro_tamanho:
            return erro_tamanho

        with open(
            tmp_path,
            "rb"
        ) as f:

            imagem_bytes = (
                f.read()
            )

        resultado = (
            gemini_service
            .analisar_imagem(
                imagem_bytes=
                    imagem_bytes,

                mime_type=
                    arquivo.mimetype
            )
        )

        return jsonify({
            "analise_visual":
                resultado
        }), 200

    except Exception as e:

        return jsonify({
            "erro":
                "Falha na análise visual.",

            "detalhes":
                str(e)
        }), 500

    finally:

        _remover_arquivo_temporario(
            tmp_path
        )


# =========================================================
# ANALISE DA FOTO PARA CADASTRO AUTOMATICO
# =========================================================

@app.route(
    "/api/v2/pets/analyze-registration-photo",
    methods=["POST"]
)
def analisar_foto_cadastro_pet():

    arquivo, erro = (
        _validar_imagem_request()
    )

    if erro:
        return erro

    tmp_path = None

    try:

        tmp_path = (
            _salvar_imagem_temporaria(
                arquivo
            )
        )

        erro_tamanho = (
            _validar_tamanho_imagem(
                tmp_path
            )
        )

        if erro_tamanho:
            return erro_tamanho

        with open(
            tmp_path,
            "rb"
        ) as f:

            imagem_bytes = (
                f.read()
            )

        resultado = (
            gemini_service
            .analisar_foto_cadastro(
                imagem_bytes=
                    imagem_bytes,

                mime_type=
                    arquivo.mimetype
            )
        )

        return jsonify({
            "origem":
                "IA_VISUAL",

            "requer_confirmacao":
                True,

            "analise_cadastro":
                resultado,

            "aviso":
                (
                    "As informações foram "
                    "estimadas por inteligência "
                    "artificial e devem ser "
                    "confirmadas pelo tutor."
                )
        }), 200

    except Exception as e:

        return jsonify({
            "erro":
                "Falha ao analisar foto do pet.",

            "detalhes":
                str(e)
        }), 500

    finally:

        _remover_arquivo_temporario(
            tmp_path
        )


# =========================================================
# SCORE CONSOLIDADO
# =========================================================

@app.route(
    "/api/v2/score/consolidado",
    methods=["POST"]
)
def score_consolidado():

    try:

        dados = request.get_json()

        if not dados:

            return jsonify({
                "erro":
                    "JSON não informado."
            }), 400

        if "pet" not in dados:

            return jsonify({
                "erro":
                    "Objeto pet é obrigatório."
            }), 400

        if "historico" not in dados:

            return jsonify({
                "erro":
                    "Objeto historico é obrigatório."
            }), 400

        resultado = (
            health_score_service.calcular(
                pet=dados["pet"],

                historico=
                    dados["historico"],

                analise_visual=
                    dados.get(
                        "analise_visual"
                    )
            )
        )

        return jsonify(
            resultado
        ), 200

    except KeyError as e:

        return jsonify({
            "erro":
                "Campo obrigatório ausente.",

            "campo":
                str(e)
        }), 400

    except ValueError as e:

        return jsonify({
            "erro":
                "Valor inválido.",

            "detalhes":
                str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "erro":
                "Falha ao calcular Score Clyvo.",

            "detalhes":
                str(e)
        }), 500


# =========================================================
# FUNCOES AUXILIARES PARA UPLOAD
# =========================================================

def _validar_imagem_request():

    if "imagem" not in request.files:

        return None, (
            jsonify({
                "erro":
                    "Nenhuma imagem enviada."
            }),
            400
        )

    arquivo = request.files[
        "imagem"
    ]

    if not arquivo.filename:

        return None, (
            jsonify({
                "erro":
                    "Arquivo de imagem vazio."
            }),
            400
        )

    if (
        not arquivo.mimetype
        or not arquivo.mimetype.startswith(
            "image/"
        )
    ):

        return None, (
            jsonify({
                "erro":
                    "O arquivo enviado não é uma imagem."
            }),
            400
        )

    return arquivo, None


def _salvar_imagem_temporaria(
    arquivo
):

    extensao = os.path.splitext(
        arquivo.filename or ""
    )[1]

    if not extensao:
        extensao = ".jpg"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extensao
    ) as tmp:

        arquivo.save(
            tmp.name
        )

        return tmp.name


def _validar_tamanho_imagem(
    tmp_path
):

    tamanho = os.path.getsize(
        tmp_path
    )

    if tamanho > MAX_IMAGE_SIZE:

        return (
            jsonify({
                "erro":
                    "Imagem muito grande.",

                "limite_mb":
                    round(
                        MAX_IMAGE_SIZE
                        / 1024
                        / 1024,
                        1
                    )
            }),
            400
        )

    return None


def _remover_arquivo_temporario(
    tmp_path
):

    try:

        if (
            tmp_path
            and os.path.exists(
                tmp_path
            )
        ):

            os.remove(
                tmp_path
            )

    except Exception as e:

        print(
            "Erro ao remover arquivo temporário:",
            e
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    print(
        "================================="
    )

    print(
        "CLYVO AI API V2"
    )

    print(
        "http://localhost:5000"
    )

    print(
        "================================="
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )