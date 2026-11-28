# volleyball-ttp-fairness

# Escalonamento Otimizado com Justiça Competitiva para a Superliga Brasileira de Voleibol (SBV)

Este repositório contém a modelagem, a coleta de dados e a otimização para o **Problema de Tabela-Horário de Jogos da Superliga Brasileira de Voleibol (SBV)** (temporada Masculina 2024/25), unindo **eficiência logística (distância total percorrida)** e **justiça competitiva (*breaks* e efeito de *carryover*)**.

---

## 📌 Motivação e Proposta

A literatura recente voltada à **Superliga Brasileira de Voleibol** focou exclusivamente na minimização de distâncias de deslocamento, enquanto estudos sobre o **Campeonato Brasileiro de Futebol** avançaram na modelagem de critérios de justiça competitiva (*breaks* e *carryover*).

Este projeto une essas duas frentes: **aplicar os critérios de justiça competitiva do futebol ao problema logístico da Superliga de Vôlei**, gerando tabelas espelhadas (*Double Round-Robin*) para 12 equipes (22 rodadas) que equilibrem redução de viagens e equidade esportiva.

---

## 🛠️ Passo a Passo do Projeto

### 1. Coleta de Dados e Matriz de Distâncias (`scripts/1_gerar_instancia.py`)
Para garantir reprodutibilidade sem depender de APIs pagas, a matriz de distâncias reais foi construída automaticamente:
- **Geocodificação:** Consulta à API gratuita **Nominatim (OpenStreetMap)** para obter as coordenadas oficiais (latitude e longitude) dos municípios-sede das 12 equipes da Superliga Masculina 2024/25.
- **Distâncias Rodoviárias:** Consulta à API do **OSRM (Open Source Routing Machine)** para calcular as distâncias reais de estrada (em km), gerando a matriz simétrica $12 \times 12$ salva em `data/sbv_m_24_25.csv`.

### 2. Modelagem, Solução Inicial e Avaliação (`src/2_problema.py`)
- **Representação:** Matriz $22 \times 12$ (22 rodadas $\times$ 12 equipes), com times numerados de `1` a `12`. O sinal indica o mando de campo (`+j` = joga em casa contra `j`; `-j` = joga fora contra `j`).
- **Solução Inicial (Método do Polígono):** Gera um 1º turno válido de 11 rodadas e espelha os confrontos no 2º turno com mandos invertidos. Garante viabilidade imediata e poucos *breaks*, mas produz o pior caso estrutural de *carryover*.
- **Métricas Avaliadas:**
  - **Distância Total ($f_{\text{dist}}$):** Soma dos deslocamentos das 12 equipes (partindo de casa, viajando direto entre jogos fora consecutivos e retornando para casa ao fim das sequências e da temporada).
  - **Breaks ($f_{\text{breaks}}$):** Quantidade de sequências `Casa -> Casa` ou `Fora -> Fora` em rodadas consecutivas.
  - **Carryover Effect ($f_{\text{coe}}$):** Mede se uma equipe enfrenta repetidamente adversários vindos de confrontos contra um mesmo clube, calculado pela métrica de Russell (1980):
    $$COE = \sum_{i=1}^{n} \sum_{j=1}^{n} c_{ij}^2$$
- **Restrições Operacionais:** Máximo de **6 jogos consecutivos** em casa ou fora, e diferença máxima de **6 jogos** entre mandos em casa e fora em cada turno.

### 3. Função Objetivo Multiobjetivo (`src/2_problema.py`)
Como as três métricas possuem escalas diferentes, adotou-se a **soma ponderada com normalização Min-Max** (Miettinen, 1999; Armani et al., SBPO 2025) acrescida de penalidade para violações:

$$F(x) = w_d \cdot \tilde{D}(x) + w_b \cdot \tilde{B}(x) + w_c \cdot \tilde{C}(x) + P \cdot V(x)$$

Cada métrica $f(x)$ é colocada no intervalo $[0, 1]$ por meio de:

$$\tilde{f}(x) = \frac{f(x) - f^{\min}}{f^{\max} - f^{\min}}$$

Os limites estruturais $(f^{\min}, f^{\max})$ são calculados diretamente a partir da instância (sem valores arbitrários):
- **Distância Total:**
  - $D_{\min} = n \sum_{i=1}^{n} \min_{j \neq i} d_{ij}$ (limite inferior otimista baseado na menor viagem possível saindo de cada cidade).
  - $D_{\max} = 2 \sum_{i=1}^{n} \sum_{j=1}^{n} d_{ij}$ (pior caso logístico, indo e voltando para casa em todos os jogos fora).
- **Breaks:**
  - $B_{\min} = 2(n - 2) = 20$ (limite teórico inferior para torneio *round-robin* espelhado com $n = 12$).
  - $B_{\max} = n \cdot (R - 1) = 252$ (máximo absoluto de transições entre rodadas).
- **Carryover (COE):**
  - $C_{\min} = n \cdot (R - 1) = 252$ (limite teórico inferior caso todas as ocorrências ficassem distribuídas sem repetição).
  - $C_{\max} = 3372$ (pior caso estrutural de concentração, gerado pelo Método do Polígono para $n = 12$).

- **Pesos padrão (cenário equilibrado):** $w_d = w_b = w_c = 1/3$.
- **Penalidade:** $P = 100$ por violação ($V(x)$).

### 4. Meta-heurística: Simulated Annealing (`src/3_sa.py`)
Para otimizar a tabela preservando a estrutura espelhada válida, foi implementado um **Simulated Annealing (SA)** operando sobre **4 movimentos de vizinhança**:
1. **`swap_homes`:** Inverte o mando de campo de um confronto (e espelha no returno).
2. **`swap_rounds`:** Troca duas rodadas inteiras de posição.
3. **`swap_teams`:** Permuta o calendário completo de duas equipes.
4. **`partial_swap_rounds`:** Troca uma cadeia fechada de partidas entre duas rodadas (essencial para quebrar o padrão rígido de *carryover* do Método do Polígono).

---

## 📊 Resultados Preliminares (Superliga 2024/25)

Comparação entre a solução inicial (*baseline* do Método do Polígono) e a primeira execução do Simulated Annealing (`pesos = 1/3` cada, `seed = 42`, tempo de execução: **24,58s**):

| Métrica | Inicial (Polígono) | Melhor SA | Variação |
| :--- | :---: | :---: | :---: |
| **Distância Total (km)** | 168.349 | **129.896** | **-22,8%** (-38.453 km) |
| **Carryover (COE)** | 3.372 | **712** | **-78,9%** |
| **Breaks** | 30 | **70** | +40 *(trade-off esperado)* |
| **Violações** | 0 | **0** | 100% viável |
| **Função Objetivo (FO)** | 0,6667 | **0,3604** | **-45,9%** |

---

## 📁 Estrutura do Repositório e Execução

```text
volleyball-ttp-fairness/
├── data/
│   └── sbv_m_24_25.csv         # Matriz de distâncias rodoviárias (12x12)
├── scripts/
│   └── 1_gerar_instancia.py    # Coleta via Nominatim + OSRM
├── src/
│   ├── 2_problema.py           # Modelagem, Polígono, métricas e FO
│   └── 3_sa.py                 # Movimentos de vizinhança e Simulated Annealing
└── README.md