from engine import FeatureAnalysis, BusinessRule, UserFlow, Dependency


class TestLayer:
    def __init__(self, name: str, description: str, framework_hints: list[str],
                 speed: str, quantity: str):
        self.name = name
        self.description = description
        self.framework_hints = framework_hints
        self.speed = speed
        self.quantity = quantity
        self.test_suites: list[TestSuite] = []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "framework_hints": self.framework_hints,
            "speed": self.speed,
            "quantity": self.quantity,
            "test_suites": [s.to_dict() for s in self.test_suites],
        }


class TestCase:
    def __init__(self, name: str, description: str, rule_ref: str = "",
                 input_data: str = "", expected: str = ""):
        self.name = name
        self.description = description
        self.rule_ref = rule_ref
        self.input_data = input_data
        self.expected = expected

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "rule_ref": self.rule_ref,
            "input_data": self.input_data,
            "expected": self.expected,
        }


class TestSuite:
    def __init__(self, name: str, description: str, test_cases: list[TestCase] = None):
        self.name = name
        self.description = description
        self.test_cases = test_cases or []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
        }


class PyramidReport:
    def __init__(self, feature: FeatureAnalysis):
        self.feature = feature
        self.layers: list[TestLayer] = []
        self._build()

    def _build(self):
        self._build_unit_layer()
        self._build_integration_layer()
        self._build_e2e_layer()

    def _build_unit_layer(self):
        layer = TestLayer(
            name="Unit Tests",
            description="Testam a menor unidade de código isoladamente (funções, métodos, regras puras)",
            framework_hints=["Jest (JS/TS)", "JUnit (Java/Kotlin)", "pytest (Python)",
                             "XCTest (iOS/Swift)", "Mocha (JS)", "Vitest (JS/TS)"],
            speed="Rapidos (ms)",
            quantity="Maior quantidade (70% da piramide)",
        )

        unit_rules = [r for r in self.feature.business_rules
                      if r.layer_hint == "unit" or r.category in ("validation", "boundary", "error")]

        if unit_rules:
            for rule in unit_rules:
                suite = TestSuite(
                    name=f"Regra: {rule.description[:50]}",
                    description=f"Categoria: {rule.category}",
                    test_cases=self._generate_unit_cases(rule),
                )
                layer.test_suites.append(suite)

        # Edge cases suite
        if self.feature.edge_cases and self.feature.edge_cases[0] != "Identificar casos limite durante o desenvolvimento":
            suite = TestSuite(
                name="Casos Limite (Edge Cases)",
                description="Testes de fronteira e cenários extremos",
                test_cases=[TestCase(
                    name=f"Edge: {ec[:60]}",
                    description=ec,
                    input_data="Valor no limite ou inválido",
                    expected="Comportamento esperado definido pela regra",
                ) for ec in self.feature.edge_cases],
            )
            layer.test_suites.append(suite)

        # Input validation suite
        if self.feature.inputs:
            suite = TestSuite(
                name="Validação de Entradas",
                description="Testes de validação dos parâmetros de entrada",
                test_cases=[TestCase(
                    name=f"Validar entrada: {inp[:50]}",
                    description=f"Testar formatos válidos e inválidos para: {inp}",
                    input_data=inp,
                    expected="Aceitar válidos, rejeitar inválidos",
                ) for inp in self.feature.inputs],
            )
            layer.test_suites.append(suite)

        if not layer.test_suites:
            layer.test_suites.append(TestSuite(
                name="Regras de Negócio",
                description="Testes unitários das regras de negócio",
                test_cases=[TestCase(
                    name="Teste unitário base",
                    description="Implementar conforme regras de negócio definidas",
                    expected="Comportamento esperado",
                )],
            ))

        self.layers.append(layer)

    def _build_integration_layer(self):
        layer = TestLayer(
            name="Integration Tests",
            description="Testam a interação entre componentes (DB, APIs, serviços externos)",
            framework_hints=["Supertest (JS)", "Spring Boot Test (Java)",
                             "pytest + pytest-postgresql (Python)", "Cypress Component Testing",
                             "WireMock (mock de APIs)", "TestContainers"],
            speed="Medios (segundos)",
            quantity="Quantidade moderada (20% da piramide)",
        )

        for dep in self.feature.dependencies:
            if dep.name == "Nenhuma dependência externa identificada":
                suite = TestSuite(
                    name="Contratos Internos",
                    description="Verificar comunicação entre módulos internos",
                    test_cases=[TestCase(
                        name="Contrato entre camadas",
                        description="Testar que as camadas se comunicam corretamente",
                        expected="Dados trafegam corretamente entre camadas",
                    )],
                )
                layer.test_suites.append(suite)
                continue

            suite_name = dep.type.replace("_", " ").title()
            suite = TestSuite(
                name=f"Integração com {suite_name}",
                description=f"Testar interação com {dep.name} ({', '.join(dep.operations[:3])})",
                test_cases=[
                    TestCase(
                        name=f"{dep.type.title()} - Operação básica",
                        description=f"Verificar operação padrão com {dep.name}",
                        input_data="Payload/dados de entrada",
                        expected="Resposta esperada do {0}".format(dep.name),
                    ),
                    TestCase(
                        name=f"{dep.type.title()} - Tratamento de falha",
                        description=f"Simular indisponibilidade/timeout de {dep.name}",
                        input_data="Cenário de falha simulado",
                        expected="Sistema trata graciosamente a falha",
                    ),
                    TestCase(
                        name=f"{dep.type.title()} - Dados inconsistentes",
                        description=f"Verificar comportamento com dados corrompidos de {dep.name}",
                        input_data="Dados inválidos/inconsistentes",
                        expected="Sistema lida sem quebrar",
                    ),
                ],
            )

            if any(r.category == "flow" for r in self.feature.business_rules):
                suite.test_cases.append(TestCase(
                    name="Fluxo integrado",
                    description="Testar fluxo completo envolvendo múltiplas dependências",
                    expected="Fluxo executa sem erros",
                ))

            layer.test_suites.append(suite)

        if not layer.test_suites:
            layer.test_suites.append(TestSuite(
                name="Integração Base",
                description="Testes de integração padrão",
                test_cases=[TestCase(
                    name="Teste de integração base",
                    description="Implementar conforme dependências identificadas",
                )],
            ))

        self.layers.append(layer)

    def _build_e2e_layer(self):
        layer = TestLayer(
            name="E2E Tests (End-to-End)",
            description="Testam o fluxo completo do sistema como um usuário real",
            framework_hints=["Cypress (Web)", "Playwright (Web)", "Detox (React Native)",
                             "Appium (Mobile)", "XCUITest (iOS)", "Espresso (Android)",
                             "Cypress + Mobile plugins"],
            speed="Lentos (minutos)",
            quantity="Menor quantidade (10% da piramide)",
        )

        if self.feature.flows:
            for flow in self.feature.flows:
                priority = "[CRITICO]" if flow.is_critical else "[Secundario]"
                suite = TestSuite(
                    name=f"E2E - {flow.description[:60]}",
                    description=f"{priority} | {len(flow.steps)} passos",
                    test_cases=[
                        TestCase(
                            name=f"Happy Path: {flow.description[:50]}",
                            description=f"Fluxo completo de {flow.description}",
                            input_data=" → ".join(flow.steps[:5]),
                            expected="Fluxo executado com sucesso até o final",
                        ),
                        TestCase(
                            name=f"Sad Path: {flow.description[:50]}",
                            description=f"Fluxo com falha durante: {flow.description}",
                            input_data="Cenário com erro em uma etapa",
                            expected="Usuário recebe feedback apropriado",
                        ),
                    ],
                )
                layer.test_suites.append(suite)
        else:
            layer.test_suites.append(TestSuite(
                name="Fluxo Principal",
                description="Jornada crítica do usuário",
                test_cases=[
                    TestCase(
                        name="Happy Path Principal",
                        description="Fluxo completo de sucesso — entrada → processamento → saída",
                        expected="Resultado esperado conforme especificação",
                    ),
                    TestCase(
                        name="Sad Path Principal",
                        description="Fluxo com erro — validação de falha e recuperação",
                        expected="Usuário recebe mensagem de erro clara e pode recuperar",
                    ),
                ],
            ))

        if self.feature.error_scenarios:
            suite = TestSuite(
                name="Cenários de Falha E2E",
                description="Testes de resiliência e recuperação",
                test_cases=[TestCase(
                    name=f"Falha: {es[:55]}",
                    description=es,
                    expected="Sistema não quebra e exibe erro amigável",
                ) for es in self.feature.error_scenarios],
            )
            layer.test_suites.append(suite)

        self.layers.append(layer)

    def _generate_unit_cases(self, rule: BusinessRule) -> list[TestCase]:
        cases = [
            TestCase(
                name=f"Happy Path - {rule.description[:40]}",
                description=f"Validar regra: {rule.description}",
                input_data="Dados válidos conforme regra",
                expected="Regra deve ser satisfeita",
            ),
            TestCase(
                name=f"Violation - {rule.description[:38]}",
                description=f"Testar violação da regra: {rule.description}",
                input_data="Dados que violam a regra",
                expected="Regra deve rejeitar / lançar exceção",
            ),
        ]

        if rule.category == "boundary":
            cases.append(TestCase(
                name="Limite - valor exato no boundary",
                description="Testar o valor exato do limite definido pela regra",
                input_data="Valor exatamente no limite",
                expected="Comportamento definido na fronteira",
            ))

        if rule.category == "security":
            cases.append(TestCase(
                name="Tentativa de acesso não autorizado",
                description="Testar que usuário sem permissão não acessa",
                input_data="Token/credencial inválida",
                expected="Acesso negado (401/403)",
            ))

        return cases

    def to_dict(self):
        return {
            "feature_name": self.feature.feature_name,
            "summary": self.feature.summary,
            "entities": [{"name": e.name, "attributes": e.attributes} for e in self.feature.entities],
            "dependencies": [{"name": d.name, "type": d.type, "operations": d.operations}
                             for d in self.feature.dependencies],
            "layers": [l.to_dict() for l in self.layers],
        }
