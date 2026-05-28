# Cognis — Gerador de Arquitetura de Testes

**Cognis** é uma CLI em Python puro (zero dependências externas) que analisa descrições em linguagem natural de funcionalidades e gera automaticamente a **arquitetura completa de testes** baseada no modelo da **Pirâmide de Testes**.

Em vez de gastar horas pensando "o que testar?", você descreve a funcionalidade e as regras de negócio, e o Cognis entrega:

- Um **relatório markdown** com features, regras, inputs/outputs, dependências, fluxos
- A **pirâmide de testes completa**: Unit → Integration → E2E
- **Casos de teste detalhados** (Happy Path + Violation + Boundary + Error)
- Uma **estrutura de pastas** com stubs prontos para implementar
- **Checklist de implementação** e sugestão de frameworks

---

## Índice

- [Como funciona](#como-funciona)
- [Instalação](#instalação)
- [Uso](#uso)
- [Configuração](#configuração)
- [Exemplo](#exemplo)
- [Saídas](#saídas)
- [Arquitetura](#arquitetura)
- [Stack sugerida](#stack-sugerida)
- [Limitações](#limitações)
- [Roadmap](#roadmap)

---

## Como funciona

```
Você (prompt único em linguagem natural)
       │
       ▼
┌─ engine.py ──────────────────────┐
│  Análise do texto:               │
│  • Extrai nome da funcionalidade │
│  • Identifica regras de negócio  │
│  • Detecta dependências (DB,API) │
│  • Mapeia fluxos de usuário      │
│  • Classifica cada regra         │
└──────────┬───────────────────────┘
           ▼
┌─ pyramid.py ─────────────────────┐
│  Gera a pirâmide de testes:      │
│  ┌──────────┐                    │
│  │ E2E 10%  │  ← fluxos críticos │
│  ├──────────┤                    │
│  │ Integ 20%│  ← dependências    │
│  ├──────────┤                    │
│  │ Unit 70% │  ← regras + val.   │
│  └──────────┘                    │
│  Cada camada com suites + casos  │
└──────────┬───────────────────────┘
           ▼
┌─ generator.py ───────────────────┐
│  Cria estrutura de pastas:       │
│  tests__{feature}/               │
│  ├── unit/*.{ext}                │
│  ├── integration/*.{ext}         │
│  └── e2e/*.{ext}                 │
│  Stubs com Arrange/Act/Assert    │
└──────────┬───────────────────────┘
           ▼
   Relatório .md + Pastas de teste
```

### Motor de análise

O `engine.py` usa **pattern matching baseado em regex** para extrair informações do seu texto:

- **Regras de negócio**: detecta padrões como `deve`, `não pode`, `se...então`, `mínimo/máximo`, `obrigatório`
- **Dependências**: reconhece keywords como `postgres`, `redis`, `oauth`, `email`, `api`, `cache`, `queue`
- **Fluxos**: identifica blocos marcados com `Fluxo:` ou `Flow:` e extrai steps
- **Classificação**: cada regra é categorizada como `validation`, `logic`, `security`, `boundary`, `error` ou `flow`

### Gerador da pirâmide

O `pyramid.py` mapeia a análise para a pirâmide:

| Camada | % da pirâmide | O que testa | Quantidade de testes |
|--------|:---:|---|:---:|
| **Unit** | 70% | Regras de negócio isoladas (sem dependências) | Happy Path + Violation + Boundary |
| **Integration** | 20% | Interação com dependências reais/simuladas | Operação + Falha + Dados inconsistentes |
| **E2E** | 10% | Fluxos completos do usuário | Happy Path + Sad Path |

### Gerador de estrutura

O `generator.py` traduz a pirâmide em **arquivos stub** com placeholder de código, usando a convenção de nomenclatura:

```
{camada}__{contexto}.{ext}
```

Exemplo:
```
tests__login_usuario/
├── unit__regra_email_valido.{ext}
├── integration__integracao_com_database.{ext}
└── e2e__fluxo_login_com_sucesso.{ext}
```

---

## Instalação

### Requisitos

- **Python 3.7+** (sem dependências externas — apenas a biblioteca padrão)

### Download

```bash
git clone https://github.com/rodrigod3v/cognis.git
cd cognis
```

Ou copie os 4 arquivos (`cli.py`, `engine.py`, `pyramid.py`, `generator.py`) para seu projeto.

---

## Uso

### Básico — prompt direto

```bash
python cli.py "Funcionalidade: Login de usuário. Regras: email deve ser único, senha 8+ caracteres"
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

### Personalizar extensão dos stubs

```bash
python cli.py --generate --ext .spec.ts "Funcionalidade: Login..."
```

### Salvar relatório em arquivo

```bash
python cli.py -o relatorio.md "Funcionalidade: Login..."
```

### Saída JSON

```bash
python cli.py --json "Funcionalidade: Login..." > arquitetura.json
```

### Usar arquivo de configuração

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
  "auto_generate": true,
  "report_dir": "testsprite_tests",
  "report_filename": "PLANO_TESTES_{feature}.md"
}
```

Depois é só usar:

```bash
python cli.py -f descricao.txt
```

O placeholder `{feature}` é substituído pelo nome da funcionalidade.
CLI args sobrescrevem valores do config:

```bash
python cli.py -c cognis.json --ext .spec.ts -f descricao.txt
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

## Configuração

O Cognis pode ser configurado via arquivo JSON (`cognis.json` por padrão).
Isso evita repetir flags a cada execução.

### Inicializar configuração padrão

```bash
python cli.py --init-config
# Cria cognis.json com valores padrão
```

### Estrutura do config

| Campo | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `project_path` | string | `"."` | Caminho do projeto alvo |
| `output_path` | string | `"generated_tests"` | Diretório de saída da estrutura de testes. Aceita `{feature}` |
| `extension` | string | `".md"` | Extensão dos arquivos stub gerados |
| `auto_generate` | bool | `false` | Se `true`, gera estrutura automaticamente ao rodar |
| `report_dir` | string | `"."` | Diretório onde salvar o relatório markdown |
| `report_filename` | string | `"PLANO_TESTES_{feature}.md"` | Nome do arquivo de relatório. Aceita `{feature}` |

### Ordem de precedência

1. CLI args (`--ext`, `--gen-dir`, `--generate`) **sobrescrevem** o config
2. Config file (`cognis.json`) **sobrescreve** os padrões
3. Valores padrão da ferramenta

### Exemplo de config para um projeto React + Vitest

```json
{
  "project_path": ".",
  "output_path": "tests__{feature}",
  "extension": ".test.tsx",
  "auto_generate": true,
  "report_dir": "testsprite_tests",
  "report_filename": "PLANO_TESTES_{feature}.md"
}
```

Com esse config, basta rodar:

```bash
python cli.py -f descricao_funcionalidade.txt
```

E o Cognis já gera o relatório + estrutura de pastas automaticamente.

### Múltiplos configs

Você pode ter diferentes configs para diferentes projetos:

```bash
python cli.py -c cognis-projeto-a.json -f prompt.txt
python cli.py -c cognis-projeto-b.json -f prompt.txt
```

---

## Exemplo

### Input

```bash
python cli.py --generate "Funcionalidade: Login de usuário
Descrição: Sistema de autenticação com email e senha

Regras de Negócio:
- Email deve ser válido e único no sistema
- Senha deve ter no mínimo 8 caracteres
- Usuário deve confirmar email antes do primeiro login

Entradas:
- Email (string)
- Senha (string)

Saídas:
- Token JWT
- Mensagem de erro

Dependências:
- Banco PostgreSQL
- API de autenticação Google OAuth2

Fluxos:
- Fluxo crítico: Login com sucesso -> token -> acesso protegido
- Fluxo: Login inválido -> mensagem de erro"
```

### Output

```
Plano de Testes: Login de usuário
═══════════════════════════════════

📋 Visão Geral
──────────────
Entidades      : Usuário
Dependências   : PostgreSQL (database), Google OAuth2 (api)
Regras         : 3 identificadas
Fluxos         : 2 (1 crítico)

📐 Regras de Negócio
────────────────────
RN1: [VALIDACAO] Email deve ser válido
RN2: [LIMITE]    Senha 8+ caracteres
RN3: [LOGICA]    Confirmar email antes do login

🏗️ Pirâmide de Testes
──────────────────────
          [E2E] (10%)
        [Integração] (20%)
  [Unit] [Unit] [Unit] (70%)

✅ Checklist de Implementação
─────────────────────────────
...

Estrutura de testes criada em: tests__login_usuario/
```

Estrutura gerada:

```
tests__login_usuario/
├── _README_.md
├── unit/
│   ├── _README_.md
│   ├── unit__regra_email_valido.md
│   ├── unit__regra_senha_8_caracteres.md
│   └── unit__validacao_entradas.md
├── integration/
│   ├── _README_.md
│   ├── integration__integracao_database.md
│   └── integration__integracao_oauth2.md
└── e2e/
    ├── _README_.md
    ├── e2e__fluxo_login_sucesso.md
    └── e2e__fluxo_login_invalido.md
```

---

## Saídas

### Relatório Markdown

O relatório inclui:

1. **Visão geral** — entidades, dependências, regras, fluxos
2. **Contrato** — inputs e outputs esperados
3. **Regras de negócio** — listadas com categoria e camada sugerida
4. **Pirâmide de testes** — representação visual
5. **Testes detalhados por camada**:
   - **Unit**: cada regra vira uma suite com Happy Path + Violation (+ Boundary quando aplicável)
   - **Integration**: cada dependência gera teste de operação normal, falha e dados inconsistentes
   - **E2E**: cada fluxo gera Happy Path + Sad Path
6. **Checklist de implementação** — passos práticos por camada
7. **Recomendações** — stack de testes, cobertura, CI/CD

### Estrutura de pastas (com `--generate`)

Cada arquivo stub contém:
- Metadados da suite de teste
- Descrição detalhada de cada caso
- Código placeholder com Arrange/Act/Assert
- Formato Gherkin para cenários E2E

### JSON (com `--json`)

Estrutura completa dos dados em JSON para integração com outras ferramentas.

---

## Arquitetura

```
cognis/
├── cli.py          # Ponto de entrada (CLI)
├── engine.py       # Motor de análise do texto
├── pyramid.py      # Gerador da pirâmide de testes
└── generator.py    # Gerador de estrutura de pastas
```

| Módulo | Responsabilidade |
|--------|-----------------|
| `cli.py` | Interface de linha de comando, parsing de args, saída |
| `engine.py` | Análise NLP via regex, extração de regras/deps/fluxos |
| `pyramid.py` | Mapeamento para pirâmide, geração de suites/casos |
| `generator.py` | Criação de pastas e arquivos stub |

Cada módulo é independente e pode ser usado separadamente via import:

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

O relatório sugere frameworks adequados para cada camada, detectando o contexto do seu projeto:

| Camada | Frameworks sugeridos |
|--------|---------------------|
| **Unit** | Jest, Vitest, JUnit, pytest, XCTest, Mocha |
| **Integration** | Supertest, TestContainers, WireMock, pytest-postgresql |
| **E2E** | Cypress, Playwright, Detox, Appium, XCUITest, Espresso |

---

## Limitações atuais

1. **Não gera código de teste executável** — apenas stubs com placeholder. O desenvolvedor precisa implementar a lógica real.
2. **Análise baseada em regex** — funciona bem para prompts estruturados, mas não entende linguagem natural complexa. Para melhores resultados, use seções claras: `Regras:`, `Entradas:`, `Saídas:`, `Dependências:`, `Fluxos:`.
3. **Sem suporte a múltiplos idiomas** no prompt — otimizado para português e inglês.
4. **Detecção de entidades limitada** — entidades são inferidas do contexto, não de schemas ou types reais.

---

## Roadmap

- [ ] Geração de código de teste real (Jest, pytest, Cypress)
- [ ] Suporte a entrada via YAML/JSON estruturado
- [ ] Integração com OpenAPI/Swagger para detectar endpoints
- [ ] Modo interativo com perguntas guiadas
- [ ] Plugin para VSCode
- [ ] Suporte a múltiplos cenários por fluxo
- [ ] Exportação para formatos JUnit XML / xUnit

---

## Contribuição

1. Fork o repositório
2. Crie uma branch (`git checkout -b feat/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona...'`)
4. Push para a branch (`git push origin feat/nova-funcionalidade`)
5. Abra um Pull Request

---

## Licença

MIT © [Rodrigo Dev](https://github.com/rodrigod3v)
