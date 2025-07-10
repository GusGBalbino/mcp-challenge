from pydantic import BaseModel

class Vehicle(BaseModel):
    marca: str
    modelo: str
    ano: int
    cor: str
    preco: float
    kilometragem: int
    novo: bool
    doc_ok: bool
    batida: bool
    chassi: str
    combustivel: str
    portas: int
    cambio: str