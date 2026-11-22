"""
Agente 2: AgenteGeolocalizacao (Microsserviço de Inteligência Regional por UF/Cidade).
Rota Exclusiva: POST /api/agentes/regional
Escopo RBAC: SCOPE_GEO_PRICING
"""

from gateway.route_permissions import executar_ferramenta_protegida
from tools_scoped.all_scoped_tools import (
    consultar_parametros_regiao_uf,
    estimar_orcamento_regional
)

CATALOGO_GEO = {
    "consultar_parametros_regiao_uf": consultar_parametros_regiao_uf,
    "estimar_orcamento_regional": estimar_orcamento_regional
}


def processar_agente_geolocalizacao(ferramenta: str, argumentos: dict) -> dict:
    alvo = ferramenta or "consultar_parametros_regiao_uf"
    return executar_ferramenta_protegida(
        id_agente="AGENTE_GEOLOCALIZACAO",
        nome_ferramenta=alvo,
        catalogo_funcoes=CATALOGO_GEO,
        argumentos=argumentos
    )
