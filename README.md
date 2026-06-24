# Empresas Habilitadas na Lei de Informática — Prospecção de Parcerias de P&D

Mapeamento das empresas habilitadas na **Lei de Informática** (Lei nº 8.248/1991 e Lei nº 13.969/2019), cadastradas no portal do **MCTI**, com foco em identificar **oportunidades de parceria em projetos de Pesquisa & Desenvolvimento (P&D)** para um **Instituto de Física** (UFRGS / CEENF).

Cada empresa é classificada quanto à sua aderência aos temas de pesquisa de física experimental e aplicada — instrumentação científica, eletrônica, sensores, fotônica e óptica, materiais, detectores, vácuo e criogenia, metrologia, automação de laboratório, computação científica e áreas correlatas.

O resultado é uma **página web interativa** que permite buscar, filtrar, ordenar e ranquear as empresas pelo seu potencial de parceria.

---

## Como o projeto foi feito

O projeto tem duas partes: um **pipeline de coleta e enriquecimento** dos dados (que gera o `empresas.json`) e uma **aplicação web** (`app.py`) que apresenta o resultado.

### 1. Coleta dos dados oficiais (MCTI)

O ponto de partida é o cadastro de empresas habilitadas exportado do portal do MCTI (`MCTIC.pdf` / `MCTICinfos.pdf`). Esse PDF é processado para extrair, de forma estruturada, os dados **autoritativos** de cada empresa:

- Razão social e nome fantasia
- CNPJ
- Endereço, município e UF
- Pessoa/área de contato, e-mail, telefone e site

Esses campos vêm direto da fonte oficial e têm prioridade sobre qualquer outra etapa. Foram extraídas **~500 empresas** a partir do cadastro.

### 2. Enriquecimento com IA (Claude)

Para cada empresa, o perfil é completado e analisado usando os modelos **Claude (Anthropic)**. A estratégia foi pensada para ser **barata e robusta**:

- **Quando a empresa tem site:** o conteúdo do site institucional (página inicial + algumas páginas internas como "sobre", "produtos" e "soluções") é coletado e enviado ao modelo, que apenas **estrutura** as informações — sem custo de busca na web.
- **Quando não há site:** usa-se busca na web (web search) ou o conhecimento próprio do modelo como alternativa.

A partir desse material, o modelo preenche um **perfil padronizado** de cada empresa (segmento, nicho, produtos, tecnologias, áreas de P&D etc.) e produz a análise central do projeto:

- **Oportunidades de Projetos de P&D** — temas de parceria mais promissores com um instituto de física, em 1–2 frases.
- **Potencial de Parceria (P&D)** — classificação **Alto / Médio / Baixo** conforme a aderência da empresa aos temas de pesquisa em física, com uma justificativa curta.

O pipeline foi construído com várias salvaguardas de produção:

- **Gravação atômica** do JSON (escreve em arquivo temporário e renomeia), evitando corromper os dados se o processo for interrompido.
- **Retentativas com _backoff_** em caso de _rate limit_ (429) ou erros de servidor (5xx).
- **Reprocessamento seletivo** apenas das empresas que ficaram sem enriquecimento.
- **Variante via Batch API**, que processa todas as análises em lote por cerca de metade do custo de tokens.

### 3. Saída: `empresas.json`

O resultado consolidado é exportado para o arquivo **`empresas.json`** — uma lista de empresas, cada uma com os campos padronizados. É esse arquivo que alimenta a página web.

### 4. Aplicação web (`app.py`)

Um servidor **Flask** simples serve uma página única (sem dependências de front-end externas). A página oferece:

- **KPIs** — total de empresas, distribuição por potencial de P&D, empresas com site.
- **Gráficos** — potencial de parceria, setores de atuação e principais nichos.
- **Lista ranqueada** por potencial de P&D, com filtros por setor e potencial, busca textual e ordenação.
- **Detalhamento** por empresa (produtos, tecnologias, áreas de P&D, contato, oportunidades etc.).
- **Atualização em tempo real** — o servidor relê o `empresas.json` a cada requisição e a página faz _polling_, refletindo o processamento conforme novas empresas são analisadas.

---

## Como executar

Pré-requisitos: **Python 3.10+**.

```bash
# 1. Instalar as dependências
pip install -r requirements.txt

# 2. Subir o servidor
python app.py
# Acesse: http://127.0.0.1:5050

# 3. (Opcional) Expor publicamente, em outro terminal
ngrok http 5050
```

O caminho do JSON pode ser customizado pela variável de ambiente `EMPRESAS_JSON` (padrão: `empresas.json`).

---

## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `app.py` | Servidor Flask + página web interativa. |
| `empresas.json` | Base de dados final das empresas enriquecidas. |
| `requirements.txt` | Dependências do projeto. |
| `MCTIC.pdf` / `MCTICinfos.pdf` | Cadastro oficial das empresas habilitadas (fonte dos dados). |
| `UFRGS.png`, `IF-UFRGS_-logo.png`, `images.jpg` | Logos exibidas no cabeçalho da página. |

---

## Campos do `empresas.json`

Cada empresa contém, entre outros, os seguintes campos:

| Campo | Conteúdo |
|---|---|
| `nome_da_empresa`, `razao_social`, `cnpj_da_empresa` | Identificação. |
| `municipio`, `uf`, `endereco` | Localização. |
| `principal_site`, `email_contato`, `telefone_contato`, `pessoa_contato`, `pagina_contato`, `redes_sociais_principais` | Contato. |
| `segmento`, `setores_chave`, `nicho_de_atuacao`, `macro_categoria`, `modelo_de_negocio` | Classificação de atuação. |
| `principais_produtos_e_servicos`, `tecnologias_utilizadas`, `publico_alvo`, `diferenciais_da_empresa` | Perfil técnico/comercial. |
| `status_habilitacao_lei_informatica` | Situação na Lei de Informática. |
| `areas_de_pd`, `linhas_de_pesquisa_e_inovacao` | Atuação em P&D. |
| **`oportunidades_de_projetos_pd`** | Temas de parceria de P&D com o instituto de física. |
| **`potencial_de_parceria_pd`** | Classificação Alto / Médio / Baixo + justificativa. |

---

## Observações

- Os dados de identidade e contato vêm do cadastro oficial do MCTI; os campos analíticos são gerados por IA a partir do conteúdo público das empresas e devem ser tratados como **apoio à prospecção**, não como informação verificada caso a caso.
- O enriquecimento por IA requer uma chave da Anthropic (`ANTHROPIC_API_KEY`) e foi executado em um notebook de processamento, não incluído neste repositório.
