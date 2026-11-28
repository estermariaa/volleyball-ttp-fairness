"""
Gerador em lote das matrizes de distâncias rodoviárias (12x12) para todas as
temporadas da Superliga Brasileira de Voleibol (Masculina e Feminina, 2020/21 a 2026/27).

O que este código faz:
1. Mapeia cada equipe para sua cidade-sede oficial na respectiva temporada.
2. Consulta a API Nominatim (OSM) apenas uma vez por cidade única e salva em cache
   (data/cidades_coords.json) para evitar bloqueios e acelerar reexecuções.
3. Consulta a API OSRM (Table Service) para montar a matriz 12x12 de distâncias
   rodoviárias reais (em km) de cada uma das 14 temporadas em data/sbv_*.csv.
"""

import json
import os
import time
import numpy as np
import pandas as pd
import requests

TEMPORADAS = {
    "sbv_f_20_21": [
        ("Minas", "Belo Horizonte, MG"),
        ("Osasco", "Osasco, SP"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Barueri", "Barueri, SP"),
        ("Curitiba Vôlei", "Curitiba, PR"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Pinheiros", "São Paulo, SP"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("São José dos Pinhais", "São José dos Pinhais, PR"),
        ("São Caetano EC", "São Caetano do Sul, SP"),
    ],
    "sbv_m_20_21": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Vôlei Taubaté", "Taubaté, SP"),
        ("Vôlei Renata", "Campinas, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("APAN Blumenau", "Blumenau, SC"),
        ("Academia do Vôlei", "Uberlândia, MG"),
        ("América", "Montes Claros, MG"),
        ("Vôlei Itapetininga", "Itapetininga, SP"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("Sesi-SP", "São Paulo, SP"),
        ("Caramuru", "Castro, PR"),
        ("Vôlei Ribeirão", "Ribeirão Preto, SP"),
    ],
    "sbv_f_21_22": [
        ("Praia Clube", "Uberlândia, MG"),
        ("Minas", "Belo Horizonte, MG"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Osasco", "Osasco, SP"),
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Barueri", "Barueri, SP"),
        ("Pinheiros", "São Paulo, SP"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Sancor Seguros", "Maringá, PR"),
        ("Renata Valinhos", "Valinhos, SP"),
        ("Curitiba Vôlei", "Curitiba, PR"),
    ],
    "sbv_m_21_22": [
        ("Minas", "Belo Horizonte, MG"),
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Sesi-SP", "São Paulo, SP"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("APAN Blumenau", "Blumenau, SC"),
        ("Vôlei Renata", "Campinas, SP"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Funvic Natal", "Natal, RN"),
        ("América", "Montes Claros, MG"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Goiás", "Goiânia, GO"),
        ("Academia do Vôlei", "Uberlândia, MG"),
    ],
    "sbv_f_22_23": [
        ("Praia Clube", "Uberlândia, MG"),
        ("Osasco", "Osasco, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Pinheiros", "São Paulo, SP"),
        ("Barueri", "Barueri, SP"),
        ("Sancor Seguros", "Maringá, PR"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("São Caetano EC", "São Caetano do Sul, SP"),
        ("Abel Moda", "Brusque, SC"),
    ],
    "sbv_m_22_23": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Vôlei Renata", "Campinas, SP"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Sesi-SP", "São Paulo, SP"),
        ("Suzano Vôlei", "Suzano, SP"),
        ("APAN Blumenau", "Blumenau, SC"),
        ("Araguari Vôlei", "Araguari, MG"),
        ("América", "Montes Claros, MG"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Rede Cuca", "Fortaleza, CE"),
    ],
    "sbv_f_23_24": [
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Osasco", "Osasco, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Pinheiros", "São Paulo, SP"),
        ("Barueri", "Barueri, SP"),
        ("Sancor Seguros", "Maringá, PR"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Blumenau", "Blumenau, SC"),
        ("São Caetano EC", "São Caetano do Sul, SP"),
    ],
    "sbv_m_23_24": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Sesi Bauru", "Bauru, SP"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Araguari Vôlei", "Araguari, MG"),
        ("Joinville Vôlei", "Joinville, SC"),
        ("Vôlei Renata", "Campinas, SP"),
        ("Suzano Vôlei", "Suzano, SP"),
        ("APAN Blumenau", "Blumenau, SC"),
        ("Academia do Vôlei", "Monte Carmelo, MG"),
        ("América", "Montes Claros, MG"),
    ],
    "sbv_f_24_25": [
        ("Praia Clube", "Uberlândia, MG"),
        ("Minas", "Belo Horizonte, MG"),
        ("Osasco", "Osasco, SP"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Barueri", "Barueri, SP"),
        ("Sancor Seguros", "Maringá, PR"),
        ("Batavo Mackenzie", "Belo Horizonte, MG"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Pinheiros", "São Paulo, SP"),
        ("Abel Moda", "Brusque, SC"),
    ],
    "sbv_m_24_25": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Minas", "Belo Horizonte, MG"),
        ("Vôlei Renata", "Campinas, SP"),
        ("Sesi Bauru", "Bauru, SP"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Joinville Vôlei", "Joinville, SC"),
        ("Suzano Vôlei", "Suzano, SP"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Goiás", "Goiânia, GO"),
        ("APAN Blumenau", "Blumenau, SC"),
        ("Neurologia Ativa", "Goiânia, GO"),
    ],
    "sbv_f_25_26": [
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Minas", "Belo Horizonte, MG"),
        ("Osasco", "Osasco, SP"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Sancor Seguros", "Maringá, PR"),
        ("Batavo Mackenzie", "Belo Horizonte, MG"),
        ("Brasília Vôlei", "Brasília, DF"),
        ("Barueri", "Barueri, SP"),
        ("Tijuca", "Rio de Janeiro, RJ"),
        ("Renasce Vôlei Sorocaba", "Sorocaba, SP"),
    ],
    "sbv_m_25_26": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Vôlei Renata", "Campinas, SP"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Minas", "Belo Horizonte, MG"),
        ("Suzano Vôlei", "Suzano, SP"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("Academia do Vôlei", "Monte Carmelo, MG"),
        ("Goiás", "Goiânia, GO"),
        ("Sesi Bauru", "Bauru, SP"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Joinville Vôlei", "Joinville, SC"),
        ("JF Vôlei", "Juiz de Fora, MG"),
    ],
    "sbv_f_26_27": [
        ("Sesc RJ Flamengo", "Rio de Janeiro, RJ"),
        ("Vôlei Bauru", "Bauru, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Praia Clube", "Uberlândia, MG"),
        ("Osasco", "Osasco, SP"),
        ("Abel Moda", "Brusque, SC"),
        ("Pinheiros", "São Paulo, SP"),
        ("Batavo Mackenzie", "Belo Horizonte, MG"),
        ("Fluminense", "Rio de Janeiro, RJ"),
        ("Barueri", "Barueri, SP"),
        ("Sancor Seguros", "Londrina, PR"),
        ("Brasília Vôlei", "Brasília, DF"),
    ],
    "sbv_m_26_27": [
        ("Sada Cruzeiro", "Contagem, MG"),
        ("Vôlei Renata", "Campinas, SP"),
        ("Minas", "Belo Horizonte, MG"),
        ("Praia Clube", "Uberlândia, MG"),
        ("São José Vôlei", "São José dos Campos, SP"),
        ("Sesi Bauru", "Bauru, SP"),
        ("Montes Claros", "Montes Claros, MG"),
        ("Suzano Vôlei", "Suzano, SP"),
        ("Academia do Vôlei", "Monte Carmelo, MG"),
        ("Vôlei Guarulhos", "Guarulhos, SP"),
        ("Norde Vôlei", "Fortaleza, CE"),
        ("Goiás", "Goiânia, GO"),
    ],
}


def geocodificar_cidades(cidades_unicas: set[str], caminho_cache: str) -> dict:
    """Busca (lat, lon) no Nominatim apenas para cidades que ainda não estão no cache."""
    if os.path.exists(caminho_cache):
        with open(caminho_cache, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    headers = {"User-Agent": "volleyball-ttp-fairness-ufsj/1.0"}
    faltantes = sorted(c for c in cidades_unicas if c not in cache)

    if faltantes:
        print(f"Geocodificando {len(faltantes)} cidades novas via Nominatim...")

    for cidade in faltantes:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{cidade}, Brasil", "format": "json", "limit": 1}
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        dados = resp.json()

        if not dados:
            raise ValueError(f"Cidade não encontrada no Nominatim: {cidade}")

        cache[cidade] = [float(dados[0]["lat"]), float(dados[0]["lon"])]
        print(f"  [OK] {cidade} -> {cache[cidade]}")
        time.sleep(1.1) 
    with open(caminho_cache, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    return cache


def gerar_matriz_osrm(equipes: list[tuple[str, str]], coords_cache: dict) -> pd.DataFrame:
    """Consulta o OSRM e devolve a matriz simétrica de distâncias em km."""
    nomes = [eq[0] for eq in equipes]
    coords_str = ";".join(
        f"{coords_cache[cidade][1]},{coords_cache[cidade][0]}"  # lon,lat
        for _, cidade in equipes
    )

    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}"
    params = {"annotations": "distance"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    dados = resp.json()

    if dados.get("code") != "Ok":
        raise RuntimeError(f"Erro no OSRM: {dados}")

    dist_m = np.array(dados["distances"], dtype=float)
    dist_km = np.round(((dist_m + dist_m.T) / 2.0) / 1000.0).astype(int)
    np.fill_diagonal(dist_km, 0)

    return pd.DataFrame(dist_km, index=nomes, columns=nomes)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    caminho_cache = os.path.join(data_dir, "cidades_coords.json")

    # Coleta todas as cidades únicas entre as 14 temporadas
    cidades_unicas = {
        cidade
        for lista in TEMPORADAS.values()
        for _, cidade in lista
    }
    coords_cache = geocodificar_cidades(cidades_unicas, caminho_cache)

    # Gera um CSV por temporada
    print("\nGerando matrizes de distância via OSRM...")
    for nome_inst, equipes in TEMPORADAS.items():
        assert len(equipes) == 12, f"{nome_inst} não tem 12 equipes!"
        df = gerar_matriz_osrm(equipes, coords_cache)
        caminho_csv = os.path.join(data_dir, f"{nome_inst}.csv")
        df.to_csv(caminho_csv, encoding="utf-8")

        media_km = df.to_numpy()[np.triu_indices(12, k=1)].mean()
        max_km = df.to_numpy().max()
        print(f"  [SALVO] {nome_inst}.csv | Média entre cidades: {media_km:6.1f} km | Máx: {max_km:4d} km")
        time.sleep(0.5)

    print("\nConcluído! Todas as 14 instâncias estão prontas em data/.")


if __name__ == "__main__":
    main()