# Clyvo AI — acompanhamento preventivo de pets

Protótipo acadêmico desenvolvido para o FIAP Challenge 2026. A API combina histórico informado, um modelo tabular e análise de fotografias para apoiar o acompanhamento de cães e gatos.

Repositório: https://github.com/Hayzer3/predict-clyvo-ia

## Integrantes

| Integrante | RM |
|---|---|
| Camily Vitoria Pereira Maciel | RM566520 |
| Eduarda Weiss Ventura | RM564434 |
| Lucas Nunes Soares | RM566503 |
| Maria Gabriela Landim Severo | RM565146 |
| Samara Porto Souza | RM559072 |

## Ideia central

Reunir indicadores do pet em um score de acompanhamento e destacar fatores que merecem atenção. A fotografia também auxilia o cadastro, sugerindo espécie, raça, cor, porte e uma faixa de peso que o tutor precisa confirmar.

O projeto está em fase de protótipo. O modelo usa dados sintéticos e regras acadêmicas; os resultados não representam diagnóstico ou probabilidades clínicas validadas.

## Recursos implementados

- Health check da API.
- Predição tabular com score base, classe, probabilidades do modelo e fatores de risco.
- Análise visual de condição corporal com penalidade definida por regras.
- Sugestão de dados para cadastro a partir de uma foto.
- Score consolidado com histórico e análise visual opcional.
- Resposta estruturada de alerta, com prioridade e mensagem sugerida.

O campo de variação de peso é recebido por JSON: não existe conexão com um sensor físico neste repositório. A API prepara uma mensagem de alerta, mas não envia WhatsApp. Não há geração de imagem anotada, interface web ou persistência de dados nesta versão.

## Tecnologias e arquitetura

| Tecnologia | Uso |
|---|---|
| Python e Flask | API HTTP |
| NumPy e pandas | Construção e manipulação dos dados sintéticos |
| scikit-learn | RandomForestClassifier |
| LangChain e integração Google GenAI | Chamadas ao Gemini para análise de fotos e recomendações |
| python-dotenv | Configuração local por variáveis de ambiente |

Fluxo: cliente/Postman → Flask → modelo tabular e/ou Gemini → regras de score → JSON.
O backend Java pode consumir este serviço na porta 5000; a API de IA pode ser demonstrada diretamente pelo Postman.

## Execução local

1. Clone o repositório:

```bash
git clone https://github.com/Hayzer3/predict-clyvo-ia.git
cd predict-clyvo-ia
python -m venv .venv
```

2. Ative o ambiente:

Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source .venv/bin/activate
```

3. Instale as dependências e configure o ambiente:

```bash
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha `GOOGLE_API_KEY`. Ajuste `GEMINI_MODEL` para um modelo disponível na sua conta; o exemplo acompanha a configuração atual do projeto. Não publique o arquivo `.env`.

4. Inicie:

```bash
python app.py
```

Endereço: `http://localhost:5000`. O Random Forest é treinado na inicialização. O servidor atual usa o modo de desenvolvimento do Flask.

Sem chave do Gemini, o histórico tabular funciona e a recomendação consolidada pode usar texto de fallback. As rotas que analisam fotos dependem da chave, acesso à internet e disponibilidade do provedor. Health check online não comprova que o Gemini está disponível.

## Endpoints da versão 2

| Método | Rota | Entrada |
|---|---|---|
| GET | /api/v2/health | Sem corpo |
| POST | /api/v2/score/historico | JSON com os cinco indicadores |
| POST | /api/v2/score/visual | multipart/form-data, campo imagem |
| POST | /api/v2/pets/analyze-registration-photo | multipart/form-data, campo imagem |
| POST | /api/v2/score/consolidado | JSON com pet, historico e analise_visual opcional |

### Histórico

```json
{
  "idade_anos": 12,
  "raca_predisposicao": 1,
  "dias_ultima_vacina": 400,
  "dias_ultimo_vermifugo": 120,
  "variacao_peso_iot": -1
}
```

Use idade e dias não negativos, predisposição 0 ou 1 e variação de peso -1 (redução), 0 (estável) ou 1 (aumento). A resposta contém `score_base`, `nivel_risco_predito`, `classificacao_modelo`, `probabilidades` e `fatores_risco`.

