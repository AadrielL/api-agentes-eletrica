# Microsserviço Multi-Agentes Elétricos MyGo (`api-agentes-eletrica`)

Microsserviço projetado para suportar **300+ usuários simultâneos utilizando uma única `GEMINI_API_KEY`**, com isolamento estrito de rotas e ferramentas por agente (*Principle of Least Privilege*), subdivisão de dados JSON por **Estado/Região (`UF/Cidade`)** e **Agente de Aprendizado e Calibração de Fios por Padrão Construtivo**.

---

## 1. Arquitetura de Pastas do Microsserviço

```text
C:\meus projetos\api-agentes-eletrica\
├── gateway/
│   ├── __init__.py
│   ├── concurrency_pool.py      # Semáforo (300 usuários -> fila assíncrona) + Cache Semântico Regional
│   ├── quota_billing_guard.py   # Controle de cotas por plano mensal (FREE, PRO_39, MASTER_69)
│   └── route_permissions.py     # Matriz RBAC: garante que cada Agente só acesse suas próprias Tools
│
├── agents/
│   ├── __init__.py
│   ├── agente_nbr5410.py        # [AGENTE 1] Dimensionamento técnico (Queda ΔV, Eletroduto, QDC, BTU/CV)
│   ├── agente_geolocalizacao.py # [AGENTE 2] Orçamento regionalizado por UF/Cidade/Concessionária
│   └── agente_calibrador_fios.py# [AGENTE 3] IA que aprende com feedback pós-obra (faltou/sobrou fio)
│
├── tools_scoped/
│   ├── __init__.py
│   ├── nbr_tools.py             # Ferramentas exclusivas do Agente 1 (SCOPE_NBR_TOOLS)
│   ├── geo_tools.py             # Ferramentas exclusivas do Agente 2 (SCOPE_GEO_PRICING)
│   └── calibration_tools.py     # Ferramentas exclusivas do Agente 3 (SCOPE_WIRE_LEARNING)
│
├── data_regional/               # JSONs subdivididos por Estado (UF), Cidade e Padrão de Construção
│   ├── padroes_construcao.json  # Coeficientes de metragem de fios por tipo de casa/laje/alvenaria
│   ├── TO/
│   │   └── palmas.json          # Energisa TO (220V/380V), bairros/quadras, preços médios e fatores
│   ├── GO/
│   │   └── goiania.json         # Equatorial GO (220V/380V), preços médios e fatores
│   └── SP/
│       └── sao_paulo.json       # Enel SP (127V/220V), preços médios e fatores
│
├── server_agentes.py            # API REST FastAPI (Porta 8084 / /svc/agentes)
├── requirements.txt
└── README.md
```
