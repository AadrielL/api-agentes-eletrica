"""
Ferramentas Escopadas para os Agentes 1, 2, 4 e 5:
- SCOPE_NBR_TOOLS (Agente 1 - NBR 5410)
- SCOPE_GEO_PRICING (Agente 2 - Geolocalização por UF/Cidade)
- SCOPE_SAFETY_DIAGNOSTICS (Agente 4 - Diagnóstico de Falhas & NR-10)
- SCOPE_PROPOSAL_AUDITOR (Agente 5 - Argumentação Técnica Comercial p/ Cliente)
"""

import json
import math
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==============================================================================
# ESCOPO 1: SCOPE_NBR_TOOLS (Agente 1 - NBR 5410)
# ==============================================================================
def calcular_queda_tensao_nbr(
    potencia_watts: float,
    tensao_volts: float = 220.0,
    distancia_metros: float = 20.0,
    sistema: str = "MONOFASICO",
    finalidade: str = "TOMADAS_FORCA",
    limite_queda_pct: float = 4.0
) -> dict:
    rho = 0.0172
    fp = 0.92
    trifasico = sistema.upper() == "TRIFASICO"
    fator_circ = math.sqrt(3.0) if trifasico else 2.0
    corrente_ib = (
        potencia_watts / (math.sqrt(3.0) * tensao_volts * fp)
        if trifasico
        else potencia_watts / (tensao_volts * fp)
    )

    secoes = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0]
    iz_tab = [15.5, 21.0, 28.0, 36.0, 50.0, 68.0, 89.0, 110.0, 134.0, 171.0] if trifasico else [17.5, 24.0, 32.0, 41.0, 57.0, 76.0, 101.0, 125.0, 151.0, 192.0]
    disjuntores = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200]

    secao_min = 1.5 if finalidade.upper() == "ILUMINACAO" else 2.5
    delta_v_max = (limite_queda_pct / 100.0) * tensao_volts
    secao_queda = (fator_circ * rho * distancia_metros * corrente_ib * fp) / delta_v_max

    secao_escolhida = secoes[-1]
    iz_escolhido = iz_tab[-1]
    for s, iz in zip(secoes, iz_tab):
        if s >= secao_min and s >= secao_queda and iz >= corrente_ib:
            secao_escolhida = s
            iz_escolhido = iz
            break

    disj_in = next((d for d in disjuntores if d >= math.ceil(corrente_ib)), 200)
    if disj_in > iz_escolhido:
        for s, iz in zip(secoes, iz_tab):
            if iz >= disj_in and s >= secao_escolhida:
                secao_escolhida = s
                iz_escolhido = iz
                break

    queda_v = (fator_circ * rho * distancia_metros * corrente_ib * fp) / secao_escolhida
    queda_pct = (queda_v / tensao_volts) * 100.0

    return {
        "corrente_ib_amperes": round(corrente_ib, 2),
        "cabo_recomendado_mm2": secao_escolhida,
        "capacidade_iz_amperes": iz_escolhido,
        "disjuntor_din_amperes": disj_in,
        "queda_tensao_real_pct": round(queda_pct, 2),
        "conforme_nbr5410": queda_pct <= limite_queda_pct and corrente_ib <= disj_in <= iz_escolhido
    }


