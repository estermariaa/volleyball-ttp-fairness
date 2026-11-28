"""
Módulo base do problema de escalonamento da Superliga Brasileira de Voleibol.

O que este código faz:
1. Carrega a matriz de distâncias rodoviárias entre as 12 equipes e guarda
   as regras do campeonato.
2. Gera uma tabela inicial válida usando o Método do Polígono: monta o 1º turno
   (11 rodadas) garantindo que todos se enfrentem uma vez e espelha os jogos
   para o 2º turno com os mandos invertidos.
3. Avalia qualquer tabela de jogos calculando as 3 métricas do projeto + restrições:
   - Distância Total (km): soma dos deslocamentos de todas as equipes na temporada.
   - Breaks: quantidade de vezes que um time joga 2 rodadas seguidas em casa ou fora.
   - Carryover (COE): mede se algum time fica "na cola" de um mesmo adversário
     rodada após rodada (quanto menor, mais equilibrada e justa é a tabela).
   - Violações: conta quantas regras de limite de mando foram quebradas.
"""

import numpy as np
import pandas as pd

class InstanciaSBV:
    """Armazena os dados da instância e os parâmetros do regulamento."""

    def __init__(self, caminho_csv: str, max_seguidos: int = 6, max_diff_turno: int = 6):
        df = pd.read_csv(caminho_csv, index_col=0)
        self.equipes = list(df.index)
        self.n = len(self.equipes)           # 12 equipes
        self.num_rodadas = 2 * (self.n - 1)  # 22 rodadas (11 ida + 11 volta)
        self.dist = df.to_numpy(dtype=int)   # Matriz 12x12
        self.max_seguidos = max_seguidos
        self.max_diff_turno = max_diff_turno

        # Limites (min, max) para normalização Min-Max dos 3 objetivos
        menores_saidas = np.sort(self.dist, axis=1)[:, 1]  
        self.dist_min = int(self.n * np.sum(menores_saidas))
        self.dist_max = int(2 * np.sum(self.dist))

        self.breaks_min = 2 * (self.n - 2)
        self.breaks_max = self.n * (self.num_rodadas - 1)

        self.coe_min = self.n * (self.num_rodadas - 1)
        self.coe_max = 3372


def gerar_solucao_inicial(n: int = 12) -> np.ndarray:
    """
    Gera uma tabela espelhada válida (22 x 12) usando o Método do Polígono.
    Convenção de valores na matriz (times numerados de 1 a n):
      +j -> time i joga EM CASA contra o time j
      -j -> time i joga FORA contra o time j
    """
    rodadas_turno = n - 1
    turno = np.zeros((rodadas_turno, n), dtype=int)
    times = list(range(1, n + 1))

    for r in range(rodadas_turno):
        for k in range(n // 2):
            t1 = times[k]
            t2 = times[n - 1 - k]

            # Alterna mando de campo para reduzir breaks na solução inicial
            if (k == 0 and r % 2 == 0) or (k > 0 and k % 2 == 1):
                casa, fora = t1, t2
            else:
                casa, fora = t2, t1

            turno[r, casa - 1] = fora
            turno[r, fora - 1] = -casa

        # Rotaciona os times no sentido horário mantendo o primeiro fixo
        times = [times[0]] + [times[-1]] + times[1:-1]

    # Volta espelhada: mesmos confrontos com mandos invertidos
    returno = -turno
    return np.vstack([turno, returno])


def avaliar_solucao(tabela: np.ndarray, inst: InstanciaSBV) -> dict:
    """
    Avalia uma tabela de jogos e retorna um dicionário com:
    distancia_km, breaks, carryover_coe e violacoes.
    """
    n = inst.n
    R = inst.num_rodadas
    dist_total = 0
    total_breaks = 0
    violacoes = 0

    # Distância Total, Breaks e Violações de Mando
    for i in range(n):
        local_atual = i  # Toda equipe começa a temporada em casa
        seq_casa = 0
        seq_fora = 0
        casa_t1, fora_t1 = 0, 0
        casa_t2, fora_t2 = 0, 0
        ultimo_mando = None  # True = Casa, False = Fora

        for r in range(R):
            jogo = tabela[r, i]
            em_casa = jogo > 0
            adversario = abs(jogo) - 1

            # Deslocamento até o local da partida
            local_jogo = i if em_casa else adversario
            dist_total += inst.dist[local_atual, local_jogo]
            local_atual = local_jogo

            # Contagem de breaks (Casa->Casa ou Fora->Fora)
            if ultimo_mando is not None and em_casa == ultimo_mando:
                total_breaks += 1
            ultimo_mando = em_casa

            # Controle de sequências e equilíbrio por turno
            if em_casa:
                seq_casa += 1
                seq_fora = 0
                if r < R // 2:
                    casa_t1 += 1
                else:
                    casa_t2 += 1
            else:
                seq_fora += 1
                seq_casa = 0
                if r < R // 2:
                    fora_t1 += 1
                else:
                    fora_t2 += 1

            if seq_casa > inst.max_seguidos:
                violacoes += 1
            if seq_fora > inst.max_seguidos:
                violacoes += 1

        # Retorno para casa ao final da última rodada
        dist_total += inst.dist[local_atual, i]

        # Checa diferença máxima entre jogos em casa e fora em cada turno
        if abs(casa_t1 - fora_t1) > inst.max_diff_turno:
            violacoes += 1
        if abs(casa_t2 - fora_t2) > inst.max_diff_turno:
            violacoes += 1

    # Carryover Effect (COE)
    # c[a, b] = quantas vezes um time enfrentou 'b' logo após enfrentar 'a'
    c = np.zeros((n, n), dtype=int)
    for i in range(n):
        for r in range(R - 1):
            adv_anterior = abs(tabela[r, i]) - 1
            adv_atual = abs(tabela[r + 1, i]) - 1
            c[adv_anterior, adv_atual] += 1

    carryover_coe = int(np.sum(c ** 2))

    return {
        "distancia_km": int(dist_total),
        "breaks": int(total_breaks),
        "carryover_coe": carryover_coe,
        "violacoes": int(violacoes),
    }

def calcular_funcao_objetivo(
    tabela: np.ndarray,
    inst: InstanciaSBV,
    pesos: tuple[float, float, float] = (1/3, 1/3, 1/3),
    penalidade: float = 100.0,
) -> tuple[float, dict]:
    """
    Calcula a função objetivo escalarizada (soma ponderada Min-Max) + penalidade.
    pesos = (w_distancia, w_breaks, w_carryover)
    Retorna: (valor_objetivo, dicionario_metricas)
    """
    m = avaliar_solucao(tabela, inst)

    d_norm = (m["distancia_km"] - inst.dist_min) / (inst.dist_max - inst.dist_min)
    b_norm = (m["breaks"] - inst.breaks_min) / (inst.breaks_max - inst.breaks_min)
    c_norm = (m["carryover_coe"] - inst.coe_min) / (inst.coe_max - inst.coe_min)

    w_d, w_b, w_c = pesos
    custo = (w_d * d_norm) + (w_b * b_norm) + (w_c * c_norm) + (penalidade * m["violacoes"])

    m["d_norm"] = round(d_norm, 4)
    m["b_norm"] = round(b_norm, 4)
    m["c_norm"] = round(c_norm, 4)
    m["objetivo"] = round(custo, 4)

    return custo, m


if __name__ == "__main__":
    inst = InstanciaSBV("../data/sbv_m_24_25.csv")
    solucao = gerar_solucao_inicial(inst.n)
    custo, metricas = calcular_funcao_objetivo(solucao, inst)

    print("Avaliação da Solução Inicial (Método do Polígono):")
    for k, v in metricas.items():
        print(f"  {k}: {v}")