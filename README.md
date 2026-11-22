# volleyball-ttp-fairness

# Escalonamento Otimizado com Justiça Competitiva para a Superliga Brasileira de Voleibol (SBV)

Este repositório contém a modelagem e o ambiente de simulação para o **Problema de Tabela-Horário de Jogos da Superliga Brasileira de Voleibol (SBV)**, integrando **custos logísticos (distância total de deslocamento)** e **justiça competitiva (*breaks* e efeito de *carryover*)**.

---

## 📌 Contextualização e Motivação

O agendamento de jogos em ligas profissionais de pontos corridos com turno e returno (*Double Round-Robin* — DRR) envolve desafios combinatórios complexos com forte impacto financeiro e esportivo:
1. **Dimensão Logística (Viagens):** As equipes percorrem milhares de quilômetros ao longo da temporada. Minimizar essas distâncias reduz custos operacionais e o desgaste físico dos atletas.
2. **Dimensão de Equidade (Justiça Competitiva):** Tabelas mal formuladas podem privilegiar certas equipes com longas sequências em casa ou criar desequilíbrios onde um time enfrenta repetidamente adversários desgastados por confrontos prévios contra equipes da elite.

### 💡 Lacuna da Literatura e Proposta deste Trabalho
A literatura recente focada na **Superliga Brasileira de Voleibol** tratou a otimização de calendários sob a perspectiva exclusivamente logística (minimização da distância total percorrida). Por outro lado, pesquisas voltadas ao **futebol profissional (Campeonato Brasileiro - Série A)** desenvolveram métodos robustos para balancear a justiça competitiva através de *breaks* e do efeito de *carryover*.

Este projeto une essas duas frentes: **aplicar os critérios de justiça competitiva do futebol ao contexto logístico da Superliga Brasileira de Voleibol**, construindo tabelas espelhadas que equilibrem a economia de transporte e a equidade do campeonato.

---

## 🎯 Definição do Problema e Métricas

Considera-se o torneio da **Superliga Masculina** com $n = 12$ equipes e $R = 22$ rodadas (11 no turno e 11 no returno espelhado com mando invertido).

### 1. Distância Total ($f_{\text{dist}}$)
Soma de todas as distâncias rodoviárias percorridas pelas 12 equipes ao longo das 22 rodadas:
* Início da temporada na cidade-sede.
* Deslocamento direto entre jogos fora consecutivos.
* Retorno à cidade-sede após cada sequência de jogos fora e ao final da última rodada.

### 2. Breaks ($f_{\text{breaks}}$)
Um *break* ocorre quando uma equipe joga duas vezes consecutivas como mandante (`Casa -> Casa`) ou duas vezes consecutivas como visitante (`Fora -> Fora`). O objetivo é estabilizar a sequência de mandos.

### 3. Efeito de Carryover ($f_{\text{coe}}$)
O *Carryover Effect* (COE) mede se um time $B$ enfrenta consistentemente adversários que acabaram de jogar contra um time $A$ na rodada anterior.
Calculado pela soma dos quadrados da matriz de *carryover* $C_{n \times n}$ (Métrica de Russell, 1980):
$$COE = \sum_{i=1}^{n} \sum_{j=1}^{n} c_{ij}^2$$
Quanto menor o COE, mais bem distribuída é a sequência de confrontos entre todas as equipes.

### 4. Restrições Operacionais
* **Limite de Jogos Consecutivos:** Máximo de $6$ jogos seguidos em casa ou fora por equipe.
* **Equilíbrio por Turno:** Diferença máxima de $6$ jogos entre mandos em casa e fora no turno e no returno.

---

## 📚 Base Teórica e Trabalhos Correlos (SBPO)

O projeto fundamenta-se nos seguintes trabalhos da literatura do Simpósio Brasileiro de Pesquisa Operacional (SBPO):

1. **Superliga de Vôlei — Base Logística:**
   * *Algoritmo Híbrido Iterated Local Search e Simulated Annealing para o Problema de Tabela-Horário de Jogos da Superliga Brasileira de Voleibol* (SBPO 2025): Estabeleceu a minimização de distâncias na SBV com abordagens ILS+SA.
   * *Algoritmo Genético Acoplado com Q-Learning e Multimineração para o Problema de Tabela-Horário de Jogos da Superliga Brasileira de Voleibol* (SBPO 2026): Estado da arte em otimização de distâncias na SBV utilizando meta-heurística híbrida (MDM-GA-QVND).

2. **Futebol Profissional — Base de Justiça Competitiva:**
   * *MIP Heurísticas para Geração Otimizada da Tabela do Campeonato Brasileiro de Futebol* (SBPO 2025): Introduziu o modelo MIP, *relax-and-fix* e ALNS focados na minimização de *breaks* e *carryover*.
   * *Geração Otimizada da Tabela do Campeonato Brasileiro de Futebol com Considerações de Justiça Competitiva entre as Equipes* (SBPO 2025): Formalizou os conceitos de equidade em ligas de pontos corridos.

3. **Logística e Otimização Combinatória:**
   * *Metaheurísticas Busca Tabu e ALNS no Problema do Caixeiro Viajante: Aplicação à Distribuição de Vacinas no Rio Grande do Norte* (SBPO 2025): Demonstrou a eficiência da modelagem de rotas e busca local em matrizes de distância.

---