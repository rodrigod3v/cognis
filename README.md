# Cognis — Gerador de Arquitetura de Testes

**Cognis** é uma CLI em Python puro (zero dependencias externas) que analisa descricoes em linguagem natural de funcionalidades e gera automaticamente a **arquitetura completa de testes** baseada no modelo da **Piramide de Testes**.

Em vez de gastar horas pensando "o que testar?", voce descreve a funcionalidade e as regras de negocio, e o Cognis entrega:

- Um **relatorio markdown** com features, regras, inputs/outputs, dependencias, fluxos
- A **piramide de testes completa**: Unit → Integration → E2E
- **Casos de teste detalhados** (Happy Path + Violation + Boundary + Error)
- Uma **estrutura de pastas** com stubs prontos para implementar
- **READMES contextuais** com informacoes da branch e commit atual
- **Checklist de implementacao** e sugestao de frameworks

---

## Indice

- [Como funciona](#como-funciona)
- [Instalacao](#instalacao)
- [Uso](#uso)
- [Configuracao](#configuracao)
- [Exemplo](#exemplo)
- [Saidas](#saidas)
- [Arquitetura](#arquitetura)
- [Stack sugerida](#stack-sugerida)
- [Integracao em projetos](#integracao-em-projetos)
- [Limitacoes](#limitacoes)
- [Roadmap](#roadmap)

---

## Como funciona

```
Voce (prompt unico em linguagem natural)
       |
       v
+- engine.py ----------------------------+
|  Analise do texto:                    |
|  • Extrai nome da funcionalidade      |
|  • Identifica regras de negocio       |
|  • Detecta dependencias (DB, API)     |
|  • Mapeia fluxos de usuario           |
|  • Classifica cada regra              |
+----------+----------------------------+
           v
+- pyramid.py --------------------------+
|  Gera a piramide de testes:          |
|  +----------+                        |
|  | E2E 10%  |  <- fluxos criticos    |
|  +----------+                        |
|  | Integ 20%|  <- dependencias       |
|  +----------+                        |
|  | Unit 70% |  <- regras + val.      |
|  +----------+                        |
|  Cada camada com suites + casos      |
+----------+----------------------------+
           v
+- generator.py ------------------------+
|  Cria estrutura de pastas:           |
|  {output_path}/                      |
|  +-- _README_.md (contexto + git)    |
|  +-- unit/*.{ext}                    |
|  +-- integration/*.{ext}             |
|  +-- e2e/*.{ext}                     |
|  Stubs com Arrange/Act/Assert        |
|  READMEs contextuals por camada       |
+----------+----------------------------+
           v
   Relatorio .md + Pastas de teste
```

### Motor de analise

O `engine.py` usa **pattern matching baseado em regex** para extrair informacoes do seu texto:

- **Regras de negocio**: detecta padroes como `deve`, `nao pode`, `se...entao`, `minimo/maximo`, `obrigatorio`
- **Dependencias**: reconhece keywords como `postgres`, `redis`, `oauth`, `email`, `api`, `cache`, `queue`
- **Fluxos**: identifica blocos marcados com `Fluxo:` ou `Flow:` e extrai steps
- **Classificacao**: cada regra e categorizada como `validation`, `logic`, `security`, `boundary`, `error` ou `flow`

### Gerador da piramide

O `pyramid.py` mapeia a analise para a piramide:

| Camada | % da piramide | O que testa | Quantidade de testes |
|--------|:---:|---|:---:|
| **Unit** | 70% | Regras de negocio isoladas (sem dependencias) | Happy Path + Violation + Boundary |
| **Integration** | 20% | Interacao com dependencias reais/simuladas | Operacao + Falha + Dados inconsistentes |
| **E2E** | 10% | Fluxos completos do usuario | Happy Path + Sad Path |

### Gerador de estrutura

O `generator.py` traduz a piramide em **arquivos stub** com placeholder de codigo, usando a convencao de nomenclatura:

```
{camada}__{contexto}.{ext}
```

Exemplo:
```
login/
+-- _README_.md                (contexto + branch/commit + estatisticas)
+-- unit/
|   +-- _README_.md            (regras sendo testadas listadas)
|   +-- unit__regra_email_valido.spec.ts
|   +-- unit__regra_senha_8_caracteres.spec.ts
+-- integration/
|   +-- _README_.md            (dependencias identificadas)
|   +-- integration__database.spec.ts
|   +-- integration__api_oauth.spec.ts
+-- e2e/
    +-- _README_.md            (fluxos de usuario + criticos)
    +-- e2e__fluxo_login_sucesso.spec.ts
    +-- e2e__fluxo_login_invalido.spec.ts
```

### READMEs contextuais

Cada `_README_.md` gerado contem informacoes especificas da execucao:

| Arquivo | Informacoes |
|---------|-------------|
| **Root** | Branch atual, commit hash, mensagem do commit, feature analisada, data, estatisticas da piramide, regras listadas |
| **Unit** | Contexto da feature, git info, regras sendo testadas com qtd de casos, premissas |
| **Integration** | Contexto da feature, git info, dependencias identificadas, suites, premissas |
| **E2E** | Contexto da feature, git info, fluxos de usuario com indicacao de criticos, cenarios, premissas |

---

## Instalacao

### Requisitos

- **Python 3.7+** (sem dependencias externas — apenas a biblioteca padrao)

### Download

```bash
git clone https://github.com/rodrigod3v/cognis.git
cd cognis
```

Ou copie os 4 arquivos principais para seu projeto:

```bash
cp cli.py engine.py pyramid.py generator.py /seu/projeto/cognis/
```

---

## Uso

### Basico — prompt direto

```bash
python cli.py "Funcionalidade: Login de usuario. Regras: email deve ser unico, senha 8+ caracteres"
```

### A partir de arquivo

```bash
python cli.py --file descricao.txt
```

### Modo interativo

```bash
python cli.py --interactive
```

### Gerar estrutura de pastas com stubs

```bash
python cli.py --generate "Funcionalidade: Login..."
```

### Personalizar extensao dos stubs

```bash
python cli.py --generate --ext .spec.ts "Funcionalidade: Login..."
```

### Salvar relatorio em arquivo

```bash
python cli.py -o relatorio.md "Funcionalidade: Login..."
```

### Saida JSON

```bash
python cli.py --json "Funcionalidade: Login..." > arquitetura.json
```

### Usar arquivo de configuracao

Crie um `cognis.json` na raiz do seu projeto (ou use `--init-config`):

```bash
python cli.py --init-config
```

Isso gera:

```json
{
  "project_path": ".",
  "output_path": "tests__{feature}",
  "extension": ".test.tsx",
  "auto_generate": false,
  "report_dir": ".",
  "report_filename": "PLANO_TESTES_{feature}.md"
}
```

Depois e so usar:

```bash
python cli.py -f descricao.txt
```

O placeholder `{feature}` e substituido pelo nome da funcionalidade.
CLI args sobrescrevem valores do config:

```bash
python cli.py -c cognis.json --ext .spec.ts -f descricao.txt
```

### Inicializar configuracao padrao

```bash
python cli.py --init-config
# Cria cognis.json com valores padrao
```

### Multiplos configs para diferentes projetos

```bash
python cli.py -c cognis-projeto-a.json -f prompt.txt
python cli.py -c cognis-projeto-b.json -f prompt.txt
```

### Combinar flags

```bash
python cli.py -f descricao.txt -g --ext .test.ts -o plano_testes.md
```

### Ajuda

```bash
python cli.py --help
```

---

## Configuracao

O Cognis pode ser configurado via arquivo JSON (`cognis.json` por padrao).
Isso evita repetir flags a cada execucao.

### Estrutura do config

| Campo | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| `project_path` | string | `"."` | Caminho do projeto alvo |
| `output_path` | string | `"generated_tests"` | Diretorio de saida da estrutura de testes. Aceita `{feature}` |
| `extension` | string | `".md"` | Extensao dos arquivos stub gerados |
| `auto_generate` | bool | `false` | Se `true`, gera estrutura automaticamente ao rodar |
| `report_dir` | string | `"."` | Diretorio onde salvar o relatorio markdown |
| `report_filename` | string | `"PLANO_TESTES_{feature}.md"` | Nome do arquivo de relatorio. Aceita `{feature}` |

### Ordem de precedencia

1. CLI args (`--ext`, `--gen-dir`, `--generate`) **sobrescrevem** o config
2. Config file (`cognis.json`) **sobrescreve** os padroes
3. Valores padrao da ferramenta

### Exemplo de config para projeto React + Playwright

```json
{
  "project_path": ".",
  "output_path": "test-blueprints/{feature}",
  "extension": ".spec.ts",
  "auto_generate": true,
  "report_dir": "test-plans",
  "report_filename": "PLANO_TESTES_{feature}.md"
}
```

Com esse config, basta rodar:

```bash
python cli.py -f descricao_funcionalidade.txt
```

E o Cognis ja gera o relatorio + estrutura de pastas automaticamente nos diretorios configurados.

---

## Exemplo

### Input

```bash
python cli.py --generate "Funcionalidade: Login de usuario
Descricao: Sistema de autenticacao com email e senha

Regras de Negocio:
- Email deve ser valido e unico no sistema
- Senha deve ter no minimo 8 caracteres
- Usuario deve confirmar email antes do primeiro login

Entradas:
- Email (string)
- Senha (string)

Saidas:
- Token JWT
- Mensagem de erro

Dependencias:
- Banco PostgreSQL
- API de autenticacao Google OAuth2

Fluxos:
- Fluxo critico: Login com sucesso -> token -> acesso protegido
- Fluxo: Login invalido -> mensagem de erro"
```

### Output gerado

Estrutura de pastas:

```
login/
+-- _README_.md                    (branch: main | commit: abc1234 | data: ...)
+-- unit/
|   +-- _README_.md                (3 regras sendo testadas | 8 casos)
|   +-- unit__regra_email_valido.spec.md
|   +-- unit__regra_senha_8_caracteres.spec.md
|   +-- unit__regra_confirmar_email.spec.md
|   +-- unit__validacao_entradas.spec.md
+-- integration/
|   +-- _README_.md                (2 dependencias identificadas)
|   +-- integration__integracao_database.spec.md
|   +-- integration__integracao_oauth2.spec.md
+-- e2e/
    +-- _README_.md                (2 fluxos | 1 critico)
    +-- e2e__fluxo_login_sucesso.spec.md
    +-- e2e__fluxo_login_invalido.spec.md
```

Exemplo de README contextual gerado (`unit/_README_.md`):

```markdown
# Unit Tests: Login de usuario

> **Contexto:** Sistema de autenticacao com email e senha
> **Branch:** `main` | **Commit:** `abc1234`
> **Mensagem:** feat: implementa modulo de login

Total de suites nesta camada: 4

## Regras sendo testadas
- Regra: Email deve ser valido — 2 caso(s) de teste
- Regra: Senha 8+ caracteres — 3 caso(s) de teste (inclui boundary)
- Regra: Confirmar email antes do login — 2 caso(s) de teste
- Validacao de Entradas — 2 caso(s) de teste
```

---

## Saidas

### Relatorio Markdown

O relatorio inclui:

1. **Visao geral** — entidades, dependencias, regras, fluxos
2. **Contrato** — inputs e outputs esperados
3. **Regras de negocio** — listadas com categoria e camada sugerida
4. **Piramide de testes** — representacao visual
5. **Testes detalhados por camada**:
   - **Unit**: cada regra vira uma suite com Happy Path + Violation (+ Boundary quando aplicavel)
   - **Integration**: cada dependencia gera teste de operacao normal, falha e dados inconsistentes
   - **E2E**: cada fluxo gera Happy Path + Sad Path
6. **Checklist de implementacao** — passos praticos por camada
7. **Recomendacoes** — stack de testes, cobertura, CI/CD

### Estrutura de pastas (com `--generate`)

Cada arquivo stub contem:
- Metadados da suite de teste
- Descricao detalhada de cada caso
- Codigo placeholder com Arrange/Act/Assert
- Formato Gherkin para cenarios E2E
- README contextual por camada com branch/commit e estatisticas

### JSON (com `--json`)

Estrutura completa dos dados em JSON para integracao com outras ferramentas.

---

## Arquitetura

```
cognis/
+-- cli.py          # Ponto de entrada (CLI)
+-- engine.py       # Motor de analise do texto
+-- pyramid.py      # Gerador da piramide de testes
+-- generator.py    # Gerador de estrutura de pastas + READMEs contextuais
+-- cognis.json     # Arquivo de configuracao (projeto-especifico, gitignorado)
+-- cognis.example.json  # Exemplo de configuracao
```

| Modulo | Responsabilidade |
|--------|-----------------|
| `cli.py` | Interface de linha de comando, parsing de args, config, saida |
| `engine.py` | Analise NLP via regex, extracao de regras/deps/fluxos |
| `pyramid.py` | Mapeamento para piramide, geracao de suites/casos |
| `generator.py` | Criacao de pastas, stubs e READMEs contextuais com git info |

Cada modulo e independente e pode ser usado separadamente via import:

```python
from engine import AnalysisEngine
from pyramid import PyramidReport
from generator import generate_test_structure

engine = AnalysisEngine()
feature = engine.analyze("Funcionalidade: ...")
report = PyramidReport(feature)
generate_test_structure(report, output_dir=".", ext=".spec.ts")
```

---

## Stack sugerida

O relatorio sugere frameworks adequados para cada camada, detectando o contexto do seu projeto:

| Camada | Frameworks sugeridos |
|--------|---------------------|
| **Unit** | Jest, Vitest, JUnit, pytest, XCTest, Mocha |
| **Integration** | Supertest, TestContainers, WireMock, pytest-postgresql |
| **E2E** | Cypress, Playwright, Detox, Appium, XCUITest, Espresso |

---

## Integracao em projetos

### Estrutura recomendada em projetos de teste

```
meu-projeto/
+-- cognis/                        # Tool (copiar ou submodulo)
|   +-- cli.py
|   +-- engine.py
|   +-- pyramid.py
|   +-- generator.py
|   +-- cognis.json                # Config do projeto
+-- tests/                         # Testes manuais implementados
+-- pages/                         # Page Objects (se aplicavel)
+-- test-plans/                    # Relatorios gerados (output)
+-- test-blueprints/               # Stubs gerados (output)
+-- scripts/
    +-- gerar-testes.py            # Wrapper para executar cognis
```

### Exemplo de wrapper (`scripts/gerar-testes.py`)

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cognis"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "cognis"))
from cli import main
main()
```

### Fluxo de trabalho recomendado

1. Instale o Cognis no diretorio `cognis/` do seu projeto
2. Crie um `cognis.json` apontando os outputs para `test-plans/` e `test-blueprints/`
3. Identifique uma funcionalidade a ser testada
4. Descreva a funcionalidade + regras de negocio em um arquivo `.txt`
5. Execute: `python cognis/cli.py -f descricao.txt -g`
6. Use o relatorio em `test-plans/` como guia
7. Implemente os testes seguindo os stubs em `test-blueprints/`

---

## Contribuicao

1. Fork o repositorio
2. Crie uma branch (`git checkout -b feat/nova-funcionalidade`)
3. Commit suas mudancas (`git commit -m 'feat: adiciona...'`)
4. Push para a branch (`git push origin feat/nova-funcionalidade`)
5. Abra um Pull Request

---

## Limitacoes atuais

1. **Nao gera codigo de teste executavel** — apenas stubs com placeholder. O desenvolvedor precisa implementar a logica real.
2. **Analise baseada em regex** — funciona bem para prompts estruturados, mas nao entende linguagem natural complexa. Para melhores resultados, use secoes claras: `Regras:`, `Entradas:`, `Saidas:`, `Dependencias:`, `Fluxos:`.
3. **Sem suporte a multiplos idiomas** no prompt — otimizado para portugues e ingles.
4. **Deteccao de entidades limitada** — entidades sao inferidas do contexto, nao de schemas ou types reais.

---

## Roadmap

- [ ] Geracao de codigo de teste real (Jest, pytest, Playwright)
- [ ] Suporte a entrada via YAML/JSON estruturado
- [ ] Integracao com OpenAPI/Swagger para detectar endpoints
- [ ] Modo interativo com perguntas guiadas
- [ ] Plugin para VSCode
- [ ] Suporte a multiplos cenarios por fluxo
- [ ] Exportacao para formatos JUnit XML / xUnit

---

## Licenca

MIT © [Rodrigo Dev](https://github.com/rodrigod3v)
