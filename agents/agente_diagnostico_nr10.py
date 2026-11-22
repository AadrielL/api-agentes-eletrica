"""
Agente 4: AgenteDiagnosticoNR10 (Microsserviço de Diagnóstico de Panes em Campo e Segurança NR-10).
Rota Exclusiva: POST /api/agentes/diagnostico-nr10
Escopo RBAC: SCOPE_SAFETY_DIAGNOSTICS
"""

from gateway.route_permissions import executar_ferramenta_protegida
from tools_scoped.all_scoped_tools import (
    diagnosticar_falha_eletrica_campo,
    gerar_checklist_nr10_loto
)

CATALOGO_NR10 = {
    "diagnosticar_falha_eletrica_campo": diagnosticar_falha_eletrica_campo,
    "gerar_checklist_nr10_loto": gerar_checklist_nr10_loto
}


def processar_agente_diagnostico_nr10(ferramenta: str, argumentos: dict) -> dict:
    alvo = ferramenta or "diagnosticar_falha_eletrica_campo"
    return executar_ferramenta_protegida(
        id_agente="AGENTE_DIAGNOSTICO_NR10",
        nome_ferramenta=alvo,
        catalogo_funcoes=CATALOGO_NR10,
        argumentos=argumentos
    )
