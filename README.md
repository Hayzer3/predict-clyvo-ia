# CLYVO Predict API

## 🐾 Sobre o Projeto

O **CLYVO Predict API** é um microsserviço de Inteligência Artificial focado em medicina veterinária preventiva.

A API processa dados de telemetria (IoT), histórico clínico e imagens para gerar um **Score de Saúde dinâmico**, alertando tutores e clínicas sobre riscos iminentes.

Projeto desenvolvido para o **FIAP Challenge 2026**.

---

#  Arquitetura e Tecnologias

- Python 3
- Flask (Framework REST API)
- Scikit-Learn & Pandas (Machine Learning - Random Forest)
- LangChain & Google Generative AI (Gemini 3.5 Flash)
- OpenCV (Processamento e anotação de imagens)

---

#  Funcionalidades Principais

##  IA Tabular

Predição de risco clínico baseada em:

- Dados históricos
  - idade
  - vacinas
  - vermífugos
  - variação de peso
---

## Visão Computacional

Análise de imagens de pets usando Gemini 3.5 Flash para:

- Determinar condição corporal:
  - Abaixo do peso
  - Ideal
  - Sobrepeso
  - Obeso
- Inferir raça estimada

---

##  Engine de Regras de Negócio

Aplicação automática de penalidades no score baseada no diagnóstico visual, sem depender exclusivamente dos cálculos do LLM.

---

##  Alertas de Comunicação

Estruturação de respostas preparadas para:

- WhatsApp
- Sistemas de mensageria
- Futuras integrações RAG (Retrieval-Augmented Generation)

---

##  Evidência Visual Dinâmica

O sistema:

- Processa a imagem original
- Sobrepõe o diagnóstico em tempo real usando OpenCV
- Calcula dinamicamente a largura do quadro
- Evita cortes no texto da evidência clínica

---

# Configuração e Execução do Ambiente

## Clone o repositório

```bash
git clone <url-do-repositorio>
cd clyvo-predict-api
```

---

## Crie e ative um ambiente virtual

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / Mac

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Instale as dependências

```bash
pip install flask pandas numpy scikit-learn langchain-google-genai langchain-core opencv-python python-dotenv
```

---

## Configure as variáveis de ambiente

Crie um arquivo chamado `.env` na raiz do projeto:

```env
GOOGLE_API_KEY=sua_chave_de_api_aqui
```

---

## Execute a aplicação

```bash
python app.py
```

Servidor iniciado em:

```txt
http://localhost:5000
```

---

# Documentação dos Endpoints

# Predição Tabular (Histórico + IoT)

## Endpoint

```http
POST /api/score/historico
```

## Content-Type

```txt
application/json
```

## Payload

```json
{
  "idade_anos": 12,
  "raca_predisposicao": 1,
  "dias_ultima_vacina": 400,
  "dias_ultimo_vermifugo": 120,
  "variacao_peso_iot": -1
}
```

---

## Resposta Esperada (200 OK)

```json
{
  "pet_risco_id": 2,
  "score_saude": 30,
  "status_saude": "Critico",
  "cor_indicador": "Vermelho",
  "disparar_whatsapp": true
}
```

---

# Predição Visual (IA Generativa)

## Endpoint

```http
POST /api/score/visual
```

## Content-Type

```txt
multipart/form-data
```

---

## Payload

| Campo | Tipo | Descrição |
|---|---|---|
| imagem | File | Arquivo de imagem do pet (.jpg, .jpeg, .png) |

### Limite máximo

```txt
5MB
```

---

## Resposta Esperada (200 OK)

```json
{
  "especie": "Cao",
  "raca_estimada": "Pug",
  "condicao_corporal": "Sobrepeso",
  "alerta_whatsapp": "Ola! Notamos pelo nosso sistema visual que o pet encontra-se com sobrepeso. Recomendamos agendar uma avaliacao nutricional.",
  "pontos_de_risco": 10
}
```

---

# Evidência Gerada

Após o processamento bem-sucedido da rota visual, o sistema cria automaticamente o arquivo:

```txt
output_analise_ia.jpg
```

O arquivo contém:

- Diagnóstico visual
- Informações clínicas
- Evidência anotada pela IA

---

#  Estrutura Esperada do Projeto

```bash
clyvo-predict-api/
│
├── app.py
├── .env
├── requirements.txt
├── output_analise_ia.jpg
│
├── models/
├── routes/
├── services/
├── utils/
│
└── README.md
```

---

#  Objetivo do Projeto

O objetivo do CLYVO Predict é transformar a medicina veterinária reativa em um modelo preventivo, utilizando:

- Inteligência Artificial
- IoT
- Visão Computacional
- Automação de alertas clínicos

para aumentar a qualidade de vida dos pets e reduzir riscos clínicos antecipadamente.

---

# Desenvolvido para

**FIAP Challenge 2026** 