### Foto no Postman

Use POST na rota desejada, Body → form-data, chave `imagem`, tipo File. Selecione uma foto JPEG ou PNG de até **5 MB**, limite da API Python. Deixe o Postman definir o Content-Type com o boundary. A API Python não implementa autenticação; o Bearer Token é usado quando a chamada passa pelo backend Java.

A rota de cadastro retorna `origem`, `requer_confirmacao`, `analise_cadastro` e `aviso`. A análise inclui espécie, raça estimada, cor, porte, faixa de peso, condição corporal, características e confiança. Os valores podem variar entre chamadas.

### Score consolidado

```json
{
  "pet": {"id": 1, "nome": "Mel"},
  "historico": {
    "idade_anos": 12,
    "raca_predisposicao": 1,
    "dias_ultima_vacina": 400,
    "dias_ultimo_vermifugo": 120,
    "variacao_peso_iot": -1
  },
  "analise_visual": {
    "condicao_corporal": "Sobrepeso",
    "pontos_risco_visual": 8
  }
}
```

O objeto `analise_visual` acima é um exemplo simulado. Em um fluxo real, utilize o resultado da rota de análise visual. A resposta consolidada inclui score, status, prioridade, fatores, recomendação, alerta, data de processamento e identificação do modelo como protótipo acadêmico.

## Como o score é calculado

O Random Forest usa 150 árvores, profundidade máxima 8 e semente 42. É treinado na inicialização com 3.000 registros sintéticos rotulados por regras de idade, vacinação, vermifugação, predisposição e variação de peso.

- Score base: `round(100 - 35 × (P(atenção) + 2 × P(crítico)))`.
- Score final: score base menos penalidade visual, limitado entre 0 e 100.
- Penalidades visuais atuais: ideal 0; sobrepeso 8; obeso 15; abaixo do peso 12; indeterminado 0.
- A consolidação limita a penalidade recebida ao intervalo 0–20.
- Status final: SAUDAVEL a partir de 80; ATENCAO de 60 a 79; CRITICO abaixo de 60.

Esses parâmetros descrevem a implementação acadêmica; não são limiares clínicos validados.

## Demonstração e resultados parciais

Na sessão de integração de **07/09/2026**, a rota de cadastro por foto respondeu HTTP 200 com a foto de exemplo em cerca de 7 segundos. O mesmo envio pelo cliente Java retornou com sucesso em aproximadamente 6,6 segundos. São medições pontuais, não um benchmark.

Também houve uma tentativa pelo Postman que excedeu o tempo de espera do backend Java e retornou 504. Portanto, a disponibilidade e a latência da análise externa ainda precisam ser acompanhadas.

Não foram calculadas métricas de acurácia, precisão ou recall em uma base real ou conjunto independente de validação. O treinamento com dados sintéticos demonstra o fluxo técnico, não eficácia clínica.

### Reproduzir a demonstração

Com a API iniciada:
```bash
python teste.py
python teste.py --imagem foto_pet.jpg
```

O primeiro comando verifica health check, histórico e score consolidado com um cenário estável. O segundo adiciona a análise de cadastro da foto e depende do Gemini. O script usa apenas a biblioteca padrão do Python, limita o tempo de espera e termina com erro se uma requisição falhar.

Para Postman, importe `docs/Clyvo-AI.postman_collection.json`; ajuste a variável `base_url` e selecione o arquivo local nas duas requisições de foto.

## Estrutura

```text
predict-clyvo-ia/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── teste.py
├── foto_pet.jpg
├── cachorro_pet.jpeg
├── docs/
│   └── Clyvo-AI.postman_collection.json
└── services/
    ├── gemini_service.py
    ├── health_score_service.py
    └── risk_model_service.py
```

As fotos existentes foram preservadas como entradas de demonstração. Arquivos locais de saída, caches e credenciais não fazem parte dos entregáveis.

## Próximos passos

Validar com dados adequados e revisão veterinária, medir desempenho em conjunto separado, melhorar tratamento de falhas do provedor de IA e evoluir autenticação e integração com os demais componentes.
