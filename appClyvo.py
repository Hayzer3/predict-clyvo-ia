import os
import cv2
import json
import base64
import re
import ast
import tempfile
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.genai.errors import ClientError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from sklearn.ensemble import RandomForestClassifier

load_dotenv(override=True)
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise EnvironmentError("Chave GOOGLE_API_KEY nao encontrada no arquivo .env!")

app = Flask(__name__)

try:
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1, api_key=google_api_key)
except Exception as e:
    print("Erro ao inicializar LLM:", e)
    llm = None

print("Treinando IA Tabular...")
np.random.seed(42)
n_samples = 1000

df = pd.DataFrame({
    'idade_anos': np.random.randint(1, 16, size=n_samples),
    'raca_predisposicao': np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3]),
    'dias_ultima_vacina': np.random.randint(0, 500, size=n_samples),
    'dias_ultimo_vermifugo': np.random.randint(0, 200, size=n_samples),
    'variacao_peso_iot': np.random.choice([-1, 0, 1], size=n_samples, p=[0.15, 0.70, 0.15])
})

def definir_risco_real(row):
    score = 0
    if row['dias_ultima_vacina'] > 365: score += 3
    if row['dias_ultimo_vermifugo'] > 90: score += 2
    if row['variacao_peso_iot'] == -1: score += 3
    if row['raca_predisposicao'] == 1: score += 1
    if row['idade_anos'] > 10: score += 1
    
    if score <= 2: return 0
    elif score <= 5: return 1
    else: return 2

df['nivel_risco'] = df.apply(definir_risco_real, axis=1)

X = df[['idade_anos', 'raca_predisposicao', 'dias_ultima_vacina', 'dias_ultimo_vermifugo', 'variacao_peso_iot']]
y = df['nivel_risco']

modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42)
modelo_rf.fit(X, y)
print("IA Tabular Pronta!")

