# 🤖 AI Project Orchestrator
**Sistema de Orquestación Inteligente para Automatización de Proyectos**

## 📄 Descripción

Este proyecto implementa un sistema avanzado de orquestación que utiliza inteligencia artificial con OpenAI GPT-4.1-mini para automatizar el análisis, modificación y gestión de proyectos de código. El sistema está diseñado para asistir a desarrolladores y equipos en la implementación de cambios y mejoras en sus repositorios, ofreciendo:

- 🔍 **Análisis profundo** de la estructura y calidad del código
- 📊 **Evaluación de viabilidad** y estimación de esfuerzo inteligente
- 🎯 **Planificación automática** de tareas y dependencias
- 🛠️ **Implementación guiada** de mejoras y correcciones
- 📈 **Seguimiento y validación** de cambios con testing automático
- 🤖 **Sistema de agentes especializados** para diferentes tecnologías

El sistema combina agentes de IA especializados, análisis de código inteligente y múltiples interfaces (CLI y Web) para proporcionar una experiencia completa de automatización de proyectos.

---

## ⭐ Características Principales

### 🧠 Sistema de Agentes Especializados
- **Agent Analyzer**: Análisis profundo de código y estructura de proyectos
- **Agent Development**: Implementación inteligente de mejoras y cambios
- **Chunk System**: Sistema de procesamiento por fragmentos para proyectos grandes
- **Prompts especializados**: Para análisis, backend y frontend

### 🔍 Análisis Inteligente
- **Estructura del proyecto**: Análisis automático de arquitectura y organización
- **Detección de tecnologías**: Identificación automática de stacks tecnológicos
- **Evaluación de complejidad**: Scoring inteligente de dificultad de implementación
- **Análisis de viabilidad**: Evaluación técnica y estimación de esfuerzo
- **Categorización de tareas**: Sistema inteligente de clasificación y priorización

### 🛠️ Capacidades de Implementación
- **Coordinación de proyectos**: Workflow completo de análisis a implementación
- **Gestión de tareas**: Creación, categorización y ejecución automática
- **Testing automático**: Validación de implementaciones con diferentes tipos de tests
- **Integración Git**: Soporte completo para GitLab y GitHub
- **Notificaciones**: Sistema de alertas por email

### 🎮 Interfaces Disponibles
- **CLI completa**: Línea de comandos con comandos especializados
- **Sistema de testing**: Suite completa de pruebas

---

## ⚙️ Tecnologías y Dependencias

### 🔧 Core del Sistema
- **Python** >=3.9 (excluye 3.9.7 por incompatibilidades)
- **Poetry** para gestión de dependencias
- **OpenAI API** (GPT-4.1-mini) para agentes de IA
- **Pydantic v2** + **pydantic-settings** para modelos y configuración

### 💻 Interfaz CLI
- **Typer** para comandos CLI con autocompletado
- **Rich** para output colorido y formateo

### 🔗 Integración Externa
- **GitPython** para operaciones Git completas
- **requests** para APIs de GitLab/GitHub
- **python-dotenv** para variables de entorno
- **tiktoken** para conteo de tokens OpenAI

### 🧪 Testing
- **pytest** + **pytest-asyncio** para tests asíncronos
- **pytest-cov** para reportes de cobertura
- **unittest.mock** (Python stdlib) para simulación

### 📧 Notificaciones
- **smtplib** + **email.mime** (Python stdlib) para emails

---

## 🚀 Instalación y Configuración

### 📦 Instalación
```bash
# Clonar el repositorio
git clone [URL_DEL_REPOSITORIO]
cd toni-tfg-orchestrator

# Instalar dependencias con Poetry
poetry install
```

### 🔧 Configuración

Copia el archivo `.env.example` en la raíz del proyecto y renombrarlo a `.env`, después completar cada uno de sus campos con los valores correspondientes.
```

### 🎮 Modo de Pruebas (Mock)
El proyecto incluye un sistema completo de mocks para desarrollo y testing:

- **Activación**: Establece `USE_MOCKS=true` en el archivo `.env`
- **Ubicación**: Los mocks se encuentran en `src/infrastructure/mocks/`
- **Funcionalidades mock**:
  - Simulación completa de operaciones Git
  - Respuestas predefinidas para OpenAI API
  - Evita modificaciones reales en repositorios
  - Permite testing sin consumir tokens de API

---

## 🎯 Formas de Ejecución

### 1. 💻 Modo CLI (Línea de Comandos)

#### Comando Principal - Orquestación Completa
```console
project run 
  --repo-url "https://github.com/usuario/repositorio.git"
  --description "Descripción detallada de los cambios solicitados" 
  --email "tu-email@ejemplo.com" 
  --branch "main" (Opcional)
