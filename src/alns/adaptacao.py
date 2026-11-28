"""
Mecanismo Adaptativo do ALNS 

O que este módulo faz:
Controla a "inteligência" da roleta:
- Mantém os pesos de cada operador de destruição e de reparo.
- Sorteia os operadores proporcionalmente aos pesos (roleta).
- Distribui pontuações (sigma_1, sigma_2, sigma_3) conforme o resultado da iteração.
- Atualiza os pesos ao final de cada segmento usando o fator de reação (rho).
"""

import random


class GerenciadorAdaptativo:
    def __init__(
        self,
        nomes_destruicao: list[str],
        nomes_reparo: list[str],
        rho: float = 0.2,
        sigma_1: float = 33.0,
        sigma_2: float = 9.0,
        sigma_3: float = 3.0,
    ):
        self.nomes_dest = nomes_destruicao
        self.nomes_rep = nomes_reparo
        self.rho = rho  # Quanto o desempenho recente influencia o peso novo (0.2 = 20%)

        # Pontuações clássicas da literatura de ALNS
        self.sigma_1 = sigma_1  # Achou uma nova melhor solução global
        self.sigma_2 = sigma_2  # Melhorou a solução atual
        self.sigma_3 = sigma_3  # Era pior, mas foi aceita pelo critério do SA

        # Todo mundo começa com o mesmo peso 
        self.w_dest = [1.0] * len(nomes_destruicao)
        self.w_rep = [1.0] * len(nomes_reparo)

        # Zera os acumuladores do primeiro segmento
        self._zerar_segmento()

    def _zerar_segmento(self):
        self.pts_dest = [0.0] * len(self.nomes_dest)
        self.pts_rep = [0.0] * len(self.nomes_rep)
        self.usos_dest = [0] * len(self.nomes_dest)
        self.usos_rep = [0] * len(self.nomes_rep)

    def _roleta(self, pesos: list[float]) -> int:
        """Sorteia um índice com chance proporcional ao seu peso."""
        total = sum(pesos)
        r = random.uniform(0, total)
        acumulado = 0.0

        for idx, p in enumerate(pesos):
            acumulado += p
            if r <= acumulado:
                return idx
        return len(pesos) - 1

    def selecionar_operadores(self) -> tuple[int, int]:
        """Gira as duas roletas (destruição e reparo) e já contabiliza o uso."""
        idx_d = self._roleta(self.w_dest)
        idx_r = self._roleta(self.w_rep)

        self.usos_dest[idx_d] += 1
        self.usos_rep[idx_r] += 1
        return idx_d, idx_r

    def registrar_resultado(self, idx_d: int, idx_r: int, tipo: str):
        """Dá os pontos para o par de operadores usado nessa iteração."""
        if tipo == "melhor_global":
            pontos = self.sigma_1
        elif tipo == "melhor_atual":
            pontos = self.sigma_2
        elif tipo == "aceita_sa":
            pontos = self.sigma_3
        else:
            return  # Solução rejeitada não ganha nada

        self.pts_dest[idx_d] += pontos
        self.pts_rep[idx_r] += pontos

    def atualizar_pesos(self):
        """
        Chamado no fim de cada segmento (ex: a cada 50 iterações).
        Fórmula: w_novo = (1 - rho) * w_antigo + rho * (pontos / usos)
        """
        for i in range(len(self.w_dest)):
            if self.usos_dest[i] > 0:
                media = self.pts_dest[i] / self.usos_dest[i]
                self.w_dest[i] = (1 - self.rho) * self.w_dest[i] + self.rho * media

        for i in range(len(self.w_rep)):
            if self.usos_rep[i] > 0:
                media = self.pts_rep[i] / self.usos_rep[i]
                self.w_rep[i] = (1 - self.rho) * self.w_rep[i] + self.rho * media

        # Limpa pontos e usos para começar o próximo segmento do zero
        self._zerar_segmento()

    def resumo_pesos(self) -> dict:
        return {
            "destruicao": {nome: round(w, 2) for nome, w in zip(self.nomes_dest, self.w_dest)},
            "reparo": {nome: round(w, 2) for nome, w in zip(self.nomes_rep, self.w_rep)},
        }