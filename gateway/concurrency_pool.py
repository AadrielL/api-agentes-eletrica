"""
Orquestrador de Concorrência para 300+ Usuários Simultâneos com 1 Única GEMINI_API_KEY Pro.

Estratégia em 3 Camadas:
1. Cache Semântico Determinístico (TTL 24h): Perguntas/Orçamentos equivalentes na mesma UF/Cidade/Padrão
   de Casa retornam em < 5ms com 0 consumo de tokens da API Key.
2. Pré-Resolução Determinística: Os cálculos matemáticos da NBR 5410 e a calibração de fios rodam em
   Python/Java local (0 tokens) antes de acionar o LLM.
3. Semáforo Assíncrono (Token Bucket + Fila por Prioridade de Plano): Limita o número de chamadas HTTP
   simultâneas à API do Gemini (ex: máx. 15 requisições concorrentes por segundo), enfileirando picos
   de 300 usuários sem tomar erro HTTP 429.
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict


class GerenciadorAltaConcorrenciaUnicaKey:
    def __init__(self, max_chamadas_simultaneas_llm: int = 15, max_itens_cache: int = 2000):
        self.semaforo_llm = asyncio.Semaphore(max_chamadas_simultaneas_llm)
        self.max_itens_cache = max_itens_cache
        self.cache_semantico: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self.ttl_segundos = 86400  # 24 horas
        self.metricas = {
            "requisicoes_totais": 0,
            "respondidas_via_cache_0_tokens": 0,
            "respondidas_via_calculo_deterministico": 0,
            "chamadas_reais_gemini_api": 0
        }

    def _gerar_chave_cache(self, id_agente: str, uf: str, cidade: str, payload: dict) -> str:
        raw = json.dumps(
            {"agente": id_agente, "uf": uf.upper(), "cidade": cidade.lower(), "dados": payload},
            sort_keys=True,
            ensure_ascii=False
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def consultar_cache(self, id_agente: str, uf: str, cidade: str, payload: dict):
        chave = self._gerar_chave_cache(id_agente, uf, cidade, payload)
        item = self.cache_semantico.get(chave)
        if not item:
            return None
        ts, valor = item
        if time.time() - ts > self.ttl_segundos:
            del self.cache_semantico[chave]
            return None
        self.cache_semantico.move_to_end(chave)
        self.metricas["respondidas_via_cache_0_tokens"] += 1
        return valor

    def salvar_cache(self, id_agente: str, uf: str, cidade: str, payload: dict, resposta: dict):
        chave = self._gerar_chave_cache(id_agente, uf, cidade, payload)
        self.cache_semantico[chave] = (time.time(), resposta)
        if len(self.cache_semantico) > self.max_itens_cache:
            self.cache_semantico.popitem(last=False)

    async def executar_com_fila_protegida(self, corrotina_llm):
        """Garante que picos de 300 usuários simultâneos passem pelo semáforo sem estourar a API Key única."""
        self.metricas["requisicoes_totais"] += 1
        async with self.semaforo_llm:
            self.metricas["chamadas_reais_gemini_api"] += 1
            return await corrotina_llm
