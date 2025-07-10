import os
from supabase import create_client, Client
from typing import List, Dict, Optional, Any
import dotenv

dotenv.load_dotenv()

url: str = os.getenv("SUPABASE_URL")
anon_key: str = os.getenv("SUPABASE_ANON_KEY")
secret_key: str = os.getenv("SUPABASE_SECRET_KEY")  

supabase: Client = create_client(url, secret_key)

def get_all_vehicles() -> List[Dict[str, Any]]:
    """Retorna todos os veículos do banco"""
    try:
        response = supabase.table("vehicles").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar veículos: {e}")
        return []

def filter_vehicles(
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    ano_min: Optional[int] = None,
    ano_max: Optional[int] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    combustivel: Optional[str] = None,
    cor: Optional[str] = None,
    cambio: Optional[str] = None,
    portas: Optional[int] = None,
    km_max: Optional[int] = None,
    apenas_novos: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """Filtra veículos com base nos filtros fornecidos"""
    try:
        query = supabase.table("vehicles").select("*")
        
        # Aplicar filtros condicionalmente
        if marca:
            query = query.ilike("marca", f"%{marca}%")
        if modelo:
            query = query.ilike("modelo", f"%{modelo}%")
        if ano_min:
            query = query.gte("ano", ano_min)
        if ano_max:
            query = query.lte("ano", ano_max)
        if preco_min:
            query = query.gte("preco", preco_min)
        if preco_max:
            query = query.lte("preco", preco_max)
        if combustivel:
            query = query.ilike("combustivel", f"%{combustivel}%")
        if cor:
            query = query.ilike("cor", f"%{cor}%")
        if cambio:
            query = query.ilike("cambio", f"%{cambio}%")
        if portas:
            query = query.eq("portas", portas)
        if km_max:
            query = query.lte("kilometragem", km_max)
        if apenas_novos is True:
            query = query.eq("novo", True)
            
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao filtrar veículos: {e}")
        return []

def get_vehicle_brands() -> List[str]:
    """Retorna lista de marcas disponíveis no estoque"""
    try:
        response = supabase.table("vehicles").select("marca").execute()
        if response.data:
            brands = list(set([item["marca"] for item in response.data]))
            return sorted(brands)
        return []
    except Exception as e:
        print(f"Erro ao buscar marcas: {e}")
        return []