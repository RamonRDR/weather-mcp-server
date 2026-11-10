<div align="center">

# Weather MCP Server 🌦️

**Herramientas meteorológicas para asistentes de IA mediante MCP real.**

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇪🇸 Español](README.es.md)

[![CI](https://github.com/RamonRDR/weather-mcp-server/actions/workflows/ci.yml/badge.svg?branch=feat%2Fweather-mcp-server-v1)](https://github.com/RamonRDR/weather-mcp-server/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![MCP SDK](https://img.shields.io/badge/MCP_SDK-2.3%2B%20%28%3C3%29-5B43B5)
![MCP stdio](https://img.shields.io/badge/MCP_transport-stdio-6F42C1)
![MCP tools](https://img.shields.io/badge/MCP_tools-3%20read--only-7057FF)
![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063)
![Pydantic Settings](https://img.shields.io/badge/Pydantic_Settings-2.7%2B-B72867)
![httpx](https://img.shields.io/badge/httpx-0.28%2B-009688)
![Open-Meteo](https://img.shields.io/badge/Open--Meteo-HTTP%20adapter-3986C6)
[![Weather Cache API](https://img.shields.io/badge/Weather_Cache_API-adapter-3A75C4)](https://github.com/RamonRDR/weather-cache-api)

![pytest](https://img.shields.io/badge/pytest-32%20passing-0A9EDC)
![pytest-asyncio](https://img.shields.io/badge/pytest--asyncio-async%20tests-2980B9)
![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-D7FF64)
![MCP integration](https://img.shields.io/badge/MCP_protocol-stdio%20tested-3EA566)
![Python build](https://img.shields.io/badge/Python_package-wheel%20%26%20sdist-4B8BBE)
![setuptools](https://img.shields.io/badge/setuptools-build%20backend-6272A4)

</div>

> **Estado del proyecto:** Implementado en el [PR #1](https://github.com/RamonRDR/weather-mcp-server/pull/1), pendiente de revisión final con Codex y aprobación explícita de la fusión. El [último CI aprobado antes de esta actualización](https://github.com/RamonRDR/weather-mcp-server/actions/runs/42416169603) confirmó **32 pruebas aprobadas, 0 fallidas y 0 omitidas**. No se afirma que exista despliegue MCP remoto ni validación externa integral en vivo.

Servidor **Model Context Protocol (MCP)** de solo lectura, con herramientas estructuradas para condiciones actuales, pronósticos diarios y comparaciones entre ciudades. Utiliza el SDK oficial MCP para Python y el transporte stdio, no una API REST renombrada. Pydantic valida las entradas y salidas.

## ¿Qué es MCP?

MCP estandariza cómo los clientes de IA descubren e invocan herramientas. El cliente inicia este servidor como proceso local, negocia el protocolo, descubre las herramientas y recibe resultados estructurados. No requiere un modelo real ni una suscripción de IA.

## Funcionalidades

| Herramienta | Entrada | Resultado |
| --- | --- | --- |
| `get_current_weather` | `city` (1–100 caracteres) | ubicación, fecha de observación, temperatura, sensación térmica, humedad, precipitación, viento, condición y fuente |
| `get_weather_forecast` | `city`, `days` (1–7; predeterminado 3) | fechas, temperaturas mínimas/máximas, probabilidad de lluvia, condiciones y fuente |
| `compare_weather` | `first_city`, `second_city` | dos lecturas actuales y diferencia de temperatura (primera menos segunda) |

Los valores opcionales desconocidos son `null`, nunca inventados. Las temperaturas están en °C y el viento en km/h. No se admiten operaciones de escritura, comandos del sistema, acceso a archivos o URL arbitrarias.

## Tecnologías

**Ejecución:** Python **3.14** en GitHub Actions, SDK oficial MCP para Python **>=2.3,<3** (stdio), Pydantic **v2** (`>=2.10,<3`), Pydantic Settings (`>=2.7,<3`) y httpx (`>=0.28,<1`). Los badges que incluyen un signo más representan **versiones mínimas declaradas**, no versiones exactas fijadas.

**Integraciones:** Tres herramientas MCP tipadas y de solo lectura, con descubrimiento y resultados estructurados. El adaptador de la [Weather Cache API](https://github.com/RamonRDR/weather-cache-api) usa el contrato existente `GET /weather?city=` para las condiciones actuales. Los endpoints fijos de geocodificación y pronóstico de Open-Meteo se usan para previsiones diarias y, opcionalmente, para condiciones actuales directas. Los adaptadores están **implementados y probados con HTTP simulado**; no se afirma que ambos servicios se hayan ejecutado juntos en vivo. Redis pertenece a la API externa; **este repositorio no tiene base de datos propia ni Docker Compose**.

**Calidad:** pytest (con parametrización), pytest-asyncio, Ruff para lint y formato, integración MCP mediante stdio, GitHub Actions, setuptools como backend de construcción y `python -m build` para generar wheel y distribución de código fuente. El CI valida la instalación del wheel; no ejecuta mypy, build Docker, OpenAPI/Swagger ni mediciones de cobertura.

## Estructura del proyecto

| Ruta | Responsabilidad |
| --- | --- |
| `src/weather_mcp_server/server.py` | Servidor MCP, tres herramientas tipadas y manejo público de errores |
| `src/weather_mcp_server/__main__.py` | Inicio local por stdio |
| `src/weather_mcp_server/service.py` | Adaptadores HTTP Weather Cache API y Open-Meteo |
| `src/weather_mcp_server/schemas.py` | Contratos Pydantic de entrada, salida y proveedores |
| `src/weather_mcp_server/config.py` | Configuración y restricciones de URL externas |
| `src/weather_mcp_server/rate_limit.py` | Cuota de llamadas por proceso |
| `src/weather_mcp_server/demo.py`, `demo_data.py` | Demostración sin conexión con datos explícitamente ficticios |
| `tests/test_mcp.py`, `tests/test_service.py` | Pruebas del protocolo y HTTP simulado |
| `scripts/check_readme_badges.py` | Consistencia de los badges con el informe JUnit de pytest |
| `.github/workflows/ci.yml` | Ruff, pruebas, badges y validación de paquetes |

## Arquitectura

```mermaid
flowchart LR
  Host[Cliente de IA] -->|MCP stdio| MCP[MCPServer v2]
  MCP --> Tools[3 herramientas validadas]
  Tools --> Service[Servicio meteorológico]
  Service -->|actual| API[Weather Cache API /weather]
  API --> Redis[(Redis en API original)]
  Service -->|pronóstico| OM[Open-Meteo]
  Service -->|modo directo| OM
  Service -->|modo simulado| Mock[Datos ficticios]
```

La [Weather Cache API](https://github.com/RamonRDR/weather-cache-api) implementa `GET /weather?city=` y `GET /metrics` en la rama **main**; el contrato fue inspeccionado, pero no se ha validado en vivo la ejecución conjunta. **No existe un endpoint de pronóstico**. Este MCP reutiliza su contrato actual y deja el caché Redis en el otro repositorio; los pronósticos provienen directamente de Open-Meteo.

## Instalación

Se recomienda **Python 3.14** y un entorno virtual:

```bash
python -m venv .venv
# Active el entorno virtual para su sistema.
python -m pip install -e '.[dev]'
cp .env.example .env
```

En PowerShell: `Copy-Item .env.example .env` y `.venv\Scripts\Activate.ps1`.

## Configuración

| Variable | Valor inicial | Uso |
| --- | --- | --- |
| `MCP_BACKEND` | `cache_api` | `cache_api`, `open_meteo` o `mock` |
| `MCP_CACHE_API_BASE_URL` | `http://127.0.0.1:8000` | origen de la API; HTTPS obligatorio para destinos remotos |
| `MCP_HTTP_TIMEOUT_SECONDS` | `5` | timeout HTTP positivo, hasta 30 segundos |
| `MCP_RATE_LIMIT_CALLS` | `60` | cuota de llamadas por proceso |
| `MCP_RATE_LIMIT_WINDOW_SECONDS` | `60` | duración de ventana |
| `MCP_LOG_LEVEL` | `INFO` | registros JSON en stderr |

El backend inicial `cache_api` requiere que la API original esté activa para condiciones actuales. Si no está disponible, seleccione `MCP_BACKEND=open_meteo` para consultas reales directas, sin Redis. `MCP_BACKEND=mock` devuelve **datos ficticios fijos** para pruebas.

## Ejecución

```bash
python -m weather_mcp_server
# o:
weather-mcp-server
```

El servidor espera mensajes MCP del cliente, sin pedir prompts de texto común. stdout se reserva para el protocolo; los registros operativos utilizan stderr.

### Ejemplo de configuración de cliente

Cada aplicación host tiene su propio formato; este JSON es ilustrativo:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["-m", "weather_mcp_server"],
      "env": {"MCP_BACKEND": "mock"}
    }
  }
}
```

El comando Python debe usar el entorno donde está instalado el paquete. Cambie `mock` por `open_meteo` para datos reales o por `cache_api` con la API externa ejecutándose.

### MCP Inspector

Con Node.js/`npx` disponible:

```bash
MCP_BACKEND=mock npx @modelcontextprotocol/inspector python -m weather_mcp_server
```

En PowerShell: `$env:MCP_BACKEND='mock'; npx @modelcontextprotocol/inspector python -m weather_mcp_server`. Explore las herramientas, ejecute consultas y compruebe las respuestas estructuradas y los errores de entrada. Consulte [demo](docs/demo.md).

## Ejemplo estructurado

**Datos ficticios**, no una observación real:

```json
{
  "location": {"name": "Berlin", "country": "Germany", "latitude": 52.52, "longitude": 13.41},
  "observed_at": "2026-10-01T12:00:00Z",
  "temperature_c": 18.0,
  "apparent_temperature_c": null,
  "relative_humidity_percent": null,
  "precipitation_mm": null,
  "wind_speed_kmh": null,
  "weather_code": 0,
  "condition": "Clear sky (fictional sample)",
  "source": "mock-fixture",
  "cached": null
}
```

El pronóstico incluye fechas y rangos de temperatura; la comparación contiene las dos lecturas y su diferencia. Los argumentos inválidos generan errores MCP (`is_error=true`).

## Pruebas y GitHub Actions

```bash
ruff check .
ruff format --check .
python -m pytest -q
python -m build
python -m weather_mcp_server.demo
```

GitHub Actions usa un runner estándar de GitHub con Python 3.14 para Ruff, pruebas unitarias con HTTP simulado, integración MCP en memoria y con stdio real, y creación del paquete. Las pruebas obligatorias no necesitan Redis, API meteorológica externa, credenciales ni modelos de IA de pago. No se realiza despliegue ni fusión automática.

### Evidencia y mantenimiento de los badges

El badge **pytest 32 passing** es una instantánea estática de la [ejecución Quality #6, commit `e2c6599`](https://github.com/RamonRDR/weather-mcp-server/actions/runs/42416169603), que registró **32 aprobadas**, sin pruebas fallidas ni omitidas. El badge del workflow sigue la **rama de desarrollo** hasta que se fusione con `main`; después deberá actualizarse su parámetro de rama mediante un cambio de documentación revisado.

El CI ejecuta pytest con un informe JUnit XML. Luego, `scripts/check_readme_badges.py` compara el número real de casos aprobados con el badge de los tres READMEs y verifica que contengan el mismo conjunto de badges. Las modificaciones en las pruebas exigen actualizar el contador estático de los **tres archivos**; no hay commits automáticos ni tokens externos. El badge del workflow es dinámico, mientras que el de pytest no lo es.

Python 3.14 fue confirmado en CI. MCP SDK `2.3+`, httpx `0.28+` y Pydantic Settings `2.7+` indican versiones mínimas declaradas, no necesariamente versiones instaladas exactas. Los dos adaptadores meteorológicos tienen pruebas con mocks, pero no validación en vivo de ambos servicios juntos.

## Seguridad y limitaciones

Validación de ciudad y máximo de siete días, destinos externos fijados en configuración y código, HTTPS para hosts remotos, sin redirecciones, timeouts y errores públicos que no exponen secretos. Los registros van a stderr. La cuota de llamadas es por proceso, no autenticación distribuida. Una ciudad ambigua puede resolverse como la primera coincidencia.

La Weather Cache API debe ejecutarse por separado desde su rama **main** y todavía no ofrece pronósticos. Consultas reales requieren red; respete los términos de Open-Meteo. No se incluye transporte HTTP remoto porque requiere autenticación, controles de origen y sesiones. Más detalles: [arquitectura](docs/architecture.md), [demostración](docs/demo.md).

## Contribuciones

Se aceptan issues y pull requests. Ejecute `ruff check .`, `ruff format --check .` y `python -m pytest -q` antes de proponer cambios. Mantenga las herramientas de solo lectura, evite URL arbitrarias y nunca publique credenciales. Las fusiones requieren aprobación del mantenedor.

## Licencia

Datos meteorológicos: [Open-Meteo](https://open-meteo.com/). Código bajo [licencia MIT](LICENSE). © 2026 Ramon Rodriguez.
