#!/usr/bin/env python3
"""
Testes automatizados para o agente conversacional
Valida respostas e interpretação de intenções
"""
import asyncio
import json
import pytest
import os
from unittest.mock import Mock, patch
from agente_virtual import VehicleAgent
from dotenv import load_dotenv

load_dotenv()

class TestVehicleAgent:
    """Testes para o agente conversacional de veículos"""
    
    @pytest.fixture
    def agent(self):
        """Cria instância do agente para testes"""
        return VehicleAgent()
    
    def test_analyze_intent_brand_only(self, agent):
        """Testa interpretação de busca por marca apenas"""
        result = agent.analyze_user_intent("Quero um Toyota")
        
        assert result["acao"] == "buscar_com_filtros"
        criterios = result["criterios_identificados"]
        assert criterios["marca"] == "Toyota"
        assert criterios["ano_especifico"] is None
        assert "resposta_conversacional" in result
    
    def test_analyze_intent_brand_and_year(self, agent):
        """Testa interpretação de busca por marca + ano específico"""
        result = agent.analyze_user_intent("tem nissan 2022?")
        
        assert result["acao"] == "buscar_com_filtros"
        criterios = result["criterios_identificados"]
        assert criterios["marca"] == "Nissan"
        assert criterios["ano_especifico"] == 2022
    
    def test_analyze_intent_price_range(self, agent):
        """Testa interpretação de busca por faixa de preço"""
        result = agent.analyze_user_intent("ford até 80 mil")
        
        assert result["acao"] == "buscar_com_filtros"
        criterios = result["criterios_identificados"]
        assert criterios["marca"] == "Ford"
        assert criterios["preco_maximo"] == 80000
    
    def test_analyze_intent_list_brands(self, agent):
        """Testa interpretação de solicitação para listar marcas"""
        result = agent.analyze_user_intent("que marcas vocês têm?")
        
        assert result["acao"] == "buscar_marcas"
    
    def test_analyze_intent_all_vehicles(self, agent):
        """Testa interpretação de busca por todos os veículos"""
        result = agent.analyze_user_intent("quero ver todos os carros")
        
        assert result["acao"] == "buscar_todos"
    
    def test_analyze_intent_conversation(self, agent):
        """Testa interpretação de saudação/conversa geral"""
        result = agent.analyze_user_intent("oi, tudo bem?")
        
        assert result["acao"] == "conversar"
        assert "resposta_conversacional" in result
    
    def test_build_filters_from_criteria(self, agent):
        """Testa conversão de critérios em filtros MCP"""
        criterios = {
            "marca": "Toyota",
            "ano_especifico": 2022,
            "preco_maximo": 100000,
            "cor": "Branco"
        }
        
        filtros = agent.build_filters_from_criteria(criterios)
        
        assert filtros["marca"] == "Toyota"
        assert filtros["ano_minimo"] == 2022
        assert filtros["ano_maximo"] == 2022
        assert filtros["preco_maximo"] == 100000.0
        assert filtros["cor"] == "Branco"
    
    def test_format_vehicle_results_with_data(self, agent):
        """Testa formatação de resultados com dados"""
        mock_data = {
            "veiculos_encontrados": 2,
            "veiculos": [
                {
                    "marca": "Toyota",
                    "modelo": "Corolla",
                    "ano": 2022,
                    "cor": "Preto",
                    "preco": 85000.0,
                    "kilometragem": 10000,
                    "combustivel": "Flex",
                    "cambio": "Automático"
                },
                {
                    "marca": "Honda",
                    "modelo": "Civic",
                    "ano": 2021,
                    "cor": "Branco",
                    "preco": 92000.0,
                    "kilometragem": 15000,
                    "combustivel": "Flex",
                    "cambio": "Manual"
                }
            ]
        }
        
        result = agent.format_vehicle_results(json.dumps(mock_data))
        
        assert "Encontrei 2 veículo(s)" in result
        assert "Toyota Corolla 2022" in result
        assert "Honda Civic 2021" in result
        assert "R$ 85,000.00" in result
        assert "R$ 92,000.00" in result
        assert "Preto" in result
        assert "Branco" in result
    
    def test_format_vehicle_results_no_data(self, agent):
        """Testa formatação quando não há resultados"""
        mock_data = {
            "veiculos_encontrados": 0,
            "veiculos": []
        }
        
        result = agent.format_vehicle_results(json.dumps(mock_data))
        
        assert "Não encontrei veículos" in result
        assert "outros filtros" in result


class TestMCPIntegration:
    """Testes de integração com o servidor MCP"""
    
    @pytest.mark.asyncio
    async def test_mcp_connection_simulation(self):
        """Simula teste de conexão MCP"""
        #Mock mcp
        agent = VehicleAgent()
        
        agent.server_running = False
        result = await agent.call_mcp_tool("get_vehicles", {})
        assert result == "❌ Servidor MCP indisponível"
    
    def test_vehicle_schema_completeness(self):
        """Testa se o schema tem todos os atributos necessários"""
        from schema import Vehicle
        
        vehicle_data = {
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2022,
            "cor": "Preto",
            "preco": 85000.0,
            "kilometragem": 10000,
            "novo": False,
            "doc_ok": True,
            "batida": False,
            "chassi": "ABC123456789",
            "combustivel": "Flex",
            "portas": 4,
            "cambio": "Automático"
        }
        vehicle = Vehicle(**vehicle_data)
        assert vehicle.marca == "Toyota"
        assert vehicle.ano == 2022
        assert vehicle.preco == 85000.0
        assert len(vehicle_data) >= 10


class TestAgentResponses:
    """Testes das respostas do agente para cenários específicos"""
    
    def test_response_quality_metrics(self):
        """Testa métricas de qualidade das respostas"""
        agent = VehicleAgent()
        
        test_cases = [
            "nissan 2022",
            "ford até 50 mil",
            "que marcas têm?",
            "oi, tudo bem?",
            "quero um carro automático"
        ]
        
        for case in test_cases:
            result = agent.analyze_user_intent(case)
            
            assert "acao" in result
            assert "criterios_identificados" in result
            assert "resposta_conversacional" in result
            
            valid_actions = ["buscar_todos", "buscar_marcas", "buscar_com_filtros", "conversar"]
            assert result["acao"] in valid_actions
            
            assert len(result["resposta_conversacional"]) > 0