# 🎮 Nexus Digital Store — Enterprise Multi-Agent E-Commerce Platform

> Plataforma enterprise de comercio electrónico gamer de última generación impulsada por una **arquitectura híbrida de Inteligencia Artificial (System 1 + System 2)**, orquestación multi-agente determinista, búsqueda vectorial en la nube y arquitectura hexagonal orientada al dominio.

---

## 🏛️ 1. Arquitectura de Alto Nivel

Nexus combina lo mejor del desarrollo web moderno, arquitectura limpia y pipelines avanzados de IA generativa y multi-agente:

```mermaid
flowchart TB
    subgraph Clients ["Capas de Presentación (Frontend & Observabilidad)"]
        Storefront["🌐 Next.js 16 Storefront\n(React 19, Tailwind, 3D Canvas, SSE Client)"]
        AdminPanel["🛡️ Admin Dashboard\n(/admin/games — RBAC con Cognito)"]
        NexusAI["📊 nexus-ai Lab (Streamlit)\n(Dashboard Interactivo & Inspección RAG)"]
    end

    subgraph AWS_Networking ["Red & Balanceo (AWS Cloud)"]
        ALB["⚖️ Application Load Balancer (ALB)\n(SSL Termination, Listener Rules, Preflight CORS)"]
        Route53["🗺️ Amazon Route 53 (Private DNS)\n(db.nexus.internal CNAME)"]
    end

    subgraph ECS_Cluster ["Cómputo Backend (AWS ECS sobre EC2)"]
        subgraph FastAPI_Backend ["Nexus Backend Monolith (FastAPI — Arquitectura Hexagonal)"]
            Router["🛣️ Presentation / REST & SSE Routes"]
            AuthGuard["🔒 Cognito JWT Guard / RBAC (admin)"]
            Services["⚙️ Application / Domain Services"]
            
            subgraph AI_Pipeline ["Pipeline Cognitivo Híbrido (System 1 + System 2)"]
                Laya["🧠 Laya AI (System 1)\nClasificación Reflexiva Rápida"]
                LangGraph["🔄 LangGraph + MemorySaver\n(Macro-Orquestador de Estado Multi-Turno)"]
                CrewAI["🤖 CrewAI Multi-Agente (System 2)\n(Analista + Investigador + Estratega)"]
            end
        end
    end

    subgraph AWS_Data ["Persistencia & Autenticación (AWS Cloud)"]
        Cognito["🔑 Amazon Cognito User Pool\n(nexus-user-pool / Group: admin)"]
        subgraph Aurora_Cluster ["Amazon Aurora PostgreSQL (Multi-AZ)"]
            AuroraWriter[("🐘 Aurora Writer (Primary)\n(Catálogo, Órdenes, Advisory Lock)")]
            AuroraReader[("📖 Aurora Reader (Replica)\n(Consultas de Solo Lectura)")]
        end
    end

    subgraph External_AI_Services ["Servicios Externos de IA & Conocimiento"]
        Groq["⚡ Groq LPU Cloud\n(Inferencia Ultrarrápida — gpt-oss-120b)"]
        Pinecone[("🌲 Pinecone Vector DB\n(Búsqueda Semántica 384d, Namespace catalog)")]
        LangSmith["📊 LangSmith Observability\n(Tracing V2 & Trazabilidad de Grafos)"]
        Wiki["📚 Wikipedia API\n(Lore, Curiosidades & Cultura Gamer)"]
        Tavily["📰 Tavily AI Search API\n(Noticias de Última Hora & Parches)"]
        CheapShark["🏷️ CheapShark API\n(Comparativa de Precios: Steam, Epic, GOG)"]
    end

    %% Flujos de clientes
    Storefront -->|HTTPS / SSE Streaming| ALB
    AdminPanel -->|Admin REST Requests| ALB
    NexusAI -.->|Test de Pipeline / Chat SSE| ALB
    NexusAI -.->|Inspección Directa de RAG| Pinecone
    ALB --> Router
    
    %% Autenticación
    Router --> AuthGuard
    AuthGuard -.->|Valida JWT con JWKS público| Cognito
    
    %% Flujo interno del backend
    Router --> Services
    Services --> AI_Pipeline
    
    %% Pipeline de IA
    AI_Pipeline --> Laya
    Laya -->|Intent & Decision Metrics| LangGraph
    LangGraph --> CrewAI
    CrewAI --> Groq
    LangGraph -.->|Telemetría & Traces| LangSmith
    
    %% Enriquecimiento RAG & APIs externas
    LangGraph --> Pinecone
    LangGraph --> Wiki
    LangGraph --> Tavily
    LangGraph --> CheapShark
    
    %% Base de datos
    Services --> Route53
    Route53 --> AuroraWriter
    Services -.->|Read Queries| AuroraReader
```

