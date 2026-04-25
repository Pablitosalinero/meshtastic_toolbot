# Meshtastic Toolbot

Este es un bot de Meshtastic desarrollado en Python, gestionado a través de `uv` (Ultraviolet). Automáticamente se conecta a un dispositivo Meshtastic conectado por puerto serie/USB, escucha los mensajes, y responde si recibe comandos específicos.

## Requisitos
- [uv](https://github.com/astral-sh/uv) instalado.
- Un dispositivo Meshtastic conectado localmente por cable USB al PC.
- (Opcional pero necesario para el ejemplo) Debes tener un canal configurado llamado exactamente **`test`** en el dispositivo.

## Instalación

1. Clona o asegúrate de estar en el directorio de este repositorio.
2. Inicia todo el entorno y descarga de dependencias usando `uv` (nuestro gestor de paquetes de manera automática). No hay que instalar paquetes manualmente con pip, ya que `pyproject.toml` lo gestiona todo.
   
## Uso

Para ejecutar el bot, simplemente corre el siguiente comando en este directorio:

```bash
uv run main.py
```

El bot intentará conectarse mediante autodescubrimiento al dispositivo conectado por USB.

### Comandos Soportados

| Comando / Evento | Canal  | Respuesta            | Descripción                                 |
|------------------|--------|----------------------|---------------------------------------------|
| `/ping`          | `test` | `Pong!` (en test)    | Verifica que el bot está activo y conectado |

## Estructura del Código

- **`main.py`**: El código de la aplicación. Se suscribe a los eventos del dispositivo con el módulo pubsub (`pub.subscribe`). Filtra los paquetes recibidos en busca de cadenas de texto (`TEXT_MESSAGE_APP`). Revisa a qué índice de canal corresponde dicho mensaje, compara si el nombre asignado en la radio es `test` y responde por ese mismo canal.
- **`pyproject.toml`**: Archivo de metadatos utilizado por `uv` que declara dependencias (como `meshtastic`).