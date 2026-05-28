import os
import re
import subprocess
from pathlib import Path
from pyramid import PyramidReport, TestSuite, TestCase


def _sanitize(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "_", text.strip().lower())
    return text[0:max_len].rstrip("_")


def _safe_filename(text: str, max_len: int = 40) -> str:
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    text = re.sub(r"\s+", "_", text.strip().lower())
    return text[0:max_len].rstrip("_")


def _feature_slug(report: PyramidReport) -> str:
    return _sanitize(report.feature.feature_name, 30)


def _git_context():
    ctx = {
        "branch": "N/A",
        "commit_hash": "N/A",
        "commit_message": "N/A",
    }
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if branch.returncode == 0:
            ctx["branch"] = branch.stdout.strip()
    except Exception:
        pass
    try:
        commit_hash = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if commit_hash.returncode == 0:
            ctx["commit_hash"] = commit_hash.stdout.strip()
    except Exception:
        pass
    try:
        commit_msg = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            capture_output=True, text=True, timeout=5
        )
        if commit_msg.returncode == 0:
            ctx["commit_message"] = commit_msg.stdout.strip()
    except Exception:
        pass
    return ctx


def _describe_test_case(tc: TestCase) -> str:
    parts = []
    if tc.description:
        parts.append(f"Descricao: {tc.description}")
    if tc.input_data:
        parts.append(f"Entrada: {tc.input_data}")
    if tc.expected:
        parts.append(f"Esperado: {tc.expected}")
    if tc.rule_ref:
        parts.append(f"Regra: {tc.rule_ref}")
    return "\n".join(parts)


def _describe_test_case_md(tc: TestCase) -> str:
    parts = []
    if tc.description:
        parts.append(f"**Descricao:** {tc.description}")
    if tc.input_data:
        parts.append(f"**Entrada:** `{tc.input_data}`")
    if tc.expected:
        parts.append(f"**Esperado:** {tc.expected}")
    if tc.rule_ref:
        parts.append(f"**Regra:** {tc.rule_ref}")
    return "  \n".join(parts)


def _write_unit_stub(base: Path, feature_slug: str, suite: TestSuite, idx: int):
    rule_slug = _safe_filename(suite.name, 35)
    filename = f"unit__{rule_slug}.md"
    filepath = base / filename

    lines = []
    lines.append(f"# Unit Test: {suite.name}\n")
    lines.append(f"**Descricao:** {suite.description}  \n")
    lines.append(f"**Feature:** {feature_slug}  \n")
    lines.append(f"**Camada:** Unit — testar regra isoladamente sem dependencias  \n")
    lines.append("---\n")

    for rule in suite.test_cases:
        tag = "HAPPY_PATH" if "Happy" in rule.name else "VIOLATION" if "Violation" in rule.name else "EDGE_CASE"
        lines.append(f"### [{tag}] {rule.name}\n")
        lines.append(f"{_describe_test_case_md(rule)}\n")
        lines.append("```python")
        lines.append(f"# def test_{_safe_filename(rule.name, 40)}():")
        lines.append(f"#     # Arrange")
        desc = _describe_test_case(rule)
        for d in desc.split("\n"):
            lines.append(f"#     # {d}")
        lines.append(f"#     # Act")
        lines.append(f"#     # Assert")
        lines.append("```\n")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def _write_integration_stub(base: Path, feature_slug: str, suite: TestSuite, idx: int):
    dep_slug = _safe_filename(suite.name, 35)
    filename = f"integration__{dep_slug}.md"
    filepath = base / filename

    lines = []
    lines.append(f"# Integration Test: {suite.name}\n")
    lines.append(f"**Descricao:** {suite.description}  \n")
    lines.append(f"**Feature:** {feature_slug}  \n")
    lines.append(f"**Camada:** Integration — testar interacao com dependencia real ou simulada  \n")
    lines.append("---\n")

    for tc in suite.test_cases:
        lines.append(f"### {tc.name}\n")
        lines.append(f"{_describe_test_case_md(tc)}\n")
        lines.append("```python")
        lines.append(f"# def test_{_safe_filename(tc.name, 40)}():")
        lines.append(f"#     # Arrange (setup real dependency or mock)")
        desc = _describe_test_case(tc)
        for d in desc.split("\n"):
            lines.append(f"#     # {d}")
        lines.append(f"#     # Act")
        lines.append(f"#     # Assert")
        lines.append("```\n")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def _write_e2e_stub(base: Path, feature_slug: str, suite: TestSuite, idx: int):
    flow_slug = _safe_filename(suite.name, 35)
    filename = f"e2e__{flow_slug}.md"
    filepath = base / filename

    lines = []
    lines.append(f"# E2E Test: {suite.name}\n")
    lines.append(f"**Descricao:** {suite.description}  \n")
    lines.append(f"**Feature:** {feature_slug}  \n")
    lines.append(f"**Camada:** E2E — simular jornada completa do usuario  \n")
    lines.append("---\n")

    for tc in suite.test_cases:
        lines.append(f"### {tc.name}\n")
        lines.append(f"{_describe_test_case_md(tc)}\n")
        lines.append("```gherkin")
        lines.append("Feature: " + suite.name)
        if "Happy" in tc.name:
            lines.append("  Scenario: Fluxo de sucesso")
        else:
            lines.append("  Scenario: Fluxo com falha")
        lines.append("    Given ...")
        lines.append("    When ...")
        lines.append("    Then ...")
        lines.append("```\n")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def _generate_layer_readme(report: PyramidReport, layer_name: str, test_suites: list,
                           git_ctx: dict, count: int) -> str:
    f = report.feature
    lines = []
    layer_title = {"unit": "Unit Tests", "integration": "Integration Tests", "e2e": "E2E Tests (End-to-End)"}
    layer_desc = {
        "unit": "Testam a menor unidade de codigo isoladamente — regras de negocio, validacoes, logicas puras.",
        "integration": "Testam a interacao entre componentes — banco de dados, APIs, servicos externos.",
        "e2e": "Testam o fluxo completo do sistema como um usuario real — jornadas criticas e cenarios de falha.",
    }
    layer_icon = {"unit": "🔵", "integration": "🟡", "e2e": "🔴"}
    icon = layer_icon.get(layer_name, "📁")
    title = layer_title.get(layer_name, layer_name.capitalize())

    lines.append(f"# {icon} {title}: {f.feature_name}\n")
    lines.append(f"> **Contexto:** {f.summary}  ")
    lines.append(f"> **Branch:** `{git_ctx['branch']}` | **Commit:** `{git_ctx['commit_hash']}`  ")
    lines.append(f"> **Mensagem:** {git_ctx['commit_message']}  \n")
    lines.append("---\n")
    lines.append(f"**Descricao da camada:** {layer_desc.get(layer_name, '')}  \n")
    lines.append(f"**Total de suites nesta camada:** {count}  \n")

    # Layer-specific content
    if layer_name == "unit":
        lines.append("\n## Regras sendo testadas\n")
        if test_suites:
            for suite in test_suites:
                n_cases = len(suite.test_cases)
                lines.append(f"- **{suite.name}** — {n_cases} caso(s) de teste")
        else:
            lines.append("Nenhuma suite de teste unitario gerada.\n")

        lines.append(f"""
## O que validar aqui

1. **Regras de negocio** — cada regra extraida vira uma suite independente
2. **Happy Path** — cenario onde a regra eh satisfeita com dados validos
3. **Violation** — cenario onde a regra eh violada, deve ser rejeitada
4. **Boundary** — valores limites (exato no minimo, exato no maximo)
5. **Edge Cases** — entradas inesperadas, nulas, ou em formatos incorretos

## Premissas

- Todas as dependencias externas (API, banco, cache) devem ser **mockadas/stubadas**
- Cada teste deve ser atomico e independente
- Nao deve haver chamadas de rede ou I/O em testes unitarios
""")

    elif layer_name == "integration":
        deps = [(d.name, d.type) for d in f.dependencies]
        lines.append("\n## Dependencias envolvidas\n")
        if deps:
            for dep_name, dep_type in deps:
                lines.append(f"- **{dep_name}** (`{dep_type}`)")
        else:
            lines.append("Nenhuma dependencia externa identificada.\n")

        if test_suites:
            lines.append("\n## Suites de integracao\n")
            for suite in test_suites:
                n_cases = len(suite.test_cases)
                lines.append(f"- **{suite.name}** — {n_cases} caso(s) de teste")

        lines.append(f"""
## O que validar aqui

1. **Operacao basica** — fluxo normal de comunicacao com a dependencia
2. **Tratamento de falha** — comportamento quando a dependencia esta indisponivel
3. **Dados inconsistentes** — resiliencia com dados corrompidos ou inesperados

## Premissas

- Usar banco de testes ou in-memory database para dependencias de dados
- Mockar apenas servicos externos instaveis ou de terceiros
- Garantir cleanup entre testes (reset de banco, flush de cache)
""")

    elif layer_name == "e2e":
        critical = sum(1 for fl in f.flows if fl.is_critical) if f.flows else 0
        total_flows = len(f.flows) if f.flows else 0
        lines.append(f"\n## Fluxos de usuario\n")
        lines.append(f"**Total:** {total_flows} | **Criticos:** {critical}  \n")
        if f.flows:
            for fl in f.flows:
                tag = "CRITICO" if fl.is_critical else "Secundario"
                lines.append(f"- [{tag}] {fl.description}")
        else:
            lines.append("Nenhum fluxo de usuario identificado.\n")

        if test_suites:
            lines.append("\n## Cenarios E2E\n")
            for suite in test_suites:
                n_cases = len(suite.test_cases)
                lines.append(f"- **{suite.name}** — {n_cases} cenario(s)")

        lines.append(f"""
## O que validar aqui

1. **Happy Path** — jornada completa de sucesso do inicio ao fim
2. **Sad Path** — jornada com falha, verificando mensagens de erro e recuperacao
3. **Cenarios criticos** — fluxos principais do negocio devem ter prioridade

## Premissas

- Usar dados reais ou proximos de producao (via fixture ou API)
- Evitar setup pela UI — usar chamadas de API diretas para preparar estado
- Manter conjunto pequeno e focado (~10% da piramide de testes)
- Cenarios E2E devem rodar em paralelo no CI/CD
""")

    return "\n".join(lines)


def _generate_root_readme(report: PyramidReport, feature_slug: str,
                          git_ctx: dict, unit_count: int, integration_count: int,
                          e2e_count: int) -> str:
    f = report.feature
    deps = [(d.name, d.type) for d in f.dependencies]
    rules = [r for r in f.business_rules if r.description != "Regra de negocio nao especificada"]

    lines = []
    lines.append(f"# Plano de Testes: {f.feature_name}\n")
    lines.append(f"> **Descricao:** {f.summary}  \n")

    # Git context
    lines.append("## Contexto da alteracao\n")
    lines.append(f"| Item | Valor |")
    lines.append(f"|------|-------|")
    lines.append(f"| **Branch** | `{git_ctx['branch']}` |")
    lines.append(f"| **Commit** | `{git_ctx['commit_hash']}` |")
    lines.append(f"| **Mensagem** | {git_ctx['commit_message']} |")
    lines.append(f"| **Feature analisada** | {f.feature_name} |")
    lines.append(f"| **Data de geracao** | {_now_str()} |")
    lines.append("\n")

    # Summary
    lines.append("## Resumo da analise\n")
    lines.append("| Item | Detalhes |")
    lines.append("|------|----------|")
    entities_str = ", ".join(e.name for e in f.entities) if f.entities else "Nao identificada"
    lines.append(f"| **Entidades** | {entities_str} |")
    deps_str = "; ".join(f"{n} ({t})" for n, t in deps) if deps else "Nenhuma"
    lines.append(f"| **Dependencias** | {deps_str} |")
    lines.append(f"| **Regras de negocio** | {len(rules)} |")
    lines.append(f"| **Fluxos de usuario** | {len(f.flows)} ({sum(1 for fl in f.flows if fl.is_critical)} criticos) |")
    lines.append(f"| **Inputs** | {len(f.inputs)} |")
    lines.append(f"| **Outputs** | {len(f.outputs)} |")
    lines.append("\n")

    # Rules list
    if rules:
        lines.append("## Regras de negocio identificadas\n")
        for i, rule in enumerate(rules, 1):
            badge = {"validation": "[VALIDACAO]", "logic": "[LOGICA]", "security": "[SEGURANCA]",
                     "boundary": "[LIMITE]", "error": "[ERRO]", "flow": "[FLUXO]"}.get(rule.category, "[REGRA]")
            lines.append(f"{i}. {badge} {rule.description} — camada: `{rule.layer_hint}`")

    # Test pyramid stats
    total = unit_count + integration_count + e2e_count
    lines.append(f"""
## Piramide de Testes

```
          [E2E] ({e2e_count} arquivos)
        [Integracao] ({integration_count} arquivos)
  [Unit] [Unit] [Unit] ({unit_count} arquivos)
```
**Total de arquivos gerados:** {total}

## Estrutura

```
{feature_slug}/
├── _README_.md          # Este arquivo
├── unit/                # Testes unitarios ({unit_count} arquivos)
│   ├── _README_.md
│   └── unit__*.md
├── integration/         # Testes de integracao ({integration_count} arquivos)
│   ├── _README_.md
│   └── integration__*.md
└── e2e/                 # Testes E2E ({e2e_count} arquivos)
    ├── _README_.md
    └── e2e__*.md
```

## Convencao de nomenclatura

- `unit__<regra>.md` — Um arquivo por regra de negocio
- `integration__<dependencia>.md` — Um arquivo por dependencia externa
- `e2e__<fluxo>.md` — Um arquivo por fluxo de usuario

Regra geral: `{{camada}}__{{contexto}}.md`
""")

    return "\n".join(lines)


def _now_str() -> str:
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def generate_test_structure(report: PyramidReport, output_dir: str = "generated_tests", ext: str = ".md"):
    """
    Gera a estrutura de pastas e arquivos stub de teste baseada no relatorio.

    O `output_dir` eh usado diretamente como raiz. Se quiser um subdiretorio
    com o nome da feature, inclua `{feature}` no path (ex: "tests__{feature}").

    Args:
        report: PyramidReport gerado pelo analisador
        output_dir: diretorio raiz onde os testes serao criados
        ext: extensao dos arquivos de teste (ex: .md, .spec.ts, .test.py)

    Returns:
        Caminho absoluto do diretorio raiz criado
    """
    feature_slug = _feature_slug(report)
    root_name = output_dir.replace("{feature}", feature_slug)
    root = Path(root_name)

    if root.exists():
        import shutil
        shutil.rmtree(str(root))

    # Create layer dirs
    unit_dir = root / "unit"
    integration_dir = root / "integration"
    e2e_dir = root / "e2e"

    for d in [root, unit_dir, integration_dir, e2e_dir]:
        d.mkdir(parents=True, exist_ok=True)

    git_ctx = _git_context()
    unit_count = 0
    integration_count = 0
    e2e_count = 0

    # --- Unit layer ---
    unit_suites = report.layers[0].test_suites if len(report.layers) > 0 else []
    for idx, suite in enumerate(unit_suites):
        try:
            _write_unit_stub(unit_dir, feature_slug, suite, idx)
            unit_count += 1
        except Exception:
            pass
    unit_readme = _generate_layer_readme(report, "unit", unit_suites, git_ctx, unit_count)
    (unit_dir / "_README_.md").write_text(unit_readme.strip() + "\n", encoding="utf-8")

    # --- Integration layer ---
    integration_suites = report.layers[1].test_suites if len(report.layers) > 1 else []
    for idx, suite in enumerate(integration_suites):
        try:
            _write_integration_stub(integration_dir, feature_slug, suite, idx)
            integration_count += 1
        except Exception:
            pass
    integration_readme = _generate_layer_readme(report, "integration", integration_suites, git_ctx, integration_count)
    (integration_dir / "_README_.md").write_text(integration_readme.strip() + "\n", encoding="utf-8")

    # --- E2E layer ---
    e2e_suites = report.layers[2].test_suites if len(report.layers) > 2 else []
    for idx, suite in enumerate(e2e_suites):
        try:
            _write_e2e_stub(e2e_dir, feature_slug, suite, idx)
            e2e_count += 1
        except Exception:
            pass
    e2e_readme = _generate_layer_readme(report, "e2e", e2e_suites, git_ctx, e2e_count)
    (e2e_dir / "_README_.md").write_text(e2e_readme.strip() + "\n", encoding="utf-8")

    # Root README
    root_readme = _generate_root_readme(report, feature_slug, git_ctx, unit_count, integration_count, e2e_count)
    (root / "_README_.md").write_text(root_readme.strip() + "\n", encoding="utf-8")

    return str(root.absolute())