---

## 🧩 2. Estructura del Monorepo

```plaintext
nexus/
├── docker-compose.yml              # Orquestación completa multi-contenedor
├── .gitignore                      # Reglas globales de exclusión y seguridad
├── test_ai.py                      # Script interactivo de validación E2E para la IA
│
├── nexus-digital-store/
│   ├── nexus-backend/              # API Principal (FastAPI, Python 3.11, UV)
│   │   ├── src/nexus_backend/
│   │   │   ├── ai_assistant/       # Módulo IA: LangGraph, CrewAI, Laya, Pinecone
│   │   │   │   ├── domain/         # Entidades puras y puertos (Hexagonal)
│   │   │   │   ├── application/    # Casos de uso, servicios, grafos y cadenas LCEL
│   │   │   │   ├── infrastructure/ # Adaptadores (Groq, Pinecone, HF, Wikipedia)
│   │   │   │   └── presentation/   # Endpoints HTTP y Server-Sent Events (SSE)
│   │   │   ├── auth/               # Autenticación JWT y usuarios
│   │   │   ├── catalog/            # Gestión de videojuegos, géneros y stock
│   │   │   ├── orders/             # Procesamiento y ciclo de vida de órdenes
│   │   │   └── config.py           # Configuración centralizada vía Pydantic Settings
│   │   ├── tests/                  # 97 pruebas unitarias e integración (Pytest)
│   │   └── Dockerfile              # Contenedor optimizado de producción
│   │
│   └── nexus-frontend/             # Storefront (Next.js 16, React 19, TypeScript)
│       ├── src/
│       │   ├── app/                # App Router de Next.js
│       │   ├── components/         # UI Components (Shadcn UI, Lucide, 3D Canvas)
│       │   └── hooks/              # Consumo reactivo de eventos SSE del asistente
│       └── Dockerfile              # Multi-stage build para Next.js Standalone
│
└── nexus-ai/                       # Entorno de Experimentación y Observabilidad
    ├── app.py                      # App visual en Streamlit con inspección de prompts
    └── Dockerfile              
```

---

## 🤖 3. Arquitectura del Asistente IA (NexusBot)

### Diagrama del Pipeline Cognitivo (System 1 + System 2 con LangGraph, CrewAI & APIs)

