# 🐾 CLYVO Predict - API de Inteligência Artificial

O **CLYVO Predict** é uma plataforma SaaS de gestão veterinária preventiva. Este repositório contém o microsserviço de Inteligência Artificial desenvolvido em Python, responsável por calcular o **Score de Saúde** dos animais de estimação através de Machine Learning clássico e Visão Computacional (IA Generativa).

Projeto desenvolvido para o **FIAP Challenge 2026 (1º Sprint)**.

---

# 👥 Equipa (Turma 2TDSPX)

- Camily Vitoria Pereira Maciel (RM: 566520)
- Eduarda Weiss Ventura (RM: 564434)
- Lucas Nunes Soares (RM: 566503)
- Maria Gabriela Landim Severo (RM: 565146)
- Samara Porto Souza (RM: 559072)

---

#  Arquitetura e Funcionalidades

A API foi construída utilizando o **Flask** e expõe dois endpoints principais para integração com o frontend (**React Native**) e o backend central (**Java Spring Boot**):

## IA Tabular (Random Forest)

Analisa dados históricos do Oracle DB:

- Idade do animal
- Vacinas atrasadas
- Vermífugos
- Dados telemétricos IoT
- Variação de peso

Com isso, a IA classifica automaticamente o nível de risco clínico.

---

## Visão Computacional (Gemini + LangChain)

Recebe o upload de uma fotografia do animal e utiliza IA Generativa para:

- Identificar a raça
- Detectar condição corporal
- Reconhecer predisposições de risco

Exemplos:

- Sobrepeso
- Braquicefalia
- Magreza extrema

A resposta devolve um JSON estruturado com os pontos de penalização.

---

## 3 Evidência Visual (OpenCV)

A API desenha automaticamente:

- Bounding boxes
- Textos de diagnóstico
- Alertas clínicos

Tudo diretamente na imagem original, gerando um artefato visual salvo no servidor.

---

# 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **Flask** (Framework Web / API REST)
- **Scikit-Learn**
- **Pandas**
- **NumPy**
- **LangChain**
- **Google Generative AI**
- **Gemini 3.5 Flash**
- **OpenCV**
- **Python-dotenv**

---

#  Como Instalar e Executar Localmente

## Clonar o Repositório

```bash
git clone https://github.com/SeuUsuario/clyvo-predict-ia.git
cd clyvo-predict-ia

## Criar e Ativar Ambiente Virtual (Opcional)

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

## Instalar Dependências

```bash
pip install flask pandas numpy scikit-learn langchain-google-genai langchain-core opencv-python python-dotenv
```

---

##  Configurar Variáveis de Ambiente

Crie um ficheiro `.env` na raiz do projeto:

```env
GOOGLE_API_KEY="COLA_A_TUA_CHAVE_AQUI"
```

---

## Iniciar o Servidor

```bash
python app.py
```

A API ficará disponível em:

```txt
http://localhost:5000
```

---

#  Documentação dos Endpoints

## Histórico e IoT Tabular

### Rota

```http
POST /api/score/historico
```

### Content-Type

```txt
application/json
```

### Exemplo de Request

```json
{
  "idade_anos": 12,
  "raca_predisposicao": 1,
  "dias_ultima_vacina": 400,
  "dias_ultimo_vermifugo": 120,
  "variacao_peso_iot": -1
}
```

### Resposta (200 OK)

```json
{
  "codigo_risco": 2,
  "score_saude": 30,
  "status_saude": "Crítico",
  "disparar_whatsapp": true
}
```

---

## Análise Visual (IA Generativa)

### Rota

```http
POST /api/score/visual
```

### Content-Type

```txt
multipart/form-data
```

### Exemplo de Request

| Key    | Tipo | Valor   |
|--------|------|----------|
| imagem | File | pug.jpg  |

---

### Resposta (200 OK)

```json
{
  "especie": "Cão",
  "raca_estimada": "Pug",
  "condicao_corporal": "Sobrepeso",
  "alerta_risco_visual": "Animal apresenta braquicefalia extrema associada a sobrepeso...",
  "pontos_de_risco": 3
}
```

> O servidor também guardará automaticamente um ficheiro:
>
> ```txt
> output_analise_ia.jpg
> ```
>
> contendo o diagnóstico renderizado sobre a imagem original.

---

# 📂 Estrutura 

```txt
clyvo-predict-ia/
│
├── app.py
├── .env
├── requirements.txt
└── README.md
```

---

# 🧠 Objetivo do Projeto

O objetivo do **CLYVO Predict** é utilizar Inteligência Artificial para transformar a medicina veterinária preventiva através de:

- Análise preditiva
- Monitoramento inteligente
- Telemetria IoT
- Visão Computacional
- Alertas automatizados

Permitindo intervenções mais rápidas e melhor qualidade de vida para os animais.

---

# 📜 Licença

Projeto académico desenvolvido para o **FIAP Challenge 2026**.