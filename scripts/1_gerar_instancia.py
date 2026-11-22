"""
Script para gerar a matriz de distâncias da Superliga Masculina 2024/25.

O que este código faz:
1. Mapeia as 12 equipes participantes para suas respectivas cidades-sede.
2. Consulta a API gratuita do Nominatim (OpenStreetMap) para obter as
   coordenadas oficiais (latitude e longitude) de cada município.
3. Envia essas coordenadas ao OSRM (OpenStreetMap) para calcular as
   distâncias rodoviárias reais entre todas as cidades.
4. Converte os valores para quilômetros inteiros, garante simetria na matriz,
   zera a diagonal principal e salva o resultado em data/sbv_m_24_25.csv.
"""

import os
import time
import requests
import pandas as pd
import numpy as np

EQUIPES_CIDADES = {
    "Sada_Cruzeiro": "Contagem, Minas Gerais, Brazil",
    "Minas": "Belo Horizonte, Minas Gerais, Brazil",
    "Praia_Clube": "Uberlândia, Minas Gerais, Brazil",
    "Sesi_Bauru": "Bauru, São Paulo, Brazil",
    "Volei_Renata": "Campinas, São Paulo, Brazil",
    "Guarulhos": "Guarulhos, São Paulo, Brazil",
    "Suzano": "Suzano, São Paulo, Brazil",
    "Sao_Jose": "São José dos Campos, São Paulo, Brazil",
    "Joinville": "Joinville, Santa Catarina, Brazil",
    "Blumenau": "Blumenau, Santa Catarina, Brazil",
    "Goias": "Goiânia, Goiás, Brazil",
    "Neurologia_Ativa": "Goiânia, Goiás, Brazil",
}

def buscar_coordenadas_municipio(cidade: str) -> tuple[float, float]:
    """Consulta o Nominatim (OSM) e retorna (latitude, longitude) do município"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": cidade, "format": "json", "limit": 1}
    # O Nominatim exige um User-Agent identificando a aplicação
    headers = {"User-Agent": "SBV_Fair_Scheduling_ALNS/1.0 (pesquisa academica)"}

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    resultados = resp.json()

    if not resultados:
        raise ValueError(f"Município não encontrado no Nominatim: {cidade}")

    return float(resultados[0]["lat"]), float(resultados[0]["lon"])

def gerar_matriz_distancias(equipes_cidades: dict, caminho_saida: str):
    cache_cidades = {}
    coordenadas = {}

    # Buscando coordenadas dos municípios no Nominatim (OSM)
    for equipe, cidade in equipes_cidades.items():
        if cidade not in cache_cidades:
            lat, lon = buscar_coordenadas_municipio(cidade)
            cache_cidades[cidade] = (lat, lon)
            print(f"   {cidade} -> ({lat:.4f}, {lon:.4f})")
            time.sleep(1.1)
        coordenadas[equipe] = cache_cidades[cidade]

    nomes = list(coordenadas.keys())
    # OSRM usa formato longitude,latitude
    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coordenadas.values())
    url_osrm = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"

    # Consultando distâncias rodoviárias no OSRM
    resp = requests.get(url_osrm, timeout=30)
    resp.raise_for_status()
    dados = resp.json()

    matriz_km = np.array(dados["distances"], dtype=float) / 1000.0
    matriz_simetrica = np.round((matriz_km + matriz_km.T) / 2.0).astype(int)
    np.fill_diagonal(matriz_simetrica, 0)

    df = pd.DataFrame(matriz_simetrica, index=nomes, columns=nomes)

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    df.to_csv(caminho_saida)
    print(f"\nMatriz salva com sucesso em: {caminho_saida}\n")
    print(df.iloc[:5, :5])

if __name__ == "__main__":
    gerar_matriz_distancias(EQUIPES_CIDADES, "../data/sbv_m_24_25.csv")