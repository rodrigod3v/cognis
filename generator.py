import os
import re
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


LAYER_README = {
    "unit": """# Unit Tests

**O que testar aqui:**
- Regras de negocio isoladamente (sem dependencias externas)
- Validacoes de entrada (formato, tipos, limites)
- Logica pura (calculos, transformacoes, decisoes)
- Edge cases e boundary conditions
- Tratamento de erros e excecoes

**Frameworks sugeridos:** Jest, Vitest, JUnit, pytest, XCTest

**Dicas:**
- Mock/Stub todas as dependencias externas
- Um teste por comportamento (arrange, act, assert)
- Prefira testar comportamento a implementacao
""",
    "integration": """# Integration Tests

**O que testar aqui:**
- Interacao com banco de dados (CRUD, migrations, queries)
- Comunicacao com APIs externas (HTTP, GraphQL, gRPC)
- Servicos de terceiros (email, pagamento, notificacao)
- Cache e filas (Redis, RabbitMQ, SQS)
- Contratos entre camadas da aplicacao

**Frameworks sugeridos:** Supertest, TestContainers, WireMock, pytest-postgresql

**Dicas:**
- Use banco de testes ou in-memory database
- Mock apenas servicos externos instaveis
- Garanta cleanup entre testes (reset DB, flush cache)
""",
    "e2e": """# E2E Tests (End-to-End)

**O que testar aqui:**
- Jornadas criticas do usuario (happy paths)
- Fluxos de erro e recuperacao (sad paths)
- Integracao entre todos os componentes do sistema
- Cenarios reais com dados proximos de producao

**Frameworks sugeridos:** Cypress, Playwright, Detox, Appium, XCTest, Espresso

**Dicas:**
- Comece pelos fluxos criticos do negocio
- Mantenha um conjunto pequeno e focado (10% da piramide)
- Use dados via fixture ou API, evite UI para setup
- Rode em paralelo no CI/CD para reduzir feedback time
""",
}


def _write_layer_readme(base: Path, layer: str):
    content = LAYER_README.get(layer, "")
    if content:
        filepath = base / "_README_.md"
        filepath.write_text(content.strip() + "\n", encoding="utf-8")


def generate_test_structure(report: PyramidReport, output_dir: str = "generated_tests", ext: str = ".md"):
    """
    Gera a estrutura de pastas e arquivos stub de teste baseada no relatorio.
    
    Args:
        report: PyramidReport gerado pelo analisador
        output_dir: diretorio raiz onde os testes serao criados
        ext: extensao dos arquivos de teste (ex: .md, .spec.ts, .test.py)
    
    Returns:
        Caminho absoluto do diretorio raiz criado
    """
    feature_slug = _feature_slug(report)
    root_name = f"tests__{feature_slug}"
    root = Path(output_dir) / root_name

    if root.exists():
        import shutil
        shutil.rmtree(str(root))

    # Create layer dirs
    unit_dir = root / "unit"
    integration_dir = root / "integration"
    e2e_dir = root / "e2e"

    for d in [root, unit_dir, integration_dir, e2e_dir]:
        d.mkdir(parents=True, exist_ok=True)

    unit_count = 0
    integration_count = 0
    e2e_count = 0

    # --- Unit layer ---
    _write_layer_readme(unit_dir, "unit")
    for idx, suite in enumerate(report.layers[0].test_suites if len(report.layers) > 0 else []):
        try:
            _write_unit_stub(unit_dir, feature_slug, suite, idx)
            unit_count += 1
        except Exception as e:
            pass

    # --- Integration layer ---
    _write_layer_readme(integration_dir, "integration")
    if len(report.layers) > 1:
        for idx, suite in enumerate(report.layers[1].test_suites):
            try:
                _write_integration_stub(integration_dir, feature_slug, suite, idx)
                integration_count += 1
            except Exception as e:
                pass

    # --- E2E layer ---
    _write_layer_readme(e2e_dir, "e2e")
    if len(report.layers) > 2:
        for idx, suite in enumerate(report.layers[2].test_suites):
            try:
                _write_e2e_stub(e2e_dir, feature_slug, suite, idx)
                e2e_count += 1
            except Exception as e:
                pass

    # Root README
    root_readme = root / "_README_.md"
    root_readme_content = f"""# Test Suite: {report.feature.feature_name}

**Descricao:** {report.feature.summary}

## Estrutura

```
tests__{feature_slug}/
├── _README_.md          # Este arquivo
├── unit/                # Testes unitarios (70%)
│   ├── _README_.md
│   └── unit__*.md
├── integration/         # Testes de integracao (20%)
│   ├── _README_.md
│   └── integration__*.md
└── e2e/                 # Testes E2E (10%)
    ├── _README_.md
    └── e2e__*.md
```

## Convencao de nomenclatura

- `unit__<regra>.md` — Um arquivo por regra de negocio
- `integration__<dependencia>.md` — Um arquivo por dependencia externa
- `e2e__<fluxo>.md` — Um arquivo por fluxo de usuario

Regra geral: `{{camada}}__{{contexto}}.md`

## Estatisticas

| Camada | Arquivos |
|--------|----------|
| Unit | {unit_count} |
| Integration | {integration_count} |
| E2E | {e2e_count} |
| **Total** | **{unit_count + integration_count + e2e_count}** |
"""
    root_readme.write_text(root_readme_content.strip() + "\n", encoding="utf-8")

    return str(root.absolute())
