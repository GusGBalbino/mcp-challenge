import asyncio
import json
import os
import re
import sys
from typing import Dict, Any, List
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

class VehicleAgent:
    """Agente conversacional para busca de veículos"""
    
    def __init__(self):
        self.stdio_context = None
        self.session_context = None
        self.session = None
        self.server_running = False
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    async def initialize(self):
        """Inicializa conexão com servidor MCP"""
        try:
            server_params = StdioServerParameters(
                command="python",
                args=["mcp_server.py"]
            )
            
            self.stdio_context = stdio_client(server_params)
            read_stream, write_stream = await self.stdio_context.__aenter__()
            
            self.session_context = ClientSession(read_stream, write_stream)
            self.session = await self.session_context.__aenter__()
            await self.session.initialize()
            
            self.server_running = True
            print("Conexão MCP funcional.")
            
        except Exception as e:
            print(f"Erro ao conectar MCP: {e}")
            self.server_running = False
    
    async def cleanup(self):
        """Limpa recursos de forma adequada"""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.stdio_context:
                await self.stdio_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"Erro durante limpeza: {e}")
    
    async def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Chama ferramenta do servidor MCP com retry"""
        if not self.server_running or not self.session:
            return "Servidor MCP indisponível"
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                result = await self.session.call_tool(tool_name, params)
                return result.content[0].text if result.content else "Sem resultados"
            except Exception as e:
                print(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt == max_retries - 1:
                    return f"Erro após {max_retries} tentativas: {str(e)}"
                await asyncio.sleep(0.5)
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Usa Gemini para analisar intenção do usuário e extrair parâmetros"""
        
        prompt = f"""Analise a seguinte solicitação de um cliente em uma concessionária de veículos:

"{user_input}"

Extraia as informações relevantes e determine a ação mais apropriada. Responda APENAS em formato JSON válido:

{{
  "acao": "uma das opções: buscar_todos, buscar_marcas, buscar_por_marca, buscar_com_filtros, conversar",
  "parametros": {{
    "marca": "nome da marca se mencionada ou null",
    "modelo": "modelo específico se mencionado ou null",
    "ano_minimo": "numero_inteiro ou null",
    "ano_maximo": "numero_inteiro ou null", 
    "preco_minimo": "numero_float ou null",
    "preco_maximo": "numero_float ou null",
    "combustivel": "tipo de combustível se mencionado ou null",
    "cor": "cor se mencionada ou null",
    "cambio": "manual ou automatico se mencionado ou null"
  }},
  "resposta_conversacional": "resposta amigável e natural para o cliente"
}}

Exemplos de ações:
- "buscar_todos": cliente quer ver todos os carros disponíveis
- "buscar_marcas": cliente quer saber que marcas existem no estoque  
- "buscar_por_marca": cliente menciona marca específica (Toyota, Ford, etc)
- "buscar_com_filtros": cliente tem critérios específicos (preço, ano, cor, etc)
- "conversar": saudação, dúvida geral, precisa esclarecimentos

IMPORTANTE: Retorne apenas o JSON, sem texto adicional."""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            if json_text.startswith('```'):
                json_text = json_text.split('\n', 1)[1]
            if json_text.endswith('```'):
                json_text = json_text.rsplit('\n', 1)[0]
            
            return json.loads(json_text)
        except Exception as e:
            print(f"Erro na análise de intenção: {e}")
            return {
                "acao": "conversar", 
                "parametros": {}, 
                "resposta_conversacional": "Desculpe, não entendi bem. Pode me explicar o que você está procurando?"
            }
    
    def format_vehicle_results(self, vehicles_json: str) -> str:
        """Formata resultados dos veículos de forma amigável"""
        try:
            data = json.loads(vehicles_json)
            if "veiculos" in data:
                vehicles = data["veiculos"]
                if not vehicles:
                    return "Não encontrei veículos com esses critérios. Que tal tentar outros filtros?"
                
                total = len(vehicles)
                show_count = min(5, total)
                
                response = f"🚗 Encontrei {total} veículo(s) que podem te interessar:\n\n"
                
                for i, car in enumerate(vehicles[:show_count], 1):
                    response += f"{i}. **{car['marca']} {car['modelo']} {car['ano']}**\n"
                    response += f"   💰 R$ {car['preco']:,.2f}\n"
                    response += f"   🎨 {car['cor']} | 📏 {car['kilometragem']:,} km\n"
                    response += f"   ⛽ {car['combustivel']} | ⚙️ {car['cambio']}\n\n"
                
                if total > show_count:
                    response += f"... e mais {total - show_count} opções disponíveis!\n\n"
                
                response += "Algum desses chamou sua atenção? Posso ajudar com mais detalhes! 😊"
                return response
                
            return vehicles_json
        except Exception as e:
            print(f"Erro ao formatar resultados: {e}")
            return vehicles_json
    
    async def process_user_input(self, user_input: str) -> str:
        """Processa entrada do usuário e retorna resposta"""

        intent = self.analyze_user_intent(user_input)
        
        acao = intent.get("acao", "conversar")
        parametros = intent.get("parametros", {})
        resposta_base = intent.get("resposta_conversacional", "")
        
        try:
            if acao == "buscar_todos":
                mcp_result = await self.call_mcp_tool("get_vehicles", {})
                if mcp_result.startswith("Erro"):
                    return f"Desculpe, tive um problema técnico: {mcp_result}"
                formatted_result = self.format_vehicle_results(mcp_result)
                return f"{resposta_base}\n\n{formatted_result}"
                
            elif acao == "buscar_marcas":
                mcp_result = await self.call_mcp_tool("get_available_brands", {})
                if mcp_result.startswith("Erro"):
                    return f"Desculpe, tive um problema técnico: {mcp_result}"
                data = json.loads(mcp_result)
                brands = ", ".join(data["marcas"])
                return f"{resposta_base}\n\n🏷️ Temos estas marcas disponíveis:\n{brands}\n\nQual marca te interessa mais?"
                
            elif acao == "buscar_por_marca":
                marca = parametros.get("marca", "")
                if marca:
                    mcp_result = await self.call_mcp_tool("get_vehicles_by_brand", {"marca": marca})
                    if mcp_result.startswith("❌    "):
                        return f"Desculpe, tive um problema ao buscar veículos da {marca}: {mcp_result}"
                    formatted_result = self.format_vehicle_results(mcp_result)
                    return f"{resposta_base}\n\n{formatted_result}"
                else:
                    return "Qual marca você gostaria de ver? Temos Toyota, Ford, Chevrolet e várias outras!"
                    
            elif acao == "buscar_com_filtros":
                filtros = {}
                for k, v in parametros.items():
                    if v is not None and v != "" and v != "null":
                        if k in ["ano_minimo", "ano_maximo"]:
                            try:
                                filtros[k] = int(v)
                            except:
                                pass
                        elif k in ["preco_minimo", "preco_maximo"]:
                            try:
                                filtros[k] = float(v)
                            except:
                                pass
                        else:
                            filtros[k] = str(v)
                
                if filtros:
                    mcp_result = await self.call_mcp_tool("get_vehicles_by_filters", filtros)
                    if mcp_result.startswith("❌"):
                        return f"Desculpe, tive um problema na busca: {mcp_result}"
                    formatted_result = self.format_vehicle_results(mcp_result)
                    return f"{resposta_base}\n\n{formatted_result}"
                else:
                    return "Me conte mais sobre o que você procura - marca, faixa de preço, ano, cor..."
            
            else:
                return resposta_base
                
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return "Desculpe, tive um problema técnico. Pode tentar novamente?"

async def main():
    print("🚗 Bem-vindo à Concessionária Virtual! 🚗")
    print("\nOlá! Sou seu assistente para encontrar o carro ideal.")
    print("Digite 'sair' para encerrar.")
    agent = VehicleAgent()
    print("\n🔄 Conectando aos sistemas...")
    
    try:
        await agent.initialize()
        
        if not agent.server_running:
            print("❌ Não foi possível conectar ao servidor. Encerrando.")
            return
        
        print("✅ Tudo pronto! Como posso ajudá-lo hoje?")
        
        while True:
            try:
                # Input do usuário
                user_input = input("\n👤 Você: ").strip()
                
                if user_input.lower() in ['sair', 'quit', 'exit', 'tchau', 'bye']:
                    print("🚗 Obrigado pela visita! Volte sempre! 👋")
                    break
                
                if not user_input:
                    continue
                
                # Processar e responder
                print("🤖 Analisando...")
                response = await agent.process_user_input(user_input)
                print(f"\n🤖 Assistente: {response}")
                
            except KeyboardInterrupt:
                print("\n🚗 Até logo! 👋")
                break
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
                print("Tentando continuar...")
    
    finally:
        # Cleanup
        print("🔧 Finalizando conexões...")
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 