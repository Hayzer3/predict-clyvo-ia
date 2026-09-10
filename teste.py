"""Demonstração da API v2 em execução. Não exige requests nem imprime credenciais."""
import argparse
import json
import mimetypes
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def enviar(base_url, rota, payload=None, imagem=None):
    headers = {}
    data = None
    if imagem is not None:
        tipo = mimetypes.guess_type(imagem.name)[0]
        if tipo not in {"image/jpeg", "image/png"}:
            raise ValueError("Selecione uma foto JPEG ou PNG.")
        if not 0 < imagem.stat().st_size <= 5 * 1024 * 1024:
            raise ValueError("A imagem deve ter conteúdo e no máximo 5 MB.")
        boundary = "clyvo-" + uuid.uuid4().hex
        data = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="imagem"; filename="pet{imagem.suffix}"\r\n'
            f"Content-Type: {tipo}\r\n\r\n"
        ).encode() + imagem.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = Request(base_url.rstrip("/") + rota, data=data, headers=headers)
    with urlopen(req, timeout=60) as response:
        result = json.load(response)
        print(f"\n{req.get_method()} {rota}: HTTP {response.status}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--imagem", type=Path, help="Foto opcional para análise de cadastro")
    args = parser.parse_args()
    historico = {
        "idade_anos": 3, "raca_predisposicao": 0,
        "dias_ultima_vacina": 100, "dias_ultimo_vermifugo": 30,
        "variacao_peso_iot": 0,
    }
    try:
        enviar(args.base_url, "/api/v2/health")
        enviar(args.base_url, "/api/v2/score/historico", historico)
        enviar(args.base_url, "/api/v2/score/consolidado",
               {"pet": {"id": 1, "nome": "Mel"}, "historico": historico})
        if args.imagem:
            enviar(args.base_url, "/api/v2/pets/analyze-registration-photo",
                   imagem=args.imagem)
        print("\nDemonstração concluída sem erros HTTP.")
        return 0
    except HTTPError as exc:
        print(f"Falha HTTP {exc.code}. Confira o log da API.", file=sys.stderr)
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"Falha na demonstração: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