```mermaid
flowchart TD
    subgraph Clients_Observability ["Capas de Consumo & Observabilidad (Monorepo)"]
        Storefront["🌐 nexus-frontend (Next.js 16)\n(Chat UI Gamer, Tarjetas de Producto & SSE)"]
        NexusAI["📊 nexus-ai Lab (Streamlit App)\n(Inspección de Prompts, RAG, Agentes & Trazas)"]
        LangSmith["📈 LangSmith Observability\n(Tracing V2 & Trazabilidad de Grafos en Vivo)"]
    end

    subgraph Backend_Hexagonal ["⚙️ nexus-backend Core (FastAPI — Módulo ai_assistant)"]
        direction TB

        subgraph Presentation_Layer ["Presentation Layer"]
            Router["🛣️ Router SSE: /api/v1/assistant/chat\n(StreamingResponse text/event-stream)"]
        end

        subgraph Application_Layer ["Application Layer — Orquestadores de IA"]
            direction TB
            
            subgraph MemorySaver_Box ["Persistencia de Memoria Multi-Turno"]
                Checkpointer[("💾 MemorySaver Checkpointer\n(Checkpoints por thread_id / session_id)")]
            end

            subgraph LangGraph_Engine ["🔄 LangGraph StateGraph (Macro-Orquestador de Estado)"]
                direction TB

                %% Nodo 1: Laya AI
                subgraph Node_Decide ["Nodo 1: decide (System 1 — Laya AI)"]
                    LayaEngine["🧠 LayaDecisionAdapter\n(Clasificación Reflexiva en Microsegundos)"]
                    IntentRouter{"¿Intención?"}
                    LayaEngine --> IntentRouter
                end

                %% Nodo 2: RAG Multifuente
                subgraph Node_Retrieve ["Nodo 2: retrieve (RAG Multifuente & APIs Externas)"]
                    direction TB
                    RAG_Dispatcher["📡 Dispatcher RAG Concurrente"]
                    Port_Embed["📐 EmbeddingPort (MiniLM-L12 384d)"]
                    Port_Pinecone["🌲 VectorStorePort (Pinecone)"]
                    Port_Wiki["📚 ExternalKnowledgePort (Wikipedia)"]
                    Port_Tavily["📰 GamingNewsPort (Tavily AI)"]
                    Port_CheapShark["🏷️ PriceComparisonPort (CheapShark)"]

                    RAG_Dispatcher --> Port_Embed --> Port_Pinecone
                    RAG_Dispatcher --> Port_Wiki
                    RAG_Dispatcher --> Port_Tavily
                    RAG_Dispatcher --> Port_CheapShark
                end

                %% Nodo 3: CrewAI
                subgraph Node_Orchestrate ["Nodo 3: orchestrate (System 2 — CrewAI Multi-Agente)"]
                    direction LR
                    Agent_Catalog["📦 Catalog & Inventory Analyst\n(Valida Stock & Precios)"]
                    Agent_Culture["🎮 Gaming Culture Researcher\n(Lore & Preferencias del Gamer)"]
                    Agent_Sales["💼 Senior Sales Strategist\n(Argumentos de Venta Éticos)"]

                    Agent_Catalog --> Agent_Culture --> Agent_Sales
                end

                %% Nodo 4: Generación LCEL
                subgraph Node_Generate ["Nodo 4: generate (LCEL Chain & Groq LPU)"]
                    LCEL_Chain["⛓️ LCEL Composable Chain\n(build_nexusbot_prompt + System Prompt Enriquecido)"]
                    LLM_Port["⚡ LLMPort (GroqLLMAdapter — ChatGroq)"]
                    LCEL_Chain --> LLM_Port
                end
            end
        end

        subgraph Infrastructure_Adapters ["Infrastructure Layer — Adaptadores Externos"]
            Ad_Pinecone["🌲 PineconeVectorStoreAdapter"]
            Ad_Wiki["📚 WikipediaAdapter"]
            Ad_Tavily["📰 TavilyNewsAdapter"]
            Ad_CheapShark["🏷️ CheapSharkPriceAdapter"]
            Ad_Groq["⚡ GroqLLMAdapter"]
            Ad_Laya["🧠 LayaDecisionAdapter"]
        end
    end

    subgraph External_Cloud_APIs ["Nube & APIs Externas"]
        Cloud_Pinecone[("🌲 Pinecone Vector DB\n(nexus-catalog / nexus_chile)")]
        Cloud_Wiki["📚 Wikipedia REST API\n(Lore & Trivia Gamer)"]
        Cloud_Tavily["📰 Tavily AI Search API\n(Noticias de Última Hora & Parches)"]
        Cloud_CheapShark["🏷️ CheapShark API\n(Steam, Epic, GOG — MÁS BARATO / CARO)"]
        Cloud_Groq["⚡ Groq Cloud LPU\n(openai/gpt-oss-120b)"]
    end

    subgraph Streaming_Protocol ["Protocolo Server-Sent Events (SSE)"]
        SSE_Cards["📦 data: {'type': 'products', 'data': [...]} (UI Cards)"]
        SSE_Words["💬 data: {'type': 'token', 'data': '...'} (Tokens)"]
        SSE_End["🏁 data: {'type': 'done'} (Fin de Stream)"]
    end

    %% Conexiones Clientes -> API
    Storefront -->|POST /chat| Router
    NexusAI -.->|Test & Inspección de Prompts| Router
    NexusAI -.->|Similarity Search Directo| Cloud_Pinecone

    Router --> LangGraph_Engine
    Checkpointer <-->|Guarda / Recupera Turnos| LangGraph_Engine
    LangGraph_Engine -.->|Trazas @traceable| LangSmith

    %% Transiciones del Grafo
    IntentRouter -->|greeting| Node_Generate
    IntentRouter -->|recommendation / stock_price| Node_Retrieve
    Node_Retrieve --> Node_Orchestrate
    Node_Orchestrate --> Node_Generate

    %% Adaptadores a APIs
    Port_Pinecone -.-> Ad_Pinecone -.-> Cloud_Pinecone
    Port_Wiki -.-> Ad_Wiki -.-> Cloud_Wiki
    Port_Tavily -.-> Ad_Tavily -.-> Cloud_Tavily
    Port_CheapShark -.-> Ad_CheapShark -.-> Cloud_CheapShark
    LLM_Port -.-> Ad_Groq -.-> Cloud_Groq

    %% Salida Streaming
    Node_Generate --> SSE_Cards
    SSE_Cards --> SSE_Words
    SSE_Words --> SSE_End
    SSE_Words -->|Renderizado Reactivo| Storefront
    SSE_Words -.->|Inspección en Tiempo Real| NexusAI
```

