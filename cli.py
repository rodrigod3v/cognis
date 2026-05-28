#!/usr/bin/env python3
"""
test-pilot: Gerador de Arquitetura de Testes baseado na Piramide de Testes.

Uso:
    python cli.py "descreva a funcionalidade e regras aqui..."
    python cli.py --file prompt.txt
    python cli.py --interactive
"""

import argparse
import json
import sys
import os
from engine import AnalysisEngine
from pyramid import PyramidReport
from generator import generate_test_structure


def generate_markdown(report: PyramidReport) -> str:
    f = report.feature
    lines = []

    # Header
    lines.append(f"# Plano de Testes: {f.feature_name}\n")
    lines.append(f"> **Descricao:** {f.summary}\n")
    lines.append("---\n")

    # Entities & Dependencies summary
    lines.append("## Visao Geral\n")
    lines.append("| Item | Detalhes |")
    lines.append("|------|----------|")

    entities_str = ", ".join(e.name for e in f.entities)
    lines.append(f"| **Entidades** | {entities_str} |")

    deps_str = "; ".join(f"{d.name} ({d.type})" for d in f.dependencies)
    lines.append(f"| **Dependencias** | {deps_str} |")

    n_rules = len([r for r in f.business_rules if r.description != "Regra de negocio nao especificada"])
    lines.append(f"| **Regras** | {n_rules} identificadas |")
    lines.append(f"| **Fluxos** | {len(f.flows)} fluxos ({sum(1 for fl in f.flows if fl.is_critical)} criticos) |")
    lines.append("\n")

    # Inputs / Outputs
    lines.append("## Contrato\n")
    lines.append("**Entradas:**\n")
    for inp in f.inputs:
        lines.append(f"- `{inp}`")
    lines.append("\n**Saidas Esperadas:**\n")
    for out in f.outputs:
        lines.append(f"- `{out}`")
    lines.append("\n---\n")

    # Business rules
    lines.append("## Regras de Negocio\n")
    for i, rule in enumerate(f.business_rules, 1):
        badge = {"validation": "[VALIDACAO]", "logic": "[LOGICA]", "security": "[SEGURANCA]",
                 "boundary": "[LIMITE]", "error": "[ERRO]", "flow": "[FLUXO]"}.get(rule.category, "[REGRA]")
        lines.append(f"**RN{i}:** {badge} {rule.description}  ")
        lines.append(f"   *Categoria: `{rule.category}` | Camada sugerida: `{rule.layer_hint}`*  \n")
    lines.append("---\n")

    # Test Pyramid
    lines.append("## Piramide de Testes\n")
    lines.append("```")
    lines.append("          [E2E] (10%)")
    lines.append("        [Integracao] (20%)")
    lines.append("  [Unit] [Unit] [Unit] (70%)")
    lines.append("```\n")

    for layer_idx, layer in enumerate(report.layers, 1):
        lines.append(f"### {'='*60}")
        lines.append(f"### Camada {layer_idx}: {layer.name}")
        lines.append(f"**{layer.description}**  ")
        lines.append(f"- Velocidade: {layer.speed}  ")
        lines.append(f"- Quantidade: {layer.quantity}  ")
        lines.append(f"- Frameworks sugeridos: {', '.join(layer.framework_hints)}  \n")

        for suite in layer.test_suites:
            lines.append(f"#### {suite.name}")
            lines.append(f"_{suite.description}_  \n")

            if suite.test_cases:
                lines.append("| # | Test Case | Descricao | Entrada | Resultado Esperado |")
                lines.append("|---|-----------|-----------|---------|---------------------|")
                for tc_idx, tc in enumerate(suite.test_cases, 1):
                    desc = tc.description[:60] + "..." if len(tc.description) > 60 else tc.description
                    inp = tc.input_data[:40] + "..." if len(tc.input_data) > 40 else tc.input_data
                    exp = tc.expected[:40] + "..." if len(tc.expected) > 40 else tc.expected
                    lines.append(f"| {tc_idx} | `{tc.name[:45]}` | {desc} | {inp} | {exp} |")
            lines.append("")

    # Implementation checklist
    lines.append("---\n")
    lines.append("## Checklist de Implementacao\n")
    lines.append("""
### [Unit Tests]
- [ ] Mockar todas as dependencias externas
- [ ] Testar regras de negocio isoladamente
- [ ] Cobrir edge cases e validacoes
- [ ] Testar error handling
- [ ] Manter testes atomicos e independentes

### [Integration Tests]
- [ ] Usar banco de testes ou in-memory database
- [ ] Mockar APIs externas (WireMock / MSW / MockServer)
- [ ] Testar cenarios de falha de dependencias
- [ ] Validar contratos entre camadas
- [ ] Garantir cleanup entre testes

### [E2E Tests]
- [ ] Identificar jornadas criticas do usuario
- [ ] Escrever happy path primeiro
- [ ] Adicionar sad paths (erros, validacoes)
- [ ] Usar dados reais ou proximos do real
- [ ] Manter conjunto pequeno e focado
- [ ] Considerar CI/CD pipeline com paralelizacao
""")

    # Recommendations
    lines.append("\n## Recomendacoes\n")
    lines.append(f"""
- **Stack de testes:** {" + ".join(layer.framework_hints[0] for layer in report.layers if layer.framework_hints)} (ou similar)
- **Cobertura sugerida:** Minimo 80% unit, 60% integration, 100% dos fluxos criticos em E2E
- **CI/CD:** Integrar testes no pipeline com `npm test` / `pytest` / `gradle test`
- **Paralelizacao:** E2E tests devem rodar em paralelo para reduzir feedback time
""")

    return "\n".join(lines)


def interactive_mode():
    print("=== test-pilot | Gerador de Piramide de Testes ===\n")
    print("Cole a descricao da funcionalidade + regras de negocio.")
    print("Pressione Ctrl+Z (Enter) ou Ctrl+D quando terminar.\n")

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="test-pilot: Gera arquitetura de testes baseada na piramide de testes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python cli.py "Funcionalidade: Login. Regras: ..."
  python cli.py --file descricao.txt
  python cli.py --interactive
  python cli.py --json --file prompt.txt
        """,
    )
    parser.add_argument("prompt", nargs="?", help="Descricao da funcionalidade e regras de negocio")
    parser.add_argument("--file", "-f", help="Arquivo contendo o prompt")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interativo")
    parser.add_argument("--json", "-j", action="store_true", help="Saida em JSON")
    parser.add_argument("--output", "-o", help="Arquivo de saida (opcional)")
    parser.add_argument("--generate", "-g", action="store_true",
                        help="Gerar estrutura de pastas com stubs de teste")
    parser.add_argument("--gen-dir", default="generated_tests",
                        help="Diretorio de saida para --generate (default: generated_tests)")
    parser.add_argument("--ext", default=".md",
                        help="Extensao dos arquivos de teste (default: .md)")

    args = parser.parse_args()

    if args.interactive:
        prompt = interactive_mode()
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            prompt = fh.read()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(1)

    engine = AnalysisEngine()
    feature = engine.analyze(prompt)
    report = PyramidReport(feature)

    if args.generate:
        path = generate_test_structure(report, output_dir=args.gen_dir, ext=args.ext)
        print(f"Estrutura de testes criada em: {path}")

    if args.json:
        output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    else:
        output = generate_markdown(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Relatorio salvo em: {args.output}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