@app.route('/prever_risco', methods=['POST'])
@app.route('/api/score/historico', methods=['POST'])
def score_historico():
    try:
        dados_input = request.json
        df_input = pd.DataFrame([{
            'idade_anos': int(dados_input['idade_anos']),
            'raca_predisposicao': int(dados_input['raca_predisposicao']),
            'dias_ultima_vacina': int(dados_input['dias_ultima_vacina']),
            'dias_ultimo_vermifugo': int(dados_input['dias_ultimo_vermifugo']),
            'variacao_peso_iot': int(dados_input['variacao_peso_iot'])
        }])
        
        predicao = modelo_rf.predict(df_input)[0]
        
        mapa_score = {
            0: {"status": "Saudavel", "score": 95, "cor": "Verde", "alerta": False},
            1: {"status": "Atencao", "score": 65, "cor": "Amarelo", "alerta": True},
            2: {"status": "Critico", "score": 30, "cor": "Vermelho", "alerta": True}
        }
        res = mapa_score[predicao]
            
        return jsonify({
            "pet_risco_id": int(predicao),
            "score_saude": res['score'],
            "status_saude": res['status'],
            "cor_indicador": res['cor'],
            "disparar_whatsapp": res['alerta']
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/score/visual', methods=['POST'])
def score_visual():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    arquivo = request.files['imagem']

    if not arquivo.mimetype or not arquivo.mimetype.startswith('image/'):
        return jsonify({"erro": "Arquivo enviado nao e uma imagem."}), 400

    print("Imagem recebida. Analisando...")

    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            arquivo.save(tmp.name)
            tmp_file = tmp.name

        tamanho = os.path.getsize(tmp_file)
        if tamanho > 5 * 1024 * 1024:
            os.remove(tmp_file)
            return jsonify({"erro": "Imagem muito grande (max 5MB)."}), 400

        with open(tmp_file, "rb") as f:
            imagem_bytes = f.read()

        mime_type = "image/jpeg"
        image_data_uri = f"data:{mime_type};base64,{base64.b64encode(imagem_bytes).decode('ascii')}"

        prompt_veterinario = """
        Voce e um sistema especialista em triagem veterinaria. 
        Analise a foto deste pet e retorne ESTRITAMENTE um JSON valido com a seguinte estrutura:
        {
            "especie": "Cao ou Gato",
            "raca_estimada": "Nome da raca",
            "condicao_corporal": "Abaixo do peso / Ideal / Sobrepeso / Obeso",
            "alerta_risco_visual": "Texto curto com possiveis riscos"
        }
        Nao escreva nenhuma palavra fora do formato JSON.
        """

        if llm is None:
            return jsonify({"erro": "LLM nao inicializado."}), 500

        mensagem = HumanMessage(
            content=[
                {"type": "text", "text": prompt_veterinario},
                {"type": "image_url", "image_url": {"url": image_data_uri}}
            ]
        )

        resposta = llm.invoke([mensagem])
        raw_content = resposta.content
        texto_json = str(raw_content).replace("```json", "").replace("```", "").strip()

        start = texto_json.find('{')
        end = texto_json.rfind('}')
        if start != -1 and end != -1:
            texto_json = texto_json[start:end+1]

        diagnostico = {}
        
        try:
            parsed_data = ast.literal_eval(texto_json) if "'" in texto_json else json.loads(texto_json)
            
            if isinstance(parsed_data, dict) and "text" in parsed_data:
                inner_text = str(parsed_data["text"]).replace("```json", "").replace("```", "").strip()
                start_in = inner_text.find('{')
                end_in = inner_text.rfind('}')
                if start_in != -1 and end_in != -1:
                    diagnostico = json.loads(inner_text[start_in:end_in+1])
                else:
                    diagnostico = json.loads(inner_text)
            else:
                diagnostico = parsed_data

        except Exception as e:
            raise ValueError(f"Falha ao extrair JSON: {str(e)}")

        condicao = diagnostico.get('condicao_corporal', 'Ideal')
        
        tabela_penalidade = {
            "Obeso": 20,
            "Sobrepeso": 10,
            "Abaixo do peso": 15,
            "Ideal": 0
        }
        
        pontos_penalidade = tabela_penalidade.get(condicao, 0)
        diagnostico['pontos_de_risco'] = pontos_penalidade

        img = cv2.imread(tmp_file)
        if img is not None:
            raca = diagnostico.get('raca_estimada', 'Desconhecida')
            
            texto_tela = f"Raca: {raca} | Condicao: {condicao}"
            risco_tela = f"Score Penalizado Visivelmente: -{pontos_penalidade} pt(s)"
            
            h, w = img.shape[:2]

            # Configuracao do texto para calculo de tamanho
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            thickness = 2

            # Calcula largura do texto para ajustar o retangulo
            (t1_w, t1_h), _ = cv2.getTextSize(texto_tela, font, font_scale, thickness)
            (t2_w, t2_h), _ = cv2.getTextSize(risco_tela, font, font_scale, thickness)
            
            # Margem interna e largura total dinamica
            padding_w = 20
            max_text_width = max(t1_w, t2_w)
            final_rect_width = max_text_width + (padding_w * 2)

            # Garante que o retangulo nao estoure a largura da imagem
            rect_right = min(10 + final_rect_width, w - 10)

            # Desenha o retangulo preto dinamico
            cv2.rectangle(img, (10, 10), (rect_right, 120), (0, 0, 0), -1)

            # Desenha os textos
            cv2.putText(img, texto_tela, (20, 50), font, font_scale, (17, 202, 160), thickness)
            cv2.putText(img, risco_tela, (20, 100), font, font_scale, (255, 50, 50), thickness)
            
            caminho_output = "output_analise_ia.jpg"
            cv2.imwrite(caminho_output, img)

        return jsonify(diagnostico), 200

    except Exception as e:
        return jsonify({"erro": "Falha na IA Visual", "detalhes": str(e)}), 500
    finally:
        try:
            if tmp_file and os.path.exists(tmp_file):
                os.remove(tmp_file)
        except Exception:
            pass

if __name__ == '__main__':
    print("API CLYVO PREDICT ONLINE (Porta 5000)")
    app.run(host='0.0.0.0', port=5000, debug=True)