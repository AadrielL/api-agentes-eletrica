"""
Ferramentas Exclusivas do Agente 3 (AgenteCalibradorFios - SCOPE_WIRE_LEARNING).
Aprende continuamente com os feedbacks pós-obra dos eletricistas (se a metragem de cabos bateu,
faltou ou sobrou em cada padrão de casa e região) e ajusta automaticamente o fator de pré-definição.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_PADROES = os.path.join(BASE_DIR, "data_regional", "padroes_construcao.json")
CAMINHO_HISTORICO_FEEDBACK = os.path.join(BASE_DIR, "data_regional", "feedbacks_fios.jsonl")


def consultar_coeficiente_padrao_casa(
    padrao_casa: str,
    area_m2: float,
    uf: str = "TO",
    cidade: str = "Palmas"
) -> dict:
    """Retorna a pré-definição calibrada de fios (1.5mm², 2.5mm², 4.0mm², 6.0mm²) para o tipo de casa e região."""
    with open(CAMINHO_PADROES, "r", encoding="utf-8") as f:
        dados = json.load(f)

    padroes = dados.get("padroes_casa", {})
    item = padroes.get(padrao_casa.upper()) or padroes.get("CASA_PADRAO_MEDIO_LAJE")

    # Verifica fator regional do estado/cidade se existir
    caminho_cidade = os.path.join(BASE_DIR, "data_regional", uf.upper(), f"{cidade.lower()}.json")
    fator_regional = 1.0
    if os.path.exists(caminho_cidade):
        with open(caminho_cidade, "r", encoding="utf-8") as fc:
            dados_cid = json.load(fc)
            regioes = dados_cid.get("regioes_bairros", {})
            if regioes:
                primeiro = next(iter(regioes.values()))
                fator_regional = float(primeiro.get("fator_ajuste_fios_regional", 1.0))

    fator_ia = float(item.get("fator_calibrado_ia", 1.1))
    metragens_base = item.get("metragem_media_por_m2", {})

    estimativa_cabos_metros = {}
    for bitola, metros_por_m2 in metragens_base.items():
        bruto = area_m2 * float(metros_por_m2) * fator_ia * fator_regional
        # Arredonda para múltiplos práticos e sugere rolos fechados de 100m
        estimativa_cabos_metros[bitola] = {
            "metros_estimados_calibrados": round(bruto, 1),
            "rolos_100m_sugeridos": round(bruto / 100.0, 2)
        }

    return {
        "padrao_casa": padrao_casa.upper(),
        "descricao_padrao": item.get("nome"),
        "area_m2": area_m2,
        "regiao": f"{cidade}/{uf.upper()}",
        "fator_calibrado_ia_atual": fator_ia,
        "total_obras_aprendidas": item.get("total_feedbacks_validados", 0),
        "predefinicao_fios": estimativa_cabos_metros
    }


def recalibrar_matriz_fios_por_feedback(
    padrao_casa: str,
    area_m2: float,
    status_orcamento: str,
    metros_faltaram_ou_sobraram: float,
    metros_orcados_originalmente: float,
    comentario_eletricista: str = "",
    uf: str = "TO",
    cidade: str = "Palmas"
) -> dict:
    """
    Recebe o feedback real pós-obra do eletricista:
    - status_orcamento: 'BATEU_EXATO' | 'FALTOU_FIO' | 'SOBROU_FIO'
    - metros_faltaram_ou_sobraram: quantos metros faltaram (+) ou sobraram (-)
    Atualiza o 'fator_calibrado_ia' por Média Móvel Exponencial Ponderada (EMA com trava anti-outlier de ±15%).
    """
    with open(CAMINHO_PADROES, "r", encoding="utf-8") as f:
        dados = json.load(f)

    chave = padrao_casa.upper()
    if chave not in dados["padroes_casa"]:
        chave = "CASA_PADRAO_MEDIO_LAJE"

    item = dados["padroes_casa"][chave]
    fator_atual = float(item.get("fator_calibrado_ia", 1.1))
    n_anterior = int(item.get("total_feedbacks_validados", 10))

    orcado = max(50.0, float(metros_orcados_originalmente))
    delta = float(metros_faltaram_ou_sobraram)

    if status_orcamento.upper() == "FALTOU_FIO":
        razao_erro = (orcado + abs(delta)) / orcado
    elif status_orcamento.upper() == "SOBROU_FIO":
        razao_erro = max(0.85, (orcado - abs(delta)) / orcado)
    else:
        razao_erro = 1.0

    # Trava de segurança contra outliers (±15% por feedback individual)
    razao_limitada = min(1.15, max(0.85, razao_erro))

    # Taxa de aprendizado suave (EMA alpha = 0.15) para convergir com estabilidade
    alpha = 0.15
    novo_fator = round((1.0 - alpha) * fator_atual + (alpha * (fator_atual * razao_limitada)), 4)

    item["fator_calibrado_ia"] = novo_fator
    item["total_feedbacks_validados"] = n_anterior + 1

    with open(CAMINHO_PADROES, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    registro_log = {
        "timestamp": datetime.now().isoformat(),
        "uf": uf.upper(),
        "cidade": cidade,
        "padrao_casa": chave,
        "area_m2": area_m2,
        "status_orcamento": status_orcamento.upper(),
        "delta_metros": delta,
        "fator_anterior": fator_atual,
        "fator_novo_calibrado": novo_fator,
        "comentario": comentario_eletricista
    }
    with open(CAMINHO_HISTORICO_FEEDBACK, "a", encoding="utf-8") as fl:
        fl.write(json.dumps(registro_log, ensure_ascii=False) + "\n")

    return {
        "mensagem": "Matriz de fios recalibrada com sucesso pela IA!",
        "padrao_casa": chave,
        "fator_anterior": fator_atual,
        "fator_novo_calibrado": novo_fator,
        "total_obras_aprendidas": n_anterior + 1
    }