def dimensionar_ocupacao_eletroduto(bitola_mm2: float = 2.5, quantidade_cabos: int = 5) -> dict:
    diametros = {1.5: 3.0, 2.5: 3.6, 4.0: 4.2, 6.0: 4.9, 10.0: 6.2, 16.0: 7.4, 25.0: 9.2}
    d_ext = diametros.get(float(bitola_mm2), 4.2)
    area_cabos = math.pi * ((d_ext / 2.0) ** 2) * max(1, int(quantidade_cabos))
    limite = 0.53 if quantidade_cabos == 1 else (0.31 if quantidade_cabos == 2 else 0.40)

    conduites = [
        ("20mm (1/2\")", math.pi * (7.5 ** 2)),
        ("25mm (3/4\")", math.pi * (9.7 ** 2)),
        ("32mm (1\")", math.pi * (12.7 ** 2)),
        ("40mm (1.1/4\")", math.pi * (16.4 ** 2)),
        ("50mm (1.1/2\")", math.pi * (20.6 ** 2))
    ]
    escolhido, area_int = conduites[-1]
    for nome, a_int in conduites:
        if area_cabos <= a_int * limite:
            escolhido, area_int = nome, a_int
            break

    return {
        "eletroduto_recomendado": escolhido,
        "taxa_ocupacao_pct": round((area_cabos / area_int) * 100.0, 2),
        "limite_nbr5410_pct": limite * 100.0
    }


def dimensionar_qdc_idr_dps(carga_kw: float = 15.0, tensao_fn: float = 220.0, circuitos: int = 8) -> dict:
    polos = 1 if carga_kw <= 12 else (2 if carga_kw <= 25 else 3)
    modalidade = "Monofásico" if polos == 1 else ("Bifásico" if polos == 2 else "Trifásico")
    reserva = 2 if circuitos <= 6 else (3 if circuitos <= 12 else 4)
    return {
        "padrao_entrada": modalidade,
        "idr_recomendado": f"IDR {'Bipolar' if polos == 1 else 'Tetrapolar'} 63A / 30mA",
        "dps_recomendado": f"{polos + 1}x DPS Classe II 275V 20kA/45kA",
        "reserva_obrigatoria_circuitos": reserva
    }