### Pipeline Dual (System 1 + System 2)
1. **System 1 (Detección Reflexiva Rápida)**:  
   Implementado con **Laya AI**. Clasifica en microsegundos la intención del usuario (`greeting`, `recommendation`, `stock_price`), determinando si la consulta amerita costosas búsquedas externas o si se resuelve de manera inmediata.
2. **System 2 (Razonamiento Multi-Agente & RAG)**:  
   - **Vector DB**: Búsqueda semántica de catálogo en **Pinecone** (índice `nexus-catalog`, dimensión 384, espacio multitenant `nexus_chile`).
   - **Trivia Gamer**: Inyección de contexto histórico y curiosidades vía **Wikipedia API**.
   - **Noticias & Actualidad Gamer**: Búsqueda de parches, anuncios y lanzamientos vía **Tavily AI Search API**.
   - **Comparador de Precios Externos**: Análisis en tiempo real de ofertas en tiendas de PC (Steam, Epic Games Store, GOG, Humble Store, etc.) vía **CheapShark API**, con conversión a pesos chilenos ($ CLP) y dictamen explícito de ahorro frente a Nexus Digital Store.
   - **CrewAI**: Tres agentes autónomos colaboran en cadena:
     - *Catalog & Inventory Analyst*: Valida stock y disponibilidad real.
     - *Gaming Culture Researcher*: Conecta el lore del título con los intereses del usuario.
     - *Senior Sales Strategist*: Consolida los argumentos de venta éticos y transparentes.
   - **LangGraph & MemorySaver**: Macro-orquestador de 4 nodos que preserva el hilo conversacional multi-turno mediante checkpoints (`thread_id`), permitiendo al usuario repreguntar sin reenviar el historial.
   - **Streaming en Tiempo Real**: Protocolo **SSE (`text/event-stream`)** que despacha tarjetas de producto interactivas (`type: products`) seguidas de tokens generados en streaming (`type: token`).

---

## 🚀 4. Puesta en Marcha Rápida (Local & Docker)

### Requisitos Previos
- **Docker & Docker Compose** (v2+)
- **Python 3.11+** con gestor [`uv`](https://github.com/astral-sh/uv)
- **Node.js 20+** y `pnpm`

### Opción A: Despliegue con Docker Compose (Recomendada)
Para levantar todos los servicios integrados:

```bash
# 1. Clonar el repositorio y ubicarse en la raíz
cd c:\nexus

# 2. Configurar variables de entorno (revisar claves en .env)
# 3. Construir y levantar contenedores
docker compose up --build -d
```

| Servicio | URL Local | Descripción |
| :--- | :--- | :--- |
| **Storefront Web** | [http://localhost:3000](http://localhost:3000) | Tienda gamer con asistente 3D y streaming reactivo |
| **API Backend** | [http://localhost:8000](http://localhost:8000) | FastAPI con documentación Swagger en `/docs` |
| **AI Dashboard** | [http://localhost:8501](http://localhost:8501) | Consola interactiva de Streamlit para el laboratorio IA |

---

### Opción B: Ejecución Manual para Desarrollo

#### 1. Backend (`nexus-backend`)
```bash
cd nexus-digital-store/nexus-backend

# Sincronizar dependencias con uv
uv sync

# Ejecutar pruebas automatizadas
uv run python -m pytest

# Iniciar servidor de desarrollo
uv run uvicorn nexus_backend.main:app --reload --port 8000
```

#### 2. Frontend (`nexus-frontend`)
```bash
cd nexus-digital-store/nexus-frontend

pnpm install
pnpm dev
```

#### 3. Probar la IA en Terminal
Para verificar la recuperación semántica, el razonamiento y la memoria conversacional multi-turno:
```bash
uv run python test_ai.py
```

---

## 🛡️ 5. Calidad de Software, Testing y Seguridad

- **Pruebas Automatizadas**: 97 tests unitarios y de integración (`pytest`, `pytest-asyncio`, `httpx-asgi`) con **100% de tasa de aprobación** y ejecución en menos de 10 segundos.
- **Arquitectura Hexagonal**: Aislamiento estricto entre el dominio, los puertos y los adaptadores de infraestructura.
- **Gestión de Secretos**: Exclusión total de credenciales sensibles mediante `.gitignore` estructurado para evitar fugas de claves en repositorios remotos.
- **Observabilidad**: Integración nativa con **LangSmith** para trazabilidad de cadenas y grafos de ejecución de agentes.
