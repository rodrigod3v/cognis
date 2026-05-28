import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BusinessRule:
    description: str
    category: str  # validation, logic, security, boundary, error, flow
    layer_hint: str  # unit, integration, e2e


@dataclass
class Entity:
    name: str
    attributes: List[str] = field(default_factory=list)


@dataclass
class Dependency:
    name: str
    type: str  # database, api, external_service, filesystem, cache, queue
    operations: List[str] = field(default_factory=list)


@dataclass
class UserFlow:
    description: str
    steps: List[str] = field(default_factory=list)
    is_critical: bool = False


@dataclass
class FeatureAnalysis:
    feature_name: str
    summary: str
    business_rules: List[BusinessRule] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    flows: List[UserFlow] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    error_scenarios: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


class AnalysisEngine:
    RULE_PATTERNS = [
        (r"(?:deve|must|shall|should|tem que|precisa|obrigatório)\s+(.+)", "rule"),
        (r"(?:não pode|cannot|must not|shall not|não deve)\s+(.+)", "restriction"),
        (r"(?:se|if|when|caso|quando)\s+(.+?)(?:então|then|deve|must)\s+(.+)", "conditional"),
        (r"(?:apenas|only|somente|exclusivamente)\s+(.+)", "restriction"),
        (r"(?:mínimo|minimum|maximo|maximum|máximo|limite|limit|boundary)\s+(.+)", "boundary"),
        (r"(?:error|erro|exception|falha|fail|failure)\s+(.+)", "error"),
    ]

    DEPENDENCY_KEYWORDS = {
        "database": ["database", "db", "banco", "sql", "nosql", "mongo", "postgres", "mysql",
                     "repository", "dao", "persist"],
        "api": ["api", "rest", "graphql", "endpoint", "http", "service"],
        "external_service": ["external", "externo", "third.party", "terceiro", "gateway",
                             "payment", "pagamento", "email", "sms", "notification"],
        "filesystem": ["file", "arquivo", "upload", "download", "csv", "pdf", "image", "fs"],
        "cache": ["cache", "caching"],
        "queue": ["queue", "fila", "message", "mensagem", "rabbit", "kafka", "sqs", "sns"],
    }

    def analyze(self, prompt: str) -> FeatureAnalysis:
        lines = [l.strip() for l in prompt.strip().split("\n") if l.strip()]

        feature_name = self._extract_feature_name(lines)
        summary = self._extract_summary(lines, feature_name)

        rules = self._extract_rules(prompt)
        entities = self._extract_entities(lines)
        dependencies = self._extract_dependencies(prompt)
        flows = self._extract_flows(lines)
        edge_cases = self._extract_edge_cases(lines)
        error_scenarios = self._extract_error_scenarios(lines, rules)
        inputs, outputs = self._extract_io(lines)

        rules = self._enrich_rules_with_layer_hint(rules)

        return FeatureAnalysis(
            feature_name=feature_name,
            summary=summary,
            business_rules=rules,
            entities=entities,
            dependencies=dependencies,
            flows=flows,
            edge_cases=edge_cases,
            error_scenarios=error_scenarios,
            inputs=inputs,
            outputs=outputs,
        )

    def _extract_feature_name(self, lines: List[str]) -> str:
        for line in lines:
            line_lower = line.lower()
            for prefix in ["funcionalidade:", "feature:", "função:", "funcao:", "funcao:", "o que testar:",
                           "o que será testado:", "testar:", "nome:", "função:"]:
                if line_lower.startswith(prefix):
                    return line.split(":", 1)[1].strip()
        return "Feature em análise"

    def _extract_summary(self, lines: List[str], feature_name: str) -> str:
        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith("descrição:") or line_lower.startswith("descricao:"):
                return line.split(":", 1)[1].strip()
        non_rule_lines = [l for l in lines if not any(
            l.lower().startswith(p) for p in
            ["funcionalidade:", "feature:", "função:", "funcao:", "testar:", "regra", "entrada", "saida", "saída",
             "descrição:", "descricao:"]
        ) and len(l) > 20]
        if non_rule_lines:
            return non_rule_lines[0]
        return f"Testes automatizados para {feature_name}"

    def _extract_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        lines = text.strip().split("\n")
        in_rules_block = False

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            if any(p in line_lower for p in ["regras de negócio:", "regras:", "business rules:",
                                              "regras de negocio:", "regras de negócio"]):
                in_rules_block = True
                continue
            if any(p in line_lower for p in ["entradas:", "entrada:", "inputs:", "saídas:", "saidas:",
                                              "outputs:", "fluxos:", "dependências:", "dependencias:"]):
                in_rules_block = False
                continue

            if in_rules_block and line_stripped and (
                    line_stripped.startswith("- ") or line_stripped.startswith("* ")
                    or line_stripped.startswith("\u2022") or line_stripped[0].isdigit()):
                rule_text = re.sub(r"^[\-\*\d\.\u2022\s]+", "", line_stripped).strip()
                category = self._classify_rule(rule_text)
                rules.append(BusinessRule(description=rule_text, category=category, layer_hint=""))
                continue

        if not rules:
            rules = self._fallback_extract_rules(text)

        return rules

    def _fallback_extract_rules(self, text: str) -> List[BusinessRule]:
        rules = []
        for pattern, category in self.RULE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if category == "conditional":
                    full_text = f"Quando {match.group(1).strip()}, então {match.group(2).strip()}"
                elif category in ("rule", "restriction", "boundary", "error"):
                    full_text = match.group(1).strip()
                else:
                    full_text = match.group(1).strip()

                cat = self._classify_rule(full_text)
                rules.append(BusinessRule(description=full_text, category=cat, layer_hint=""))

        seen = set()
        unique_rules = []
        for r in rules:
            if r.description.lower() not in seen:
                seen.add(r.description.lower())
                unique_rules.append(r)
        return unique_rules if unique_rules else [
            BusinessRule(description="Regra de negócio não especificada — analise o domínio manualmente",
                         category="logic", layer_hint="unit")
        ]

    def _classify_rule(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["validation", "validar", "validate", "válido", "valido", "formato",
                                "formato", "regex", "pattern", "obrigatório", "obrigatorio",
                                "required", "deve conter", "deve ser", "precisa ser"]):
            return "validation"
        if any(w in t for w in ["security", "segurança", "seguranca", "auth", "autenticação",
                                "autenticacao", "role", "permission", "permis", "acesso"]):
            return "security"
        if any(w in t for w in ["boundary", "limite", "limit", "mínimo", "minimum", "máximo",
                                "maximum", "maximo", "acima", "abaixo", "entre"]) or \
                re.search(r"\d+", text):
            return "boundary"
        if any(w in t for w in ["error", "erro", "exception", "falha", "fail", "failure"]):
            return "error"
        if any(w in t for w in ["fluxo", "flow", "navegação", "navegacao", "redirect",
                                "transição", "transicao", "encamin"]):
            return "flow"
        return "logic"

    def _extract_entities(self, lines: List[str]) -> List[Entity]:
        entities = []
        full_text = " ".join(lines)
        patterns = [
            r"(?:entidade|entity|objeto|model|class|schema|tabela|table)\s+['\"]?(\w+)['\"]?",
            r"(?:entidades|entities):\s*(.+?)(?:\.|$)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for m in matches:
                names = [x.strip() for x in re.split(r"[,;]\s*", m) if x.strip()]
                for name in names:
                    if name and name not in [e.name for e in entities]:
                        entities.append(Entity(name=name))
        if not entities:
            candidates = re.findall(
                r"(?:entidade|entity|objeto|model|domain)\s+(\w+)",
                full_text, re.IGNORECASE
            )
            for c in candidates:
                if c not in [e.name for e in entities]:
                    entities.append(Entity(name=c))
        if not entities:
            common_entities = ["Usuario", "Conta", "Sessao", "Token"]
            full_lower = full_text.lower()
            for ce in common_entities:
                ce_lower = ce.lower()
                if re.search(r"\b" + ce_lower + r"\b", full_lower):
                    entities.append(Entity(name=ce))
                    break
        return entities if entities else [Entity(name="Entidade principal (nao identificada)")]

    def _extract_dependencies(self, text: str) -> List[Dependency]:
        deps = []
        lower_text = text.lower()
        seen_names = set()

        dep_lines = []
        in_dep_block = False
        for line in text.strip().split("\n"):
            ls = line.strip().lower()
            if any(p in ls for p in ["dependências:", "dependencias:", "dependencies:",
                                      "dependente de:", "integra com:"]):
                in_dep_block = True
                continue
            if any(p in ls for p in ["fluxos:", "regras:", "entradas:", "saidas:"]):
                in_dep_block = False
                continue
            if in_dep_block and ls:
                dep_lines.append(line.strip())

        if dep_lines:
            for dl in dep_lines:
                dl_clean = re.sub(r"^[\-\*\d\.\u2022\s]+", "", dl).strip()
                dl_lower = dl_clean.lower() if dl_clean else ""
                if dl_lower and dl_lower not in seen_names:
                    seen_names.add(dl_lower)
                    dep_type = "external_service"
                    for dtype, keywords in self.DEPENDENCY_KEYWORDS.items():
                        if any(k in dl_lower for k in keywords):
                            dep_type = dtype
                            break
                    deps.append(Dependency(name=dl_clean, type=dep_type))
        else:
            found = set()
            for dep_type, keywords in self.DEPENDENCY_KEYWORDS.items():
                for kw in keywords:
                    if kw in lower_text and dep_type not in found:
                        found.add(dep_type)
                        ops = self._extract_operations(text, dep_type)
                        deps.append(Dependency(name=dep_type.replace("_", " ").title(), type=dep_type,
                                               operations=ops))
                        break

        return deps if deps else [Dependency(name="Nenhuma dependência externa identificada",
                                             type="external_service")]

    def _extract_operations(self, text: str, dep_type: str) -> List[str]:
        ops = []
        patterns = {
            "database": [r"(?:consultar|query|select|buscar|find|get|fetch)\s+\w+",
                         r"(?:inserir|insert|create|salvar|save|add)\s+\w+",
                         r"(?:atualizar|update|alterar|modify|edit)\s+\w+",
                         r"(?:deletar|delete|remover|remove)\s+\w+",
                         r"(?:listar|list|search|filtrar|filter)\s+\w+"],
            "api": [r"(?:GET|POST|PUT|DELETE|PATCH)\s+\/\S+",
                    r"(?:chamar|call|invocar|request|get|post)\s+\w+",
                    r"(?:consumir|consume|fetch)\s+\w+",
                    r"(?:webhook|callback)\s+\w+"],
        }
        for pat in patterns.get(dep_type, []):
            matches = re.findall(pat, text, re.IGNORECASE)
            ops.extend(m.strip() for m in matches)
        return ops[:5] if ops else ["Operações específicas não detalhadas"]

    def _extract_flows(self, lines: List[str]) -> List[UserFlow]:
        flows = []
        full_text = "\n".join(lines)
        lower = full_text.lower()

        flow_keywords = ["fluxo", "flow", "cenário", "cenario", "scenario", "user journey",
                         "jornada", "caminho", "path", "história", "historia", "story"]
        if any(k in lower for k in flow_keywords):
            flow_blocks = re.split(r"(?:fluxo|flow|cenário|scenario)\s*\d*\s*[:\-]?\s*", full_text,
                                   flags=re.IGNORECASE)
            for block in flow_blocks[1:]:
                first_line = block.strip().split("\n")[0].strip()
                first_line = re.sub(r"^(crítico|critico|critical|principal|main):?\s*", "", first_line, flags=re.IGNORECASE).strip()
                steps = [s.strip() for s in re.split(r"\n+", block) if s.strip() and
                         len(s.strip()) > 5][:8]
                if steps:
                    is_critical = any(k in block.lower() for k in
                                      ["crítico", "critico", "critical", "principal", "main",
                                       "core", "obrigatório", "obrigatorio"])
                    flows.append(UserFlow(
                        description=first_line[:80],
                        steps=steps,
                        is_critical=is_critical,
                    ))

        if not flows:
            if any(k in lower for k in ["login", "cadastro", "registro", "checkout",
                                         "pagamento", "payment", "signup", "signin"]):
                flows.append(UserFlow(
                    description="Fluxo principal identificado pelo contexto",
                    steps=["Ação inicial", "Processamento", "Validação", "Resultado esperado"],
                    is_critical=True,
                ))

        return flows

    def _extract_edge_cases(self, lines: List[str]) -> List[str]:
        full_text = " ".join(lines)
        cases = []
        patterns = [
            r"(?:caso limite|edge case|caso extremo|canto|exceção|excecao|excecional)\s*[:\-]?\s*(.+)",
            r"(?:quando\s+(.+?))\s*(?:então|deve|retorna|lança|throw)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    m = ": ".join(x.strip() for x in m if x.strip())
                cases.append(m.strip())

        specific_edge_keywords = [
            "campo vazio", "null", "undefined", "vazio", "empty",
            "valor negativo", "negative", "zero",
            "caractere especial", "special char", "string longa", "long string",
            "limite superior", "limite inferior", "upper bound", "lower bound",
            "formato inválido", "invalid format", "invalido",
        ]
        for kw in specific_edge_keywords:
            if kw in full_text.lower():
                cases.append(f"Testar caso: {kw}")

        return cases[:10] if cases else ["Identificar casos limite durante o desenvolvimento"]

    def _extract_error_scenarios(self, lines: List[str], rules: List[BusinessRule]) -> List[str]:
        errors = [r.description for r in rules if r.category == "error"]
        if not errors:
            full_text = " ".join(lines)
            patterns = [
                r"(?:quando\s+)(.+?erro\s*\w+)",
                r"(?:lançar|throw|retornar|return|exibir|show)\s+(?:erro|error|exception)\s*(.+?)(?:\.|,|$)",
                r"(?:sem\s+)(?:conexão|conexao|internet|acesso|rede)",
                r"(?:timeout|time.?out|falha\s+de\s+comunicação|falha\s+de\s+comunicacao)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                errors.extend(m.strip() for m in matches)
        return errors[:8] if errors else ["Cobrir cenários de falha comuns do domínio"]

    def _extract_io(self, lines: List[str]) -> (List[str], List[str]):
        inputs, outputs = [], []
        full_text = "\n".join(lines)
        section = None
        for line in full_text.split("\n"):
            ls = line.strip().lower()
            if any(p in ls for p in ["entradas:", "entrada:", "inputs:"]):
                section = "input"
                continue
            if any(p in ls for p in ["saídas:", "saidas:", "outputs:"]):
                section = "output"
                continue
            if section == "input":
                if any(p in ls for p in ["saídas:", "saidas:", "outputs:", "fluxos:", "regras:"]):
                    section = None
                    continue
                item = re.sub(r"^[\-\*\d\.•\s]+", "", line.strip()).strip()
                if item:
                    inputs.append(item)
            elif section == "output":
                if any(p in ls for p in ["regras:", "fluxos:", "dependências:", "dependencias:"]):
                    section = None
                    continue
                item = re.sub(r"^[\-\*\d\.•\s]+", "", line.strip()).strip()
                if item:
                    outputs.append(item)

        if not inputs:
            inputs.append("Parâmetros de entrada — especificar durante modelagem")
        if not outputs:
            outputs.append("Resultado esperado — especificar durante modelagem")

        return inputs, outputs

    def _enrich_rules_with_layer_hint(self, rules: List[BusinessRule]) -> List[BusinessRule]:
        for rule in rules:
            if rule.category in ("validation", "boundary", "error", "security"):
                rule.layer_hint = "unit"
            elif rule.category == "flow":
                rule.layer_hint = "e2e"
            else:
                rule.layer_hint = "unit"
        return rules
