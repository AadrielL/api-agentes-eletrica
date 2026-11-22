"""
Agente 3: AgenteCalibradorFios (Microsserviço de Aprendizado Empírico Pós-Obra por Padrão de Casa).
Rota Exclusiva: POST /api/agentes/calibrador-fios
Escopo RBAC: SCOPE_WIRE_LEARNING
"""

from gateway.route_permissions import executar_ferramenta_protegida
from tools_scoped.calibration_tools import (
    consultar_coeficiente_padrao_casa,
    recalibrar_matriz_fios_por_feedback
)

CATALOGO_CALIBRACAO = {
    "consultar_coeficiente_padrao_casa": consultar_coeficiente_padrao_casa,
    "recalibrar_matriz_fios_por_feedback": recalibrar_matriz_fios_por_feedback
}


def processar_agente_calibrador_fios(ferramenta: str, argumentos: dict) -> dict:
    alvo = ferramenta or "consultar_coeficiente_padrao_casa"
    return executar_ferramenta_protegida(
        id_agente="AGENTE_CALIBRADOR_FIOS",
        nome_ferramenta=alvo,
        catalogo_funcoes=CATALOGO_CALIBRACAO,
        argumentos=argumentos
    )
