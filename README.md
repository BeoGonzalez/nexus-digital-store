# 🎮 Nexus Digital Store — Enterprise Multi-Agent E-Commerce Platform

> Plataforma enterprise de comercio electrónico gamer de última generación impulsada por una **arquitectura híbrida de Inteligencia Artificial (System 1 + System 2)**, orquestación multi-agente determinista, búsqueda vectorial en la nube y arquitectura hexagonal orientada al dominio.

---

## 🏛️ 1. Arquitectura de Alto Nivel

Nexus combina lo mejor del desarrollo web moderno, arquitectura limpia y pipelines avanzados de IA generativa y multi-agente:

```mermaid
flowchart TB
    subgraph Clients ["Capas de Presentación (Frontend)"]
        Storefront["🌐 Next.js 16 Storefront\n(React 19, Tailwind, 3D Canvas, SSE Client)"]
        AdminPanel["🛡️ Admin Dashboard\n(/admin/games — RBAC con Cognito)"]
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
    subgraph Clients_Observability ["Clientes & Observabilidad"]
        Storefront["🌐 Next.js Storefront\n(Chat UI Reactivo & SSE)"]
        NexusAI["📊 nexus-ai Lab (Streamlit)\n(Inspección de Prompts, RAG & Agentes)"]
        LangSmith["📈 LangSmith Observability\n(Tracing V2 & Trazabilidad de Grafos)"]
    end

    subgraph LangGraph_Core ["🔄 LangGraph StateGraph (Macro-Orquestador de Estado Multi-Turno)"]
        direction TB
        
        subgraph Memory ["Persistencia de Memoria Multi-Turno"]
            Checkpointer[("💾 MemorySaver Checkpointer\n(thread_id / session_id)")]
        end

        %% Nodo 1
        subgraph Node_Decide ["Nodo 1: decide (System 1 — Laya AI)"]
            LayaEngine["🧠 Laya AI Decision Engine\n(Clasificación Reflexiva en Microsegundos)"]
            IntentCheck{"¿Intención?"}
            LayaEngine --> IntentCheck
        end

        %% Nodo 2
        subgraph Node_Retrieve ["Nodo 2: retrieve (RAG Multifuente & APIs Externas)"]
            direction TB
            HF_Embed["📐 HuggingFace MiniLM-L12\n(Embeddings 384d)"]
            PineconeDB[("🌲 Pinecone Vector DB\n(Catálogo de Juegos)")]
            WikiAPI["📚 Wikipedia API\n(Lore, Curiosidades & Trivia)"]
            TavilyAPI["📰 Tavily AI Search API\n(Noticias de Última Hora & Parches)"]
            CheapSharkAPI["🏷️ CheapShark API\n(Steam, Epic, GOG — MÁS BARATO / CARO)"]
            
            HF_Embed --> PineconeDB
        end

        %% Nodo 3
        subgraph Node_Orchestrate ["Nodo 3: orchestrate (System 2 — CrewAI Multi-Agente)"]
            direction LR
            Agent1["📦 Inventory Analyst\n(Valida Stock Real)"]
            Agent2["🎮 Lore Researcher\n(Cultura Gamer)"]
            Agent3["💼 Sales Strategist\n(Argumentos Éticos)"]
            
            Agent1 --> Agent2 --> Agent3
        end

        %% Nodo 4
        subgraph Node_Generate ["Nodo 4: generate (LCEL Chain & Groq LPU)"]
            LCEL["⛓️ LCEL Generation Chain\n(Prompt NexusBot + Contexto Integrado)"]
            GroqEngine["⚡ Groq Cloud LPU\n(openai/gpt-oss-120b)"]
            LCEL --> GroqEngine
        end
    end

    subgraph Output_Stream ["Protocolo de Salida en Tiempo Real"]
        SSE_Products["📦 SSE type: products\n(Cards de Juegos en UI)"]
        SSE_Tokens["💬 SSE type: token\n(Streaming Palabra a Palabra)"]
        SSE_Done["🏁 SSE type: done\n(Fin de Respuesta)"]
    end

    %% Conexiones principales
    Storefront -->|POST /api/v1/assistant/chat| Node_Decide
    NexusAI -.->|Inspección Directa de RAG| Node_Decide
    
    Checkpointer <-->|State Checkpoints| LangGraph_Core
    LangGraph_Core -.->|Telemetría, Spans & Traces| LangSmith

    IntentCheck -->|greeting| Node_Generate
    IntentCheck -->|stock_price / recommendation| Node_Retrieve
    
    Node_Retrieve --> Node_Orchestrate
    Node_Orchestrate --> Node_Generate
    
    Node_Generate --> SSE_Products
    SSE_Products --> SSE_Tokens
    SSE_Tokens --> SSE_Done
    SSE_Tokens -->|Renderizado en Vivo| Storefront
    SSE_Tokens -.->|Inspección de Streaming| NexusAI
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
