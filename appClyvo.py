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
    raise EnvironmentError("Chave GOOGLE_API_KEY não encontrada no arquivo .env!")

app = Flask(__name__)

# Inicializa o Gemini (Corrigido para a versão correta da Google)
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.1, api_key=google_api_key)
except Exception as e:
    print("Erro ao inicializar LLM:", e)
    llm = None

# ==========================================
# TREINAMENTO DO MODELO RANDOM FOREST (TABULAR)
# ==========================================

print("⚙️ Treinando IA Tabular (Random Forest)...")
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
print("✅ IA Tabular Pronta!")
 
# ==========================================
# ROTA 1: PREVISÃO VIA DADOS (Para o App/Java)
# ==========================================

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
            0: {"status": "Saudável", "score": 95, "cor": "Verde", "alerta": False},
            1: {"status": "Atenção", "score": 65, "cor": "Amarelo", "alerta": True},
            2: {"status": "Crítico", "score": 30, "cor": "Vermelho", "alerta": True}
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

# ==========================================
# ROTA 2: PREVISÃO VISUAL VIA GEMINI (Upload de Foto)
# ==========================================

@app.route('/api/score/visual', methods=['POST'])
def score_visual():
    if 'imagem' not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada na requisição."}), 400

    arquivo = request.files['imagem']

    if not arquivo.mimetype or not arquivo.mimetype.startswith('image/'):
        return jsonify({"erro": "Arquivo enviado não é uma imagem."}), 400

    print("📸 Imagem recebida pelo React Native. Analisando...")

    tmp_file = None
    caminho_output = None
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
        Você é um sistema especialista em triagem veterinária. 
        Analise a foto deste pet e retorne ESTRITAMENTE um JSON válido com a seguinte estrutura:
        {
            "especie": "Cão ou Gato",
            "raca_estimada": "Nome da raça",
            "condicao_corporal": "Abaixo do peso / Ideal / Sobrepeso",
            "alerta_risco_visual": "Texto curto com possíveis riscos",
            "pontos_de_risco": um número inteiro de 0 a 3
        }
        Não escreva nenhuma palavra fora do formato JSON.
        """

        if llm is None:
            return jsonify({"erro": "LLM não inicializado."}), 500

        mensagem = HumanMessage(
            content=[
                {"type": "text", "text": prompt_veterinario},
                {"type": "image_url", "image_url": {"url": image_data_uri}}
            ]
        )

        try:
            resposta = llm.invoke([mensagem])
        except ClientError as ce:
            return jsonify({"erro": "Erro do provedor de IA", "detalhes": str(ce)}), 502

        raw_content = resposta.content
        
        if isinstance(raw_content, list):
            s = " ".join(str(item) for item in raw_content)
        elif isinstance(raw_content, dict):
            s = str(raw_content.get("text", raw_content))
        else:
            s = str(raw_content)

        s = s.replace("```json", "").replace("```", "").strip()
        
        m = re.search(r'\{\s*"', s)
        if m:
            start = m.start()
            end = s.rfind('}')
            texto_json = s[start:end+1] if end != -1 and end > start else s[start:]
        else:
            texto_json = s

        try:
            diagnostico = json.loads(texto_json)
        except Exception:
            try:
                diagnostico = ast.literal_eval(texto_json)
            except Exception as exc:
                raise ValueError(f"Não foi possível parsear JSON retornado pela IA: {exc}")

        img = cv2.imread(tmp_file)
        if img is not None:
            texto_tela = f"Raca: {diagnostico.get('raca_estimada')} | Condicao: {diagnostico.get('condicao_corporal')}"
            risco_tela = f"Score Penalizado: +{diagnostico.get('pontos_de_risco')} pt(s)"
            h, w = img.shape[:2]
            rect_w = min(800, w - 20)
            cv2.rectangle(img, (10, 10), (10 + rect_w, 120), (0, 0, 0), -1)
            cv2.putText(img, texto_tela, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (17, 202, 160), 2)
            cv2.putText(img, risco_tela, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 50, 50), 2)
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
    print("\n🚀 API CLYVO PREDICT ONLINE (Porta 5000)")
    print("Rotas disponíveis:")
    print(" -> POST /api/score/historico (JSON)")
    print(" -> POST /api/score/visual (Form-Data com arquivo 'imagem')")
    app.run(host='0.0.0.0', port=5000, debug=True)