# Meshtastic Toolbot

Este es un bot interactivo de Meshtastic desarrollado en Python, gestionado a través de `uv` (Ultraviolet). Automáticamente se conecta a un dispositivo Meshtastic conectado por puerto serie/USB, escucha los mensajes, y responde con telemetría de red detallada si recibe comandos específicos.

## Requisitos
- [uv](https://github.com/astral-sh/uv) instalado.
- Un dispositivo Meshtastic conectado localmente por cable USB al PC.
- (Recomendado) Debes tener un canal local configurado llamado **`Test`** en tu dispositivo de radio, aunque es modificable desde el código.

## Instalación

1. Clona o asegúrate de estar en el directorio de este repositorio.
2. Inicia todo el entorno y descarga de dependencias usando `uv` (nuestro gestor de paquetes de manera automática). No hay que instalar paquetes manualmente con pip, ya que `pyproject.toml` lo gestiona todo.
   
## Uso

Para ejecutar el bot, simplemente corre el siguiente comando en este directorio:

```bash
uv run main.py
```

El bot intentará conectarse mediante autodescubrimiento al dispositivo conectado por USB. Al arrancar, anunciará su inicio en el canal destino indicando su nombre de nodo original.

### Comandos Soportados

| Comando / Evento | Canal  | Respuesta                                  | Descripción                                                                                 |
|------------------|--------|--------------------------------------------|---------------------------------------------------------------------------------------------|
| `/ping`          | `Test` | Reporte completo de telemetría y enrutado  | Verifica que el bot está activo y devuelve un análisis técnico de la calidad de la conexión |

### Diccionario de Métricas del /ping

El bot desensambla el paquete protobuf entrante de Meshtastic para extraer las siguientes estadísticas:

- **Node**: Muestra el texto definido estáticamente en la constante `BOT_LOCATION` dentro de `main.py`.
- **RSSI**: Se extrae del atributo temporal `packet["rxRssi"]`. La radio base le asocia este dato al paquete en el mismo instante en que la antena atrapa la señal, indicando la potencia bruta recibida en dBm.
- **SNR**: Se extrae de `packet["rxSnr"]`. Inyectado por el chip inteligente de radio al medir el umbral de limpieza eléctrica frente al nivel general del ruido de fondo de la banda (dB).
- **Hops**: Se calcula restando los metadatos de enrutamiento del paquete de hardware. Meshtastic incluye `hopStart` (saltos máximos con los que salió del emisor) y `hopLimit` (restantes). El bot usa `(hopStart - hopLimit) / hopStart` para pintar visualmente cuantos de estos saltos fueron consumidos.
- **Relay**: Es el nodo intermedio que nos catapultó el paquete. Meshtastic (para ahorrar ancho de banda sobre LoRa) trunca la matrícula de la antena que actúa como relay a un tristísimo tamaño de **1 solo byte** (0-255) y lo estampa en `packet["relayNode"]`. El bot, para sacarle un nombre en claro, hace ingeniería cruzando ese byte contra un escaneo iterativo (`node_id & 0xFF`) del archivo interno de contactos (`interface.nodes`) hasta dar con un "match". Si esto falla o si los saltos consumidos fueron 0 (conexión directa sin nadie repitiendo), la app le quita la máscara y lo mapea extrayéndole directamente el ID de 32 bits original del paquete: `packet["from"]`.

## Estructura del Código

- **`main.py`**: El motor del bot. Se suscribe a los eventos del dispositivo con `pub.subscribe`, intercepta paquetes `TEXT_MESSAGE_APP` del index de `Test` y responde a `id` usando `replyId` en forma de hilo. Contiene lógicas visuales de mapeo.
- **`pyproject.toml`**: Archivo de entorno Python gestionado nativamente mediante `uv`.