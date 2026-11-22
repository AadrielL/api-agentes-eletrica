"""
Matriz de Controle de Acesso Baseado em Escopo (RBAC de Agentes - 5 Agentes Especializados).
Garante que cada Agente só consiga invocar as funções autorizadas para sua rota específica.
"""

PERMISSOES_POR_AGENTE = {
    "AGENTE_NBR5410": {
        "rota_permitida": "/api/agentes/nbr5410",
        "escopo": "SCOPE_NBR_TOOLS",
        "descricao": "Dimensionamento técnico de condutores, queda de tensão, eletrodutos e QDC pela ABNT NBR 5410.",
        "ferramentas_permitidas": frozenset([
            "calcular_queda_tensao_nbr",
            "dimensionar_ocupacao_eletroduto",
            "dimensionar_qdc_idr_dps"
        ]),
        "planos_autorizados": frozenset(["FREE", "PRO_ELETRICISTA", "MASTER_ELETRO", "PRO"])
    },
    "AGENTE_GEOLOCALIZACAO": {
        "rota_permitida": "/api/agentes/regional",
        "escopo": "SCOPE_GEO_PRICING",
        "descricao": "Inteligência regional por UF/Cidade: concessionária, tensão local, fator térmico e preços por m².",
        "ferramentas_permitidas": frozenset([
            "consultar_parametros_regiao_uf",
            "estimar_orcamento_regional"
        ]),
        "planos_autorizados": frozenset(["FREE", "PRO_ELETRICISTA", "MASTER_ELETRO", "PRO"])
    },
    "AGENTE_CALIBRADOR_FIOS": {
        "rota_permitida": "/api/agentes/calibrador-fios",
        "escopo": "SCOPE_WIRE_LEARNING",
        "descricao": "Aprendizado empírico pós-obra: calibra a metragem de cabos por padrão construtivo de casa.",
        "ferramentas_permitidas": frozenset([
            "consultar_coeficiente_padrao_casa",
            "recalibrar_matriz_fios_por_feedback"
        ]),
        "planos_autorizados": frozenset(["FREE", "PRO_ELETRICISTA", "MASTER_ELETRO", "PRO"])
    },
    "AGENTE_DIAGNOSTICO_NR10": {
        "rota_permitida": "/api/agentes/diagnostico-nr10",
        "escopo": "SCOPE_SAFETY_DIAGNOSTICS",
        "descricao": "Diagnóstico de panes em campo (desarme de IDR/disjuntor, fuga à terra, aquecimento) e checklist NR-10.",
        "ferramentas_permitidas": frozenset([
            "diagnosticar_falha_eletrica_campo",
            "gerar_checklist_nr10_loto"
        ]),
        "planos_autorizados": frozenset(["PRO_ELETRICISTA", "MASTER_ELETRO", "PRO", "FREE"])
    },
    "AGENTE_AUDITOR_PROPOSTA": {
        "rota_permitida": "/api/agentes/auditor-proposta",
        "escopo": "SCOPE_PROPOSAL_AUDITOR",
        "descricao": "Gera argumentação técnica persuasiva (NBR 5410) para o cliente final aprovar o orçamento no WhatsApp.",
        "ferramentas_permitidas": frozenset([
            "gerar_justificativa_tecnica_cliente"
        ]),
        "planos_autorizados": frozenset(["PRO_ELETRICISTA", "MASTER_ELETRO", "PRO", "FREE"])
    }
}


class ViolacaoEscopoAgenteError(PermissionError):
    """Lançada quando um agente tenta executar uma ferramenta fora do seu escopo de rota."""


def executar_ferramenta_protegida(
    id_agente: str,
    nome_ferramenta: str,
    catalogo_funcoes: dict,
    argumentos: dict
):
    """Verifica se o agente tem permissão explícita para a ferramenta antes de invocá-la."""
    politica = PERMISSOES_POR_AGENTE.get(id_agente)
    if not politica:
        raise ViolacaoEscopoAgenteError(f"Agente '{id_agente}' não registrado na matriz de segurança.")

    if nome_ferramenta not in politica["ferramentas_permitidas"]:
        raise ViolacaoEscopoAgenteError(
            f"BLOQUEIO DE SEGURANÇA: O agente '{id_agente}' tentou acessar '{nome_ferramenta}', "
            f"mas seu escopo ({politica['escopo']}) permite apenas: {sorted(politica['ferramentas_permitidas'])}."
        )

    func = catalogo_funcoes.get(nome_ferramenta)
    if not func:
        raise KeyError(f"Ferramenta '{nome_ferramenta}' não encontrada no catálogo.")

    return func(**argumentos)
