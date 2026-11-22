"""
Agente 1: AgenteNBR5410 (Microsserviço de Dimensionamento Normativo ABNT NBR 5410).
Rota Exclusiva: POST /api/agentes/nbr5410
Escopo RBAC: SCOPE_NBR_TOOLS
"""

from gateway.route_permissions import executar_ferramenta_protegida
from tools_scoped.all_scoped_tools import (
    calcular_queda_tensao_nbr,
    dimensionar_ocupacao_eletroduto,
    dimensionar_qdc_idr_dps
)

CATALOGO_NBR = {
    "calcular_queda_tensao_nbr": calcular_queda_tensao_nbr,
    "dimensionar_ocupacao_eletroduto": dimensionar_ocupacao_eletroduto,
    "dimensionar_qdc_idr_dps": dimensionar_qdc_idr_dps
}


def processar_agente_nbr5410(ferramenta: str, argumentos: dict) -> dict:
    alvo = ferramenta or "calcular_queda_tensao_nbr"
    return executar_ferramenta_protegida(
        id_agente="AGENTE_NBR5410",
        nome_ferramenta=alvo,
        catalogo_funcoes=CATALOGO_NBR,
        argumentos=argumentos
    )
