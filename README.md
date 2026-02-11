# NetApp ONTAP FCP SVM Creation Script

Script automatizado para la creación y configuración completa de Storage Virtual Machines (SVMs) con protocolo FCP en NetApp ONTAP usando la API REST oficial.

## Descripción

Este script de Python automatiza todo el proceso de creación de una SVM configurada para protocolo FCP (Fibre Channel Protocol) en NetApp ONTAP, incluyendo:

- Creación de la SVM con configuración básica
- Modificación de parámetros de espacio lógico
- Creación de servicio FCP
- Configuración de protocolos permitidos (CIFS, NFS, FCP, iSCSI, etc.)
- Creación de interfaces de red FCP (múltiples)
- Creación de interfaz de management
- Backup automático de event logs del cluster
- Sistema de logging con timestamp para todas las operaciones

## Requisitos

### Software
- Python 3.7 o superior
- NetApp ONTAP 9.6 o superior
- Acceso de red al cluster NetApp
- Credenciales de administrador del cluster

### Dependencias Python
```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
svm_fcp_create/
├── create_fcp_svm.py  # Script principal
├── config.yaml        # Archivo de configuración
├── requirements.txt   # Dependencias Python
├── README.md          # Esta documentación
└── logs/              # Logs JSON generados automáticamente
```

## Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno. El archivo incluye las siguientes secciones:

### cluster
Configuración de conexión al cluster NetApp:
- `host`: Hostname o IP del cluster
- `username`: Usuario administrador
- `password`: Contraseña

### svm
Configuración de la Storage Virtual Machine:
- `name`: Nombre de la SVM a crear
- `ipspace`: IPspace (default: Default)
- `aggregate`: Agregado para volumen raíz
- `language`: Código de idioma (default: c.utf_8)
- `security_style`: Estilo de seguridad (unix/ntfs/mixed)
- `aggr_list`: Lista de agregados permitidos
- `is_space_reporting_logical`: Reporte de espacio lógico (true/false)
- `is_space_enforcement_logical`: Enforcement de espacio lógico (true/false)
- `fcp_status_admin`: Estado administrativo del servicio FCP (up/down)
- `protocols`: Diccionario de protocolos permitidos (cifs, nfs, fcp, iscsi, etc.)

### net_interfaces
Lista de interfaces de red FCP. Cada interfaz incluye:
- `lif`: Nombre de la interfaz lógica
- `data_protocol`: Protocolo de datos (fcp)
- `home_node`: Nodo home
- `home_port`: Puerto home (ejemplo: 1a, 1b, 0a, 0b)
- `status_admin`: Estado administrativo (up/down)

### mgmt_interface
Interfaz de gestión IP. Incluye:
- `lif`: Nombre de la interfaz de management
- `service_policy`: Service policy (default-management)
- `address`: Dirección IP
- `netmask`: Máscara de red
- `home_node`: Nodo home
- `home_port`: Puerto home (ejemplo: e0c, e0a)
- `status_admin`: Estado administrativo (up/down)
- `auto_revert`: Auto-revert a home port (true/false)
- `failover_group`: Grupo de failover (opcional)

Para ver ejemplos de configuración, consulta el archivo `config.yaml` incluido en el proyecto.

## Sistema de Logging

El script implementa un sistema de logging automático que captura datos REALES de la cabina NetApp después de cada operación:

### Características
- **Timestamp automático**: Formato YYYYMMDD_HHMMSS (ej: 20260129_124530)
- **Formato JSON**: Datos estructurados y fáciles de procesar
- **Datos de cabina**: GET real desde ONTAP, no configuración enviada
- **Directorio logs/**: Se crea automáticamente si no existe

### Logs Generados

1. **create_svm_YYYYMMDD_HHMMSS.json**
   - UUID de la SVM
   - Nombre, estado, ipspace
   - Agregados asignados
   - Configuración de seguridad

2. **modify_svm_YYYYMMDD_HHMMSS.json**
   - Lista de agregados configurados
   - is-space-reporting-logical
   - is-space-enforcement-logical

3. **fcp_create_YYYYMMDD_HHMMSS.json**
   - Target Name (WWPN)
   - Administrative Status
   - SVM UUID

4. **configure_protocols_YYYYMMDD_HHMMSS.json**
   - Allowed Protocols (lista)
   - Disallowed Protocols (lista)
   - Vserver UUID

5. **create_network_interfaces_YYYYMMDD_HHMMSS.json**
   - Lista completa de interfaces FC creadas
   - WWPN, nodo, puerto, estado

6. **create_management_interface_YYYYMMDD_HHMMSS.json**
   - Dirección IP/máscara
   - Nodo, puerto, estado
   - Service policy

7. **event_logs_YYYYMMDD_HHMMSS.json**
   - Backup de eventos del cluster (últimos 100)
   - Index, timestamp, nodo, severidad, evento


## Uso

### Ejecución Básica
```bash
python create_fcp_svm.py
```

### Flujo de Ejecución

1. **Carga de configuración** - Lee y valida `config.yaml`
2. **Conexión al cluster** - Establece conexión y verifica credenciales
3. **Creación de SVM** - Crea la SVM con parámetros básicos → Guarda log
4. **Modificación de SVM** - Configura agregados y espacio lógico → Guarda log
5. **Servicio FCP** - Crea y habilita el servicio FCP → Guarda log
6. **Protocolos** - Configura protocolos permitidos/no permitidos → Guarda log
7. **Interfaces FCP** - Crea todas las interfaces de datos FCP → Guarda log
8. **Interfaz Management** - Crea la interfaz de gestión → Guarda log
9. **Event Logs Backup** - Obtiene logs de eventos del cluster → Guarda log
10. **Finalización** - Todos los logs disponibles en directorio `logs/`


## API REST de NetApp

Este script utiliza la **API REST oficial de NetApp ONTAP**:

### Endpoints POST (Creación)
- **POST** `/api/svm/svms` - Creación de SVM
- **POST** `/api/protocols/san/fcp/services` - Creación servicio FCP
- **POST** `/api/network/fc/interfaces` - Creación interfaces FCP
- **POST** `/api/network/ip/interfaces` - Creación interfaz management

### Endpoints PATCH (Modificación)
- **PATCH** `/api/svm/svms/{uuid}` - Modificación de SVM y protocolos

### Endpoints GET (Consulta)
- **GET** `/api/svm/svms` - Consulta de SVMs
- **GET** `/api/protocols/san/fcp/services` - Consulta servicio FCP
- **GET** `/api/network/fc/interfaces` - Consulta de interfaces FC
- **GET** `/api/network/ip/interfaces` - Consulta de interfaces IP
- **GET** `/api/support/ems/events` - Consulta de event logs

**Documentación oficial**: [NetApp ONTAP REST API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)

## Registro de Funciones

### Funciones de Configuración y Utilidades

#### config_loader(path="config.yaml")
Carga y valida el archivo de configuración YAML.
- **Entrada**: Ruta al archivo config.yaml
- **Salida**: Diccionario con configuración o None si falla
- **Validaciones**: Verifica estructura y secciones obligatorias (cluster, svm)

#### save_to_log(operation_name, data)
Guarda datos en archivo JSON con timestamp en carpeta logs/.
- **Entrada**: Nombre de operación y diccionario de datos
- **Salida**: Ruta del archivo creado
- **Formato**: `logs/operacion_YYYYMMDD_HHMMSS.json`

#### cluster_connection(cluster_config)
Establece y verifica conexión con el cluster NetApp ONTAP.
- **Entrada**: Diccionario con host, username, password
- **Salida**: True si conexión exitosa, False si falla
- **Validaciones**: Prueba acceso con consulta al cluster

### Funciones de Gestión de SVM

#### create_svm(svm_config)
Crea una Storage Virtual Machine con parámetros básicos.
- **Entrada**: Configuración de SVM desde config.yaml
- **Salida**: True si se creó, False si error
- **POST**: `/api/svm/svms`
- **Log**: `create_svm_YYYYMMDD_HHMMSS.json`

#### modify_svm(svm_config)
Modifica parámetros de espacio lógico y lista de agregados.
- **Entrada**: Configuración de SVM con aggr_list y parámetros de espacio
- **Salida**: True si modificación exitosa, False si error
- **PATCH**: `/api/svm/svms/{uuid}`
- **Log**: `modify_svm_YYYYMMDD_HHMMSS.json`

### Funciones de Configuración FCP

#### fcp_create(svm_config)
Crea y habilita el servicio FCP en la SVM.
- **Entrada**: Configuración de SVM con fcp_status_admin
- **Salida**: True si se creó, False si error
- **POST**: `/api/protocols/san/fcp/services`
- **Log**: `fcp_create_YYYYMMDD_HHMMSS.json`

#### configure_protocols(svm_config)
Configura protocolos permitidos y no permitidos en la SVM.
- **Entrada**: Configuración de SVM con diccionario de protocolos
- **Salida**: True si configuración exitosa, False si error
- **PATCH**: `/api/svm/svms/{uuid}`
- **Log**: `configure_protocols_YYYYMMDD_HHMMSS.json`

### Funciones de Interfaces de Red

#### create_network_interfaces(svm_name, net_interfaces_config)
Crea múltiples interfaces de red FCP (LIFs FC).
- **Entrada**: Nombre de SVM y lista de configuraciones de interfaces
- **Salida**: True si todas se crearon, False si error
- **POST**: `/api/network/fc/interfaces`
- **Log**: `create_network_interfaces_YYYYMMDD_HHMMSS.json`

#### create_management_interface(svm_name, mgmt_config)
Crea la interfaz de gestión IP con service policy.
- **Entrada**: Nombre de SVM y configuración de interfaz management
- **Salida**: True si se creó, False si error
- **POST**: `/api/network/ip/interfaces`
- **Log**: `create_management_interface_YYYYMMDD_HHMMSS.json`

### Funciones de Monitoreo

#### get_event_logs(max_records=100)
Obtiene y respalda los logs de eventos del cluster.
- **Entrada**: Número máximo de registros (default: 100)
- **Salida**: True si se obtuvieron, False si error
- **GET**: `/api/support/ems/events`
- **Log**: `event_logs_YYYYMMDD_HHMMSS.json`

## Registro de Errores

### Errores de Configuración

#### ERR-001: Archivo de configuración no encontrado
```
[ERROR] File not found: config.yaml
```
**Causa**: El archivo config.yaml no existe en el directorio actual  
**Solución**: Verificar que config.yaml existe en la misma carpeta que el script

#### ERR-002: YAML inválido
```
[ERROR] Invalid YAML format in 'config.yaml'
```
**Causa**: Sintaxis YAML incorrecta (indentación, formato)  
**Solución**: Validar sintaxis YAML, verificar espacios e indentación

#### ERR-003: Configuración incompleta
```
[ERROR] Incomplete configuration: missing 'cluster' section
[ERROR] Incomplete configuration: missing 'svm' section
```
**Causa**: Faltan secciones obligatorias en config.yaml  
**Solución**: Asegurar que config.yaml contenga secciones 'cluster' y 'svm'

#### ERR-004: Campos obligatorios faltantes
```
[ERROR] Missing required fields in cluster config: host, username
```
**Causa**: Faltan campos obligatorios en la configuración del cluster  
**Solución**: Completar todos los campos requeridos (host, username, password)

### Errores de Conexión

#### ERR-101: Error de autenticación
```
[ERROR] HTTP status: 401
[ERROR] Authentication failed
[ERROR] Invalid username or password
```
**Causa**: Credenciales incorrectas  
**Solución**: Verificar username y password en config.yaml

#### ERR-102: Acceso denegado
```
[ERROR] HTTP status: 403
[ERROR] Forbidden - User lacks required permissions
```
**Causa**: Usuario sin permisos de administrador  
**Solución**: Usar cuenta con rol admin o vsadmin

#### ERR-103: Host no alcanzable
```
[ERROR] Cannot reach host 'cluster1.demo.netapp.com'
```
**Causa**: Problemas de red o hostname incorrecto  
**Solución**: Verificar conectividad de red y hostname/IP del cluster

#### ERR-104: Timeout de conexión
```
[ERROR] Connection timeout to 'cluster1.demo.netapp.com'
```
**Causa**: Cluster no responde  
**Solución**: Verificar que el cluster esté encendido y accesible

### Errores de Creación de SVM

#### ERR-201: SVM ya existe
```
[ERROR] SVM 'svm_name' already exists on the cluster
```
**Causa**: Ya existe una SVM con ese nombre  
**Solución**: Cambiar nombre en config.yaml o eliminar SVM existente

#### ERR-202: Agregado no existe
```
[ERROR] Aggregate 'aggr1' doesn't exist (check aggregate name)
```
**Causa**: Nombre de agregado incorrecto o no existe  
**Solución**: Ejecutar `storage aggregate show` para ver agregados disponibles

#### ERR-203: IPspace inválido
```
[ERROR] Bad request - Invalid ipspace name
```
**Causa**: IPspace especificado no existe  
**Solución**: Verificar IPspaces con `network ipspace show`

#### ERR-204: Código de idioma inválido
```
[ERROR] Bad request - Invalid language code
```
**Causa**: Código de idioma no soportado  
**Solución**: Usar códigos válidos: c.utf_8, en_us.utf_8, etc.

### Errores de Servicio FCP

#### ERR-301: Servicio FCP ya existe
```
[ERROR] FCP service may already exist on this SVM
```
**Causa**: La SVM ya tiene servicio FCP configurado  
**Solución**: Verificar con `vserver fcp show -vserver <name>`

#### ERR-302: Licencia FCP no disponible
```
[ERROR] FCP license not installed
```
**Causa**: Cluster sin licencia FCP  
**Solución**: Instalar licencia FCP en el cluster

### Errores de Interfaces de Red

#### ERR-401: Nombre de puerto inválido
```
[ERROR] "1a" is an invalid value for field "location.home_port.name"
```
**Causa**: Falta prefijo en nombre del puerto  
**Solución**: Usar formato correcto: `e1a` en lugar de `1a`

#### ERR-402: Puerto no existe
```
[ERROR] Port 'e9a' does not exist on node 'cluster1-01'
```
**Causa**: Puerto especificado no existe en el nodo  
**Solución**: Verificar puertos con `network port show -node <node>`

#### ERR-403: Nodo no existe
```
[ERROR] Node 'cluster1-05' not found
```
**Causa**: Nombre de nodo incorrecto  
**Solución**: Verificar nodos con `cluster show`

#### ERR-404: Interfaz ya existe
```
[ERROR] Interface 'lif1' already exists
```
**Causa**: Ya existe una LIF con ese nombre  
**Solución**: Cambiar nombre de LIF en config.yaml

#### ERR-405: Dirección IP duplicada
```
[ERROR] IP address 192.168.0.1 is already in use
```
**Causa**: Dirección IP ya asignada a otra interfaz  
**Solución**: Usar una dirección IP diferente

#### ERR-406: Máscara de red inválida
```
[ERROR] Invalid netmask format
```
**Causa**: Formato de netmask incorrecto  
**Solución**: Usar formato decimal: 255.255.255.0

#### ERR-407: Service policy no existe
```
[ERROR] Service policy 'invalid-policy' not found
```
**Causa**: Service policy especificado no existe  
**Solución**: Usar policies predefinidos: default-management, default-data-files

### Errores de Protocolos

#### ERR-501: Protocolo no soportado
```
[ERROR] Bad request - Invalid protocol configuration
```
**Causa**: Nombre de protocolo inválido  
**Solución**: Usar protocolos válidos: nfs, cifs, fcp, iscsi, nvme, s3, ndmp

#### ERR-502: Conflicto de protocolos
```
[ERROR] Cannot enable both NFS and CIFS without proper configuration
```
**Causa**: Configuración de protocolos incompatible  
**Solución**: Configurar security-style adecuado para multiprotocolo

### Errores de Event Logs

#### ERR-601: No se pueden obtener event logs
```
[WARNING] Event logs backup failed (non-critical)
```
**Causa**: Error al consultar API de eventos  
**Solución**: No crítico, verificar permisos de lectura de eventos

### Códigos de Estado HTTP Comunes

- **400 Bad Request**: Parámetros inválidos en la solicitud
- **401 Unauthorized**: Credenciales incorrectas
- **403 Forbidden**: Sin permisos suficientes
- **404 Not Found**: Recurso no existe
- **409 Conflict**: Recurso ya existe o conflicto de estado
- **500 Internal Server Error**: Error interno del servidor ONTAP

## Seguridad

- **IMPORTANTE**: NO compartas el archivo `config.yaml` con credenciales
- Considera usar variables de entorno para credenciales sensibles
- El script desactiva verificación SSL (`verify=False`) - úsalo solo en entornos de desarrollo/pruebas
- Los logs pueden contener información sensible - protege el directorio `logs/`

## Licencia

Este script es para uso interno y educativo.

## Soporte

Para problemas relacionados con la API de NetApp, consulta:
- [Documentación API REST](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)
- [NetApp Community](https://community.netapp.com/)
- [Python Client Library](https://pypi.org/project/netapp-ontap/)

---

**Versión**: 1.0  
**Última actualización**: Febrero 2026  
**Compatible con**: ONTAP 9.6+