```

**Ejemplo práctico:**
```console
project run 
  --repo-url "https://gitlab.com/ejemplo/proyecto.git" 
  --description "Refactorizar el módulo de autenticación para mejorar la seguridad y añadir autenticación de dos factores" 
  --email "desarrollador@empresa.com" \
  --branch "develop"
```

### 2. 🧪 Sistema de Testing 
```console
# Ejecutar todos los tests
project test

# Tests específicos por tipo
project test --type unit        # Tests unitarios
project test --type integration # Tests de integración  
project test --type e2e         # Tests end-to-end

# Con reporte de cobertura
project test --type all --coverage

# Modo verbose para debugging
project test --type unit --verbose

# Test de archivo específico
project test --file src/project_tests/unit/test_analysis_service.py
```

**Tipos de testing disponibles:**
- **Unit**: Tests de componentes individuales con mocks
- **Integration**: Tests de integración entre servicios
- **E2E**: Tests completos de workflow CLI
- **Coverage**: Reporte HTML detallado de cobertura

---

## 🏗️ Estructura del Proyecto

```
src/
├── application/                           # Lógica de aplicación
│   ├── agents/                           # 🤖 Agentes de IA especializados
│   │   ├── agent_analyzer.py            # Agente análisis de código
│   │   ├── agent_development.py         # Agente implementación
│   │   ├── chunk_system.py              # Sistema de fragmentación
│   │   ├── prompts_analyzer.py          # Prompts para análisis
│   │   ├── prompts_backend.py           # Prompts para backend
│   │   └── prompts_frontend.py          # Prompts para frontend
│   ├── analysis/                        # 📊 Servicios de análisis
│   │   ├── analysis_service.py          # Servicio principal de análisis
│   │   ├── tech_detector.py             # Detector de tecnologías
│   │   └── config/
│   │       └── analysis_config.yaml     # Configuración de análisis
│   ├── tasks/                           # 📋 Gestión de tareas
│   │   ├── task_manager.py              # Gestor principal de tareas
│   │   ├── task_categorizer.py          # Categorizador inteligente
│   │   ├── task_prioritizer.py          # Sistema de priorización
│   │   └── config/
│   │       └── task_categorization.yaml # Configuración de categorías
│   ├── services/                        # 🔧 Servicios de aplicación
│   │   ├── agent_manager.py             # Gestión de agentes
│   │   └── agent_health_service.py      # Monitoreo de salud
│   ├── factories/                       # 🏭 Factorías de contexto
│   │   └── cli_context_factory.py       # Factory para contexto CLI
│   └── project_coordinator.py           # 🎯 Coordinador principal
│
├── cli/                                 # 💻 Interfaz de línea de comandos
│   ├── entrypoint.py                    # Punto de entrada CLI
│   ├── cli_runner.py                    # Ejecutor de comandos
│   └── cli_enrich.py                    # Funciones de presentación
│
├── domain/                              # 📐 Modelos de dominio
│   └── models/                          # Modelos Pydantic
│       ├── agent_model.py               # Modelos para agentes
│       ├── analysis_models.py           # Modelos de análisis
│       ├── git_models.py                # Modelos para Git
│       ├── project_details_model.py     # Modelos de proyecto
│       └── task_model.py                # Modelos de tareas
│
├── frontend/                            # 🚧 Interfaz web (en desarrollo)
│   ├── app.py                          # Aplicación Streamlit (parcial)
│   ├── run.py                          # Script de ejecución web
│   └── resources/                       # Recursos visuales
│       ├── Logo_black.png              # Logo versión oscura
│       ├── Logo_white.png              # Logo versión clara
│       ├── background_loby.png         # Fondo lobby
│       └── background_loading.png      # Fondo carga
│
├── infrastructure/                      # 🏗️ Servicios de infraestructura
│   ├── git/                            # Git y control de versiones
│   │   ├── git_service.py              # Operaciones Git locales
│   │   ├── github_service.py           # Integración GitHub
│   │   ├── gitlab_service.py           # Integración GitLab
│   │   ├── file_exclusion.py           # Sistema de exclusiones
│   │   └── common_exclusions.py        # Exclusiones comunes
│   ├── openai/                         # 🧠 Integración OpenAI
│   │   └── openai_service.py           # Cliente OpenAI
│   ├── execution_tests/                # 🧪 Testing automático
│   │   ├── test_manager.py             # Gestor de tests
│   │   ├── test_service.py             # Servicio de testing
│   │   ├── test_implementation.py      # Tests de implementación
│   │   ├── test_results_analyzer.py    # Análisis de resultados
│   │   └── test_suite_runner.py        # Ejecutor de suites
│   ├── notification/                   # 📧 Sistema de notificaciones
│   │   └── email_service.py            # Servicio de email
│   ├── mocks/                          # 🎭 Sistema de mocks
│   │   ├── mock_openai.py              # Mock OpenAI
│   │   ├── mock_responses.py           # Respuestas mock
│   │   └── mock_service.py             # Servicio mock
│   ├── services/                       # ⚙️ Servicios base
│   │   └── service_lifecycle.py        # Ciclo de vida
│   └── repositories/                   # 💾 Repositorios de datos
│
├── project_tests/                      # 🧪 Suite de testing
│   ├── unit/                           # Tests unitarios
│   │   ├── test_analysis_service.py    # Tests análisis
│   │   ├── test_git_service.py         # Tests Git
│   │   ├── test_models.py              # Tests modelos
│   │   ├── test_openai_service.py      # Tests OpenAI
│   │   └── test_task_manager.py        # Tests tareas
│   ├── integration/                    # Tests integración
│   │   └── test_project_coordinator_integration.py
│   ├── e2e/                           # Tests end-to-end
│   │   └── test_cli_workflow.py        # Tests workflow CLI
│   └── conftest.py                     # Configuración pytest
│
├── utils/                              # 🛠️ Utilidades
│   ├── logging.py                      # Sistema de logging
│   └── exceptions_control.py           # Control de excepciones
│
├── config.py                           # ⚙️ Configuración global
└── main.py                             # 🚀 Punto de entrada principal
```

---

## 📋 Sugerencias de Mejora Identificadas

### 🔧 Mejoras Técnicas Pendientes
1. **Refactorización de servicios**: Mover función `analyze_repository_structure` de `git_service` a `/analysis` para mejor organización
2. **Consistencia de datos**: Unificar el manejo de información en objetos Pydantic, evitando conversiones diccionario ↔ objeto
3. **Optimización de excepciones**: Revisar si `exceptions_control.py` necesita realmente una clase por cada grupo de archivos
4. **Sistema de rollback**: Implementar rollback automático de tareas en caso de fallos durante la ejecución (De momento no fallan)

### 🚀 Mejoras de Rendimiento
5. **Limpieza automática**: Sistema automático para limpiar repositorios clonados al finalizar el trabajo (Actualmente lo deja clonado en la carpeta `repositories`)
6. **Optimización de prompts**: Evaluar en agentes (`@prompt_analyzer`, `@prompts_frontend`, `@prompts_backend`) si usar referencias por línea exacta vs referencias semánticas (precisión vs eficiencia)
7. **Agregación de tareas**: Funcionalidad para unir tareas relacionadas y procesarlas juntas (Valorar si es rentable ahorrar tokens vs pérdida de eficacia)

### 🧪 Mejoras de Testing
8. **Tests más robustos**: Mejorar los tests de validación del código generado, actualmente tienen baja probabilidad de fallar

---

### Logging y Monitoreo
- **Logs estructurados** con diferentes niveles por módulo
- **Seguimiento completo** del workflow de orquestación
- **Métricas de rendimiento** de agentes IA
- **Reportes de testing** automático

---

## 👥 Autoría y Versión

**Autor**: Toni Tormo  
**Proyecto**: TFG-Shakers  
**Versión**: 27/06/2025 - v2.0
