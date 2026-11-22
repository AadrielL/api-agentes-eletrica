"""
Agente 5: AgenteAuditorProposta (Microsserviço de Argumentação Técnica Comercial p/ Cliente Final).
Rota Exclusiva: POST /api/agentes/auditor-proposta
Escopo RBAC: SCOPE_PROPOSAL_AUDITOR
"""

from gateway.route_permissions import executar_ferramenta_protegida
from tools_scoped.all_scoped_tools import gerar_justificativa_tecnica_cliente

CATALOGO_PROPOSTA = {
    "gerar_justificativa_tecnica_cliente": gerar_justificativa_tecnica_cliente
}


def processar_agente_auditor_proposta(ferramenta: str, argumentos: dict) -> dict:
    alvo = ferramenta or "gerar_justificativa_tecnica_cliente"
    return executar_ferramenta_protegida(
        id_agente="AGENTE_AUDITOR_PROPOSTA",
        nome_ferramenta=alvo,
        catalogo_funcoes=CATALOGO_PROPOSTA,
        argumentos=argumentos
    )
