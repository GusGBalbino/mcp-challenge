from mcp.server.fastmcp import FastMCP
from database import (
    get_all_vehicles, 
    filter_vehicles, 
    get_vehicle_brands
)
from typing import List, Dict, Optional, Any
import json

mcp = FastMCP("Estoque de Carros - Servidor MCP")

@mcp.tool()
def get_vehicles() -> str:
    """
    Busca todos os veículos disponíveis no estoque
    """
    vehicles = get_all_vehicles()
    return json.dumps({
        "total_veiculos": len(vehicles),
        "veiculos": vehicles
    }, ensure_ascii=False, indent=2)

@mcp.tool()
def get_vehicles_by_filters(
    marca: str = "",
    modelo: str = "",
    ano_minimo: int = 0,
    ano_maximo: int = 0,
    preco_minimo: float = 0.0,
    preco_maximo: float = 0.0,
    combustivel: str = "",
    cor: str = "",
    cambio: str = "",
    portas: int = 0,
    quilometragem_maxima: int = 0,
    apenas_veiculos_novos: bool = False
) -> str:
    """
    Busca veículos aplicando filtros específicos.
    Parâmetros vazios ou zerados são ignorados na busca.
    """

    filters = {
        "marca": marca if marca else None,
        "modelo": modelo if modelo else None,
        "ano_min": ano_minimo if ano_minimo > 0 else None,
        "ano_max": ano_maximo if ano_maximo > 0 else None,
        "preco_min": preco_minimo if preco_minimo > 0 else None,
        "preco_max": preco_maximo if preco_maximo > 0 else None,
        "combustivel": combustivel if combustivel else None,
        "cor": cor if cor else None,
        "cambio": cambio if cambio else None,
        "portas": portas if portas > 0 else None,
        "km_max": quilometragem_maxima if quilometragem_maxima > 0 else None,
        "apenas_novos": apenas_veiculos_novos if apenas_veiculos_novos else None
    }
    
    vehicles = filter_vehicles(**filters)
    
    return json.dumps({
        "filtros_aplicados": {k: v for k, v in filters.items() if v is not None},
        "veiculos_encontrados": len(vehicles),
        "veiculos": vehicles
    }, ensure_ascii=False, indent=2)

@mcp.tool()
def get_available_brands() -> str:
    """
    Retorna lista de todas as marcas de veículos disponíveis no estoque
    """
    brands = get_vehicle_brands()
    return json.dumps({
        "total_marcas": len(brands),
        "marcas": brands
    }, ensure_ascii=False, indent=2)

@mcp.tool()
def get_vehicles_by_brand(marca: str) -> str:
    """
    Busca todos os veículos de uma marca específica
    """
    vehicles = filter_vehicles(marca=marca)
    return json.dumps({
        "marca_pesquisada": marca,
        "veiculos_encontrados": len(vehicles),
        "veiculos": vehicles
    }, ensure_ascii=False, indent=2)

@mcp.tool()
def get_vehicles_by_price(preco_minimo: float, preco_maximo: float) -> str:
    """
    Busca veículos dentro de uma faixa de preço específica
    """
    vehicles = filter_vehicles(preco_min=preco_minimo, preco_max=preco_maximo)
    return json.dumps({
        "faixa_preco": {
            "minimo": preco_minimo,
            "maximo": preco_maximo
        },
        "veiculos_encontrados": len(vehicles),
        "veiculos": vehicles
    }, ensure_ascii=False, indent=2)

@mcp.resource("vehicles://all")
def get_all_vehicles_resource() -> str:
    """
    Resource para acessar todos os veículos
    """
    vehicles = get_all_vehicles()
    return json.dumps(vehicles, ensure_ascii=False, indent=2)

@mcp.resource("vehicles://brands")
def get_brands_resource() -> str:
    """
    Resource para acessar todas as marcas
    """
    brands = get_vehicle_brands()
    return json.dumps(brands, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys
    
    print("🚗 Servidor MCP - Estoque de Carros", file=sys.stderr)
    print("📊 Tools disponíveis:", file=sys.stderr)
    print("  - get_vehicles", file=sys.stderr)
    print("  - get_vehicles_by_filters", file=sys.stderr)
    print("  - get_available_brands", file=sys.stderr)
    print("  - get_vehicles_by_brand", file=sys.stderr)
    print("  - get_vehicles_by_price", file=sys.stderr)
    print("🔧 Resources disponíveis:", file=sys.stderr)
    print("  - vehicles://all", file=sys.stderr)
    print("  - vehicles://brands", file=sys.stderr)
    print("🚀 Servidor aguardando conexões...", file=sys.stderr)
    
    try:
        brands = get_vehicle_brands()
        print(f"✅ Banco conectado! {len(brands)} marcas disponíveis", file=sys.stderr)
    except Exception as e:
        print(f"❌ Erro no banco: {e}", file=sys.stderr)
        sys.exit(1)
    
    mcp.run()