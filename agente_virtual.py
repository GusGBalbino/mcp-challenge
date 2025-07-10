#!/usr/bin/env python3
"""
Agente conversacional para busca de veículos
Versão corrigida com melhor interpretação de intenções
"""
import asyncio
import json
import os
import re
from typing import Dict, Any, List
import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

class VehicleAgent:
    """Agente conversacional para busca de veículos com interpretação melhorada"""
    
    def __init__(self):
        self.stdio_context = None
        self.session_context = None
        self.session = None
        self.server_running = False
        
        # Configurar Gemini
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
            print("✅ Conexão MCP estabelecida!")
            
        except Exception as e:
            print(f"❌ Erro ao conectar MCP: {e}")
            self.server_running = False
    
    async def cleanup(self):
        """Limpa recursos adequadamente"""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.stdio_context:
                await self.stdio_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"⚠️ Erro durante cleanup: {e}")
    
    async def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Chama ferramenta do servidor MCP com retry"""
        if not self.server_running or not self.session:
            return "❌ Servidor MCP indisponível"
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                result = await self.session.call_tool(tool_name, params)
                return result.content[0].text if result.content else "Sem resultados"
            except Exception as e:
                print(f"⚠️ Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt == max_retries - 1:
                    return f"❌ Erro após {max_retries} tentativas: {str(e)}"
                await asyncio.sleep(0.5)
    
    def analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Analisa intenção com foco em múltiplos critérios"""
        
        prompt = f"""Analise esta solicitação de um cliente em uma concessionária:

"{user_input}"

Identifique TODOS os critérios mencionados e determine a melhor ação. Responda APENAS em JSON:

{{
  "acao": "buscar_todos | buscar_marcas | buscar_com_filtros | conversar",
  "criterios_identificados": {{
    "marca": "nome exato da marca se mencionada ou null",
    "modelo": "modelo específico se mencionado ou null", 
    "ano_especifico": "ano específico como número inteiro ou null",
    "ano_minimo": "ano mínimo se mencionado ou null",
    "ano_maximo": "ano máximo se mencionado ou null",
    "preco_minimo": "preço mínimo como número ou null",
    "preco_maximo": "preço máximo como número ou null",
    "combustivel": "tipo de combustível ou null",
    "cor": "cor mencionada ou null",
    "cambio": "manual/automatico ou null"
  }},
  "resposta_conversacional": "resposta natural e amigável"
}}

REGRAS IMPORTANTES:
- Se mencionar marca + ano específico → use "buscar_com_filtros"
- Se mencionar marca + qualquer outro critério → use "buscar_com_filtros"  
- Se mencionar apenas marca → use "buscar_com_filtros" com só marca
- Se mencionar "que marcas tem" → use "buscar_marcas"
- Se mencionar "todos os carros" → use "buscar_todos"
- Se for saudação/dúvida geral → use "conversar"

EXEMPLOS:
- "nissan 2022" → acao: "buscar_com_filtros", marca: "Nissan", ano_especifico: 2022
- "ford até 80 mil" → acao: "buscar_com_filtros", marca: "Ford", preco_maximo: 80000
- "que marcas vocês têm?" → acao: "buscar_marcas"
- "toyota" → acao: "buscar_com_filtros", marca: "Toyota"

Retorne apenas o JSON sem texto adicional."""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            
            # Limpar markdown se presente
            if json_text.startswith('```'):
                json_text = json_text.split('\n', 1)[1]
            if json_text.endswith('```'):
                json_text = json_text.rsplit('\n', 1)[0]
            
            result = json.loads(json_text)
            
            # Debug: mostrar o que foi interpretado
            criterios = result.get("criterios_identificados", {})
            criterios_ativos = {k: v for k, v in criterios.items() if v is not None and v != ""}
            if criterios_ativos:
                print(f"🔍 Critérios identificados: {criterios_ativos}")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Erro na análise: {e}")
            return {
                "acao": "conversar",
                "criterios_identificados": {},
                "resposta_conversacional": "Não entendi bem. Pode me explicar o que você procura?"
            }
    
    def build_filters_from_criteria(self, criterios: Dict[str, Any]) -> Dict[str, Any]:
        """Converte critérios em parâmetros para o MCP"""
        filtros = {}
        
        if criterios.get("marca"):
            filtros["marca"] = criterios["marca"]
        if criterios.get("modelo"):
            filtros["modelo"] = criterios["modelo"]
        if criterios.get("ano_especifico"):
            # Para ano específico, usar como min e max
            ano = int(criterios["ano_especifico"])
            filtros["ano_minimo"] = ano
            filtros["ano_maximo"] = ano
        else:
            if criterios.get("ano_minimo"):
                filtros["ano_minimo"] = int(criterios["ano_minimo"])
            if criterios.get("ano_maximo"):
                filtros["ano_maximo"] = int(criterios["ano_maximo"])
        
        if criterios.get("preco_minimo"):
            filtros["preco_minimo"] = float(criterios["preco_minimo"])
        if criterios.get("preco_maximo"):
            filtros["preco_maximo"] = float(criterios["preco_maximo"])
        if criterios.get("combustivel"):
            filtros["combustivel"] = criterios["combustivel"]
        if criterios.get("cor"):
            filtros["cor"] = criterios["cor"]
        if criterios.get("cambio"):
            filtros["cambio"] = criterios["cambio"]
        
        return filtros
    
    def format_vehicle_results(self, vehicles_json: str) -> str:
        """Formata resultados de forma amigável"""
        try:
            data = json.loads(vehicles_json)
            if "veiculos" in data:
                vehicles = data["veiculos"]
                if not vehicles:
                    return "🚫 Não encontrei veículos com esses critérios. Quer tentar outros filtros?"
                
                total = len(vehicles)
                show_count = min(5, total)
                
                response = f"🚗 Encontrei {total} veículo(s) que atendem seus critérios:\n\n"
                
                for i, car in enumerate(vehicles[:show_count], 1):
                    response += f"{i}. **{car['marca']} {car['modelo']} {car['ano']}**\n"
                    response += f"   💰 R$ {car['preco']:,.2f}\n"
                    response += f"   🎨 {car['cor']} | 📏 {car['kilometragem']:,} km\n"
                    response += f"   ⛽ {car['combustivel']} | ⚙️ {car['cambio']}\n\n"
                
                if total > show_count:
                    response += f"... e mais {total - show_count} opções disponíveis!\n\n"
                
                response += "Algum desses te interessou? Posso ajudar com mais detalhes! 😊"
                return response
                
            return vehicles_json
        except Exception as e:
            print(f"⚠️ Erro ao formatar: {e}")
            return vehicles_json
    
    async def process_user_input(self, user_input: str) -> str:
        """Processa entrada do usuário"""
        
        # Analisar intenção
        intent = self.analyze_user_intent(user_input)
        
        acao = intent.get("acao", "conversar")
        criterios = intent.get("criterios_identificados", {})
        resposta_base = intent.get("resposta_conversacional", "")
        
        print(f"🧠 Ação identificada: {acao}")
        
        try:
            if acao == "buscar_todos":
                mcp_result = await self.call_mcp_tool("get_vehicles", {})
                if mcp_result.startswith("❌"):
                    return f"Desculpe, problema técnico: {mcp_result}"
                formatted_result = self.format_vehicle_results(mcp_result)
                return f"{resposta_base}\n\n{formatted_result}"
                
            elif acao == "buscar_marcas":
                mcp_result = await self.call_mcp_tool("get_available_brands", {})
                if mcp_result.startswith("❌"):
                    return f"Problema técnico: {mcp_result}"
                data = json.loads(mcp_result)
                brands = ", ".join(data["marcas"])
                return f"{resposta_base}\n\n🏷️ Marcas disponíveis:\n{brands}\n\nQual te interessa?"
                
            elif acao == "buscar_com_filtros":
                filtros = self.build_filters_from_criteria(criterios)
                
                if filtros:
                    print(f"🔧 Filtros aplicados: {filtros}")
                    mcp_result = await self.call_mcp_tool("get_vehicles_by_filters", filtros)
                    if mcp_result.startswith("❌"):
                        return f"Problema na busca: {mcp_result}"
                    formatted_result = self.format_vehicle_results(mcp_result)
                    return f"{resposta_base}\n\n{formatted_result}"
                else:
                    return "Me conte mais detalhes sobre o que você procura - marca, ano, preço..."
            
            else:  # conversar
                return resposta_base
                
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return "Desculpe, tive um problema. Pode tentar novamente?"

async def main():
    """Loop principal"""
    print("🚗 Concessionária Virtual - Versão Corrigida! 🚗")
    print("=" * 55)
    print("Agora com interpretação melhorada de critérios!")
    print("Digite 'sair' para encerrar.")
    print("=" * 55)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY não encontrada no .env")
        return
    
    agent = VehicleAgent()
    print("🔄 Conectando...")
    
    try:
        await agent.initialize()
        
        if not agent.server_running:
            print("❌ Falha na conexão. Encerrando.")
            return
        
        print("✅ Pronto! Como posso ajudar?")
        
        while True:
            try:
                user_input = input("\n👤 Você: ").strip()
                
                if user_input.lower() in ['sair', 'quit', 'exit', 'tchau']:
                    print("🚗 Obrigado! Volte sempre! 👋")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Processando...")
                response = await agent.process_user_input(user_input)
                print(f"\n🤖 Assistente: {response}")
                
            except KeyboardInterrupt:
                print("\n🚗 Até logo! 👋")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    finally:
        print("🔧 Finalizando...")
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 