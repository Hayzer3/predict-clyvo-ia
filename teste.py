import requests
import json
import os

BASE_URL = "http://localhost:5000"

print("=====================================================")
print(" INICIANDO TESTES DE INTEGRAÇÃO - CLYVO PREDICT")
print("=====================================================\n")


# TESTE 1: Rota de Histórico (Machine Learning Clássico)

print("➡️ TESTE 1: Enviando dados vitais e de IoT (JSON)...")
dados_pet = {
    "idade_anos": 12,
    "raca_predisposicao": 1,
    "dias_ultima_vacina": 400,
    "dias_ultimo_vermifugo": 120,
    "variacao_peso_iot": -1
}

resposta_historico = requests.post(f"{BASE_URL}/api/score/historico", json=dados_pet)

if resposta_historico.status_code == 200:
    print(" Sucesso na IA Tabular! Resposta do Servidor:")
    print(json.dumps(resposta_historico.json(), indent=4, ensure_ascii=False))
else:
    print(" Erro no Teste 1:", resposta_historico.text)


# TESTE 2: Rota de Visão Computacional 
print("\n TESTE 2: Enviando fotografia do Pet para análise visual...")
caminho_foto = "foto_pet.jpg" # Certifica-te de que a foto do pug está na pasta

if not os.path.exists(caminho_foto):
    print(f"  Erro: Não encontrei a imagem '{caminho_foto}' na pasta.")
else:
    with open(caminho_foto, 'rb') as f:
        # Enviando como multipart/form-data
        arquivos = {'imagem': f}
        resposta_visual = requests.post(f"{BASE_URL}/api/score/visual", files=arquivos)

    if resposta_visual.status_code == 200:
        print(" Sucesso na Visão Computacional! Diagnóstico da IA:")
        print(json.dumps(resposta_visual.json(), indent=4, ensure_ascii=False))
        print("\n A imagem de evidência (output_analise_ia.jpg) deve ter sido gerada na pasta do servidor!")
    else:
        print(" Erro no Teste 2:", resposta_visual.text)

print(" TESTES CONCLUÍDOS!")
