# 🚗 Sistema de Concessionária Virtual - Desafio C2S

Sistema conversacional para busca de veículos utilizando **Model Context Protocol (MCP)** e **Gemini AI**.

## 📋 Requisitos Atendidos

- ✅ **Modelagem de Dados**: 13 atributos (marca, modelo, ano, cor, preço, etc.)
- ✅ **Banco Populado**: 105+ veículos
- ✅ **Protocolo MCP**: Comunicação Cliente → Servidor MCP → Database
- ✅ **Agente Conversacional**: LLM (Gemini)
- ✅ **Testes Automatizados**: Validação de respostas do agente

## 🏗️ Arquitetura

```
┌─────────────────┐    MCP     ┌─────────────────┐    SQL     ┌─────────────────┐
│                 │ Protocol   │                 │ Queries    │                 │
│  Agente Virtual │ ◄────────► │  Servidor MCP   │ ◄────────► │   Supabase DB   │
│   (Gemini AI)   │            │   (FastMCP)     │            │   (PostgreSQL)  │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

## 🚀 Instalação

### 1. **Pré-requisitos**
- Python 3.11+
- Conta Google (para Gemini API)
- Conta Supabase (para banco de dados)

### 2. **Clone e Dependências**
```bash
git clone <seu-repositorio>
cd cs2_challenge
pip install -r requirements.txt
```

### 3. **Configuração do Ambiente**

Crie arquivo `.env` na raiz do projeto:

```env
# Supabase Database
SUPABASE_URL=https://sua-url-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anonima_aqui
SUPABASE_SECRET_KEY=sua_chave_secreta_aqui

# Google Gemini AI
GEMINI_API_KEY=sua_chave_gemini_aqui
```

#### **Obtendo as APIs:**

**Supabase:**
1. Acesse [supabase.com](https://supabase.com)
2. Crie novo projeto
3. Vá em Settings → API
4. Copie URL e chaves

**Gemini:**
1. Acesse [ai.google.dev](https://ai.google.dev)
2. Clique em "Get API Key"
3. Crie nova chave
4. Copie a chave gerada

### 4. **Configuração do Banco**

Execute o SQL no Supabase:

```bash
# Acesse seu projeto Supabase → SQL Editor
# Cole o conteúdo do arquivo populate_vehicles.sql
# Execute o script (criará tabela + 105 veículos)
```

## 📚 Estrutura do Projeto

```
cs2_challenge/
├── agente_virtual.py      # Agente conversacional principal
├── mcp_server.py          # Servidor MCP com ferramentas
├── database.py            # Conexão e consultas Supabase
├── schema.py              # Modelo de dados dos veículos
├── populate_vehicles.sql  # Script de população do banco
├── test_agent.py          # Testes automatizados
├── requirements.txt       # Dependências Python
└── README.md              # Este arquivo
```

## 🎯 Execução

### **Modo Desenvolvimento**

**Terminal 1** - Servidor MCP:
```bash
python mcp_server.py
```

**Terminal 2** - Agente Conversacional:
```bash
python agente_virtual.py
```

### **Exemplo de Conversa**

```
🚗 Concessionária Virtual - Versão Corrigida! 🚗
=======================================================
Agora com interpretação melhorada de critérios!
Digite 'sair' para encerrar.
=======================================================
✅ Pronto! Como posso ajudar?

👤 Você: nissan 2022
🤖 Processando...
🔍 Critérios identificados: {'marca': 'Nissan', 'ano_especifico': 2022}
🧠 Ação identificada: buscar_com_filtros
🔧 Filtros aplicados: {'marca': 'Nissan', 'ano_minimo': 2022, 'ano_maximo': 2022}

🤖 Assistente: Claro! Vou verificar os Nissan 2022 disponíveis no nosso estoque.

🚗 Encontrei 4 veículo(s) que atendem seus critérios:

1. **Nissan Sentra 2022**
   💰 R$ 95,000.00
   🎨 Vermelho | 📏 8,000 km
   ⛽ Flex | ⚙️ Automático

2. **Nissan Versa 2022**
   💰 R$ 78,000.00
   🎨 Branco | 📏 10,000 km
   ⛽ Flex | ⚙️ Automático

3. **Nissan X-Trail 2022**
   💰 R$ 145,000.00
   🎨 Cinza | 📏 8,000 km
   ⛽ Gasolina | ⚙️ Automático

4. **Nissan NV200 2022**
   💰 R$ 125,000.00
   🎨 Branco | 📏 8,000 km
   ⛽ Flex | ⚙️ Manual

Algum desses te interessou? Posso ajudar com mais detalhes! 😊

👤 Você: ford até 80 mil
👤 Você: que marcas vocês têm?
👤 Você: sair
```

## 🧪 Testes

### **Testes Completos com Pytest**
```bash
pytest test_agent.py -v
```

### **Cobertura de Testes**
- ✅ Interpretação de intenções
- ✅ Conversão de critérios para filtros
- ✅ Formatação de resultados
- ✅ Validação do schema de dados
- ✅ Simulação de integração MCP

## 🛠️ Funcionalidades

### **Tipos de Busca Suportados:**

1. **Por Marca**: `"toyota"`, `"quero um honda"`
2. **Marca + Ano**: `"nissan 2022"`, `"ford 2021"`
3. **Marca + Preço**: `"chevrolet até 80 mil"`
4. **Faixa de Preço**: `"carros entre 50 e 100 mil"`
5. **Combustível**: `"carros flex"`, `"diesel"`
6. **Cor**: `"carros brancos"`, `"vermelho"`
7. **Câmbio**: `"automático"`, `"manual"`
8. **Combinações**: `"toyota automático até 90 mil"`

### **Comandos Especiais:**
- `"que marcas têm?"` → Lista todas as marcas
- `"todos os carros"` → Mostra todo o estoque
- `"sair"` → Encerra o programa