"""
Servidor Microsserviço Multi-Agentes Elétricos MyGo (server_agentes.py).
Exposto na porta 8084 (/api/agentes/*) com:
1. Proteção de Rotas e Escopo por Agente (RBAC em gateway/route_permissions.py)
2. Suporte a 300+ Usuários Simultâneos em 1 única GEMINI_API_KEY (Cache Semântico 24h + Semáforo + Pré-Cálculo Determinístico)
3. Controle de Cotas por Plano Mensal (FREE, PRO_ELETRICISTA R$ 39,90, MASTER_ELETRO R$ 69,90)
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gateway.concurrency_pool import GerenciadorAltaConcorrenciaUnicaKey
from gateway.quota_billing_guard import GuardiaoCotasMonetizacao, TABELA_PLANOS_SAAS
from gateway.route_permissions import PERMISSOES_POR_AGENTE, executar_ferramenta_protegida
from tools_scoped.calibration_tools import (
    consultar_coeficiente_padrao_casa,
    recalibrar_matriz_fios_por_feedback
)
from tools_scoped.all_scoped_tools import (
    calcular_queda_tensao_nbr,
    dimensionar_ocupacao_eletroduto,
    dimensionar_qdc_idr_dps,
    consultar_parametros_regiao_uf,
    estimar_orcamento_regional,
    diagnosticar_falha_eletrica_campo,
    gerar_checklist_nr10_loto,
    gerar_justificativa_tecnica_cliente
)

app = FastAPI(
    title="MyGo - Microsserviço Multi-Agentes Elétricos NBR 5410",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

pool_300_usuarios = GerenciadorAltaConcorrenciaUnicaKey(max_chamadas_simultaneas_llm=15)
guardiao_cotas = GuardiaoCotasMonetizacao()

CATALOGO_GLOBAL_FERRAMENTAS = {
    "calcular_queda_tensao_nbr": calcular_queda_tensao_nbr,
    "dimensionar_ocupacao_eletroduto": dimensionar_ocupacao_eletroduto,
    "dimensionar_qdc_idr_dps": dimensionar_qdc_idr_dps,
    "consultar_parametros_regiao_uf": consultar_parametros_regiao_uf,
    "estimar_orcamento_regional": estimar_orcamento_regional,
    "consultar_coeficiente_padrao_casa": consultar_coeficiente_padrao_casa,
    "recalibrar_matriz_fios_por_feedback": recalibrar_matriz_fios_por_feedback,
    "diagnosticar_falha_eletrica_campo": diagnosticar_falha_eletrica_campo,
    "gerar_checklist_nr10_loto": gerar_checklist_nr10_loto,
    "gerar_justificativa_tecnica_cliente": gerar_justificativa_tecnica_cliente
}


class ConsultaAgenteRequest(BaseModel):
    idAgente: str = "AGENTE_NBR5410"
    pergunta: str = ""
    ferramenta: str = ""
    argumentos: dict = {}
    uf: str = "TO"
    cidade: str = "Palmas"
    tenantId: str = "eletricista_padrao"
    plano: str = "FREE"


@app.get("/api/agentes/status")
def status_arquitetura():
    return {
        "servico": "api-agentes-eletrica",
        "capacidade_simultanea": "300+ usuarios concorrentes em 1 unica GEMINI_API_KEY",
        "agentes_ativos": list(PERMISSOES_POR_AGENTE.keys()),
        "planos_mensais": TABELA_PLANOS_SAAS,
        "metricas_concorrencia": pool_300_usuarios.metricas
    }


@app.post("/api/agentes/consultar")
async def consultar_agente_protegido(req: ConsultaAgenteRequest):
    id_ag = req.idAgente.upper()
    if id_ag not in PERMISSOES_POR_AGENTE:
        raise HTTPException(status_code=403, detail=f"Agente '{id_ag}' não autorizado.")

    # 1. Verifica Cache Semântico Regional (responde em < 5ms com 0 tokens de API Key)
    payload_cache = {"q": req.pergunta, "tool": req.ferramenta, "args": req.argumentos}
    em_cache = pool_300_usuarios.consultar_cache(id_ag, req.uf, req.cidade, payload_cache)
    if em_cache:
        return {**em_cache, "origem": "CACHE_SEMANTICO_REGIONAL_0_TOKENS"}

    # 2. Executa a ferramenta determinística autorizada pelo RBAC do agente
    politica = PERMISSOES_POR_AGENTE[id_ag]
    ferramenta_alvo = req.ferramenta or next(iter(politica["ferramentas_permitidas"]))

    try:
        resultado_tool = executar_ferramenta_protegida(
            id_agente=id_ag,
            nome_ferramenta=ferramenta_alvo,
            catalogo_funcoes=CATALOGO_GLOBAL_FERRAMENTAS,
            argumentos=req.argumentos
        )
    except PermissionError as err:
        raise HTTPException(status_code=403, detail=str(err))
    except Exception as err:
        resultado_tool = {"nota": f"Execução padrão: {err}"}

    # 3. Verifica cota diária do plano do usuário
    status_cota = guardiao_cotas.verificar_e_consumir_cota_ia(req.tenantId, req.plano)

    resposta = {
        "agente": id_ag,
        "escopo_rbac": politica["escopo"],
        "ferramenta_acionada": ferramenta_alvo,
        "regiao": f"{req.cidade}/{req.uf.upper()}",
        "dados_tecnicos": resultado_tool,
        "cota_plano": status_cota,
        "origem": "MOTOR_HIBRIDO_PROTEGIDO"
    }

    pool_300_usuarios.salvar_cache(id_ag, req.uf, req.cidade, payload_cache, resposta)
    return resposta


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