# ==============================================================================
# ESCOPO 2: SCOPE_GEO_PRICING (Agente 2 - Geolocalização por UF/Cidade)
# ==============================================================================
def consultar_parametros_regiao_uf(uf: str = "TO", cidade: str = "Palmas") -> dict:
    caminho = os.path.join(BASE_DIR, "data_regional", uf.upper(), f"{cidade.lower().replace(' ', '_')}.json")
    if not os.path.exists(caminho):
        caminho = os.path.join(BASE_DIR, "data_regional", "TO", "palmas.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def estimar_orcamento_regional(uf: str, cidade: str, area_m2: float, com_infra: bool = True) -> dict:
    dados = consultar_parametros_regiao_uf(uf, cidade)
    regioes = dados.get("regioes_bairros", {})
    primeiro = next(iter(regioes.values())) if regioes else {}
    valor_m2 = float(
        primeiro.get("valor_m2_com_infra_medio" if com_infra else "valor_m2_sem_infra_medio", 45.0)
    )
    return {
        "concessionaria_local": dados.get("concessionaria"),
        "tensao_padrao_v": f"{dados.get('tensao_fase_neutro_v')}V / {dados.get('tensao_fase_fase_v')}V",
        "valor_m2_regional_brl": valor_m2,
        "mao_de_obra_estimada_brl": round(area_m2 * valor_m2, 2),
        "distribuidora_parceira": dados.get("distribuidora_parceira", {}).get("nome")
    }


# ==============================================================================
# ESCOPO 4: SCOPE_SAFETY_DIAGNOSTICS (Agente 4 - Diagnóstico de Campo & NR-10)
# ==============================================================================
def diagnosticar_falha_eletrica_campo(sintoma: str) -> dict:
    s = (sintoma or "").lower()
    if "idr" in s or "dr" in s or "fuga" in s:
        return {
            "diagnostico_provavel": "Atuação do IDR (30mA) por corrente de fuga à terra ou neutro compartilhado entre circuitos.",
            "passos_teste_campo": [
                "1. Desligue todos os disjuntores terminais e rearme o IDR. Se o IDR cair mesmo com os disjuntores abertos, a fuga está no barramento de neutro ou em um neutro invertido com o terra.",
                "2. Ligue um disjuntor por vez até identificar qual circuito provoca o desarme do IDR.",
                "3. Verifique se dois circuitos diferentes estão compartilhando o mesmo fio neutro (erro clássico em retorno de iluminação) ou se há umidade em caixas de passagem externas/chuveiro."
            ],
            "norma_referencia": "ABNT NBR 5410 item 5.1.3.2 (Seccionamento automático por dispositivo DR)"
        }
    if "aquec" in s or "cheiro" in s or "derret" in s:
        return {
            "diagnostico_provavel": "Sobreaquecimento por efeito Joule devido a mal contato (torque insuficiente no borne) ou subdimensionamento do condutor.",
            "passos_teste_campo": [
                "1. Meça a corrente real com alicate amperímetro e compare com a capacidade Iz do cabo (2,5mm² = 24A; 4mm² = 32A; 6mm² = 41A).",
                "2. Inspecione se há emenda por torção sem conector adequado ou falta de terminal tubular (ilhós) em cabo flexível conectado ao disjuntor.",
                "3. Substitua o trecho carbonizado do condutor e reaplique o torque firme nos bornes."
            ],
            "norma_referencia": "ABNT NBR 5410 item 6.2.8 (Conexões elétricas)"
        }
    return {
        "diagnostico_provavel": "Desarme de disjuntor termomagnético por sobrecarga térmica (atuação bimetálica lenta) ou curto-circuito (atuação magnética instantânea).",
        "passos_teste_campo": [
            "1. Se o disjuntor desarma na hora em que é ligado: há curto-circuito franco entre Fase-Neutro ou Fase-Terra. Teste continuidade/isolação com cargas desconectadas.",
            "2. Se o disjuntor desarma após 5 a 20 minutos de uso: é sobrecarga térmica ($I_B > I_N$). Meça a corrente com alicate amperímetro e verifique se o circuito atende equipamentos acima da potência projetada."
        ],
        "norma_referencia": "ABNT NBR 5410 item 5.3.4 (Proteção contra correntes de sobrecarga)"
    }


def gerar_checklist_nr10_loto() -> dict:
    return {
        "procedimento_nr10_6_passos": [
            "1. Seccionamento: Desligar o disjuntor geral ou do circuito correspondente.",
            "2. Impedimento de Reenergização (LOTO): Aplicar cadeado/bloqueio mecânico no disjuntor.",
            "3. Constatação da Ausência de Tensão: Testar com multímetro/detector de tensão calibrado entre Fase-Neutro, Fase-Terra e Fase-Fase.",
            "4. Instalação de Aterramento Temporário (quando aplicável em quadros principais).",
            "5. Proteção dos Elementos Energizados Adjacentes (barreiras isolantes).",
            "6. Sinalização de Segurança ('NÃO LIGUE - HOMENS TRABALHANDO')."
        ]
    }


# ==============================================================================
# ESCOPO 5: SCOPE_PROPOSAL_AUDITOR (Agente 5 - Argumentação p/ Cliente Final)
# ==============================================================================
def gerar_justificativa_tecnica_cliente(valor_total: float, area_m2: float, inclui_idr_dps: bool = True) -> dict:
    return {
        "argumento_whatsapp_cliente": (
            f"Olá! Esta proposta técnica para o seu imóvel de {area_m2:.0f}m² (Total: R$ {valor_total:,.2f}) "
            "foi dimensionada 100% dentro da Norma ABNT NBR 5410. Diferente de orçamentos improvisados que subdimensionam cabos, "
            "seu projeto garante: (1) circuitos independentes para climatização e chuveiros sem queda de tensão nem aquecimento na fiação; "
            + ("(2) proteção de vida com IDR 30mA contra choques elétricos e DPS contra queima de eletrodomésticos por surtos da rede; " if inclui_idr_dps else "")
            + "e (3) lista exata de materiais para cotação direta sem desperdício de rolos de fio."
        )
    }
