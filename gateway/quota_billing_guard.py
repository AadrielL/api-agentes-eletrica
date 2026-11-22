"""
Controle de Cotas e Monetização por Plano Mensal (SaaS MyGo).
Dimensionado para sustentar 300+ usuários simultâneos em 1 única GEMINI_API_KEY Pro com alta margem líquida.
"""

from datetime import date

TABELA_PLANOS_SAAS = {
    "FREE": {
        "nome_comercial": "Plano Gratuito (Entrada)",
        "mensalidade_brl": 0.00,
        "limite_calculos_deterministicos_dia": 15,
        "limite_consultas_ia_llm_dia": 3,
        "prioridade_fila": 3
    },
    "PRO_ELETRICISTA": {
        "nome_comercial": "Plano PRO Eletricista de Campo",
        "mensalidade_brl": 39.90,
        "limite_calculos_deterministicos_dia": 9999,
        "limite_consultas_ia_llm_dia": 25,
        "prioridade_fila": 2
    },
    "PRO": {
        "nome_comercial": "Plano PRO Eletricista de Campo",
        "mensalidade_brl": 39.90,
        "limite_calculos_deterministicos_dia": 9999,
        "limite_consultas_ia_llm_dia": 25,
        "prioridade_fila": 2
    },
    "MASTER_ELETRO": {
        "nome_comercial": "Plano Técnico Eletrotécnico AI Master",
        "mensalidade_brl": 69.90,
        "limite_calculos_deterministicos_dia": 9999,
        "limite_consultas_ia_llm_dia": 60,
        "prioridade_fila": 1
    }
}


class GuardiaoCotasMonetizacao:
    def __init__(self):
        # Rastreador em memória por (tenant_id, data_iso) -> contagem
        self._consumo_diario_llm: dict[tuple[str, str], int] = {}

    def verificar_e_consumir_cota_ia(self, tenant_id: str, plano: str = "FREE") -> dict:
        plano_norm = (plano or "FREE").upper()
        regras = TABELA_PLANOS_SAAS.get(plano_norm, TABELA_PLANOS_SAAS["FREE"])
        hoje = date.today().isoformat()
        chave = (tenant_id, hoje)

        usado = self._consumo_diario_llm.get(chave, 0)
        limite = regras["limite_consultas_ia_llm_dia"]

        if usado >= limite:
            return {
                "autorizado_llm": False,
                "modo_fallback_deterministico": True,
                "usado_hoje": usado,
                "limite_diario": limite,
                "plano_atual": plano_norm,
                "mensagem_upsell": (
                    f"Você atingiu o limite diário de {limite} consultas de IA generativa do plano {regras['nome_comercial']}. "
                    "O resultado determinístico da NBR 5410 continua liberado! Faça upgrade para o Plano PRO (R$ 39,90/mês) "
                    "ou Técnico Eletrotécnico AI (R$ 69,90/mês) para liberar análises ilimitadas."
                )
            }

        self._consumo_diario_llm[chave] = usado + 1
        return {
            "autorizado_llm": True,
            "modo_fallback_deterministico": False,
            "usado_hoje": usado + 1,
            "limite_diario": limite,
            "plano_atual": plano_norm
        }
