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


risk_service = RiskModelService()

gemini_service = GeminiService()

health_score_service = (
    HealthScoreService(
        risk_service=risk_service,
        gemini_service=gemini_service
    )
)


@app.route(
    "/api/v2/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "service": "clyvo-ai",
        "status": "online",
        "version": "2.0"
    }), 200


@app.route(
    "/api/v2/score/historico",
    methods=["POST"]
)
def score_historico():

    try:

        dados = request.get_json()

        if not dados:
            return jsonify({
                "erro": (
                    "JSON não informado."
                )
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


@app.route(
    "/api/v2/score/visual",
    methods=["POST"]
)
def score_visual():

    if "imagem" not in request.files:

        return jsonify({
            "erro":
                "Nenhuma imagem enviada."
        }), 400

    arquivo = request.files[
        "imagem"
    ]

    if (
        not arquivo.mimetype
        or not arquivo.mimetype.startswith(
            "image/"
        )
    ):

        return jsonify({
            "erro":
                "O arquivo informado "
                "não é uma imagem."
        }), 400

    tmp_path = None

    try:

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

            tmp_path = tmp.name

        tamanho = os.path.getsize(
            tmp_path
        )

        if tamanho > MAX_IMAGE_SIZE:

            return jsonify({
                "erro":
                    "Imagem muito grande.",

                "limite_mb":
                    5
            }), 400

        with open(
            tmp_path,
            "rb"
        ) as f:

            imagem_bytes = f.read()

        resultado = (
            gemini_service.analisar_imagem(
                imagem_bytes,
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

        if (
            tmp_path
            and os.path.exists(
                tmp_path
            )
        ):
            os.remove(
                tmp_path
            )


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
                historico=dados["historico"],
                analise_visual=dados.get(
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

    except Exception as e:

        return jsonify({
            "erro":
                "Falha ao calcular "
                "Score Clyvo.",

            "detalhes":
                str(e)
        }), 500


if __name__ == "__main__":

    print(
        "CLYVO AI API V2"
    )

    print(
        "http://localhost:5000"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )