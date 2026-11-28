"""
Testes Preliminares do ALNS 

O que este script faz:
Executa o ALNS modularizado em um conjunto selecionado de temporadas da Superliga
(Masculina e Feminina), compara cada uma com a solução inicial do Método do Polígono
e imprime uma tabela resumida
"""

import os
from problema import InstanciaSBV, calcular_funcao_objetivo, gerar_solucao_inicial
from alns import executar_alns


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")

    instancias_teste = [
        "sbv_m_24_25.csv",
        "sbv_f_24_25.csv",
        "sbv_m_21_22.csv",
        "sbv_m_26_27.csv",
    ]

    print(f"{'Instância':<16} | {'FO Polígono':>11} | {'FO ALNS':>8} | {'Ganho':>7} | {'Dist (km)':>10} | {'Breaks':>6} | {'COE':>5} | {'Tempo':>6}")
    print("-" * 88)

    for arquivo in instancias_teste:
        caminho = os.path.join(data_dir, arquivo)
        inst = InstanciaSBV(caminho)
        sol_inicial = gerar_solucao_inicial(inst.n)

        # Avalia o baseline (Polígono)
        _, met_ini = calcular_funcao_objetivo(sol_inicial, inst)

        # Roda o ALNS
        _, met_alns, tempo, pesos = executar_alns(
            inst,
            sol_inicial,
            calcular_funcao_objetivo,
            pesos_fo=(1 / 3, 1 / 3, 1 / 3),
            max_iter=1200,
            seed=42,
        )

        ganho_pct = (1.0 - met_alns["objetivo"] / met_ini["objetivo"]) * 100

        print(
            f"{arquivo:<16} | "
            f"{met_ini['objetivo']:>11.4f} | "
            f"{met_alns['objetivo']:>8.4f} | "
            f"{ganho_pct:>6.1f}% | "
            f"{met_alns['distancia_km']:>10d} | "
            f"{met_alns['breaks']:>6d} | "
            f"{met_alns['carryover_coe']:>5d} | "
            f"{tempo:>5.1f}s"
        )


if __name__ == "__main__":
    main()