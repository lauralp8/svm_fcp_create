# NetApp ONTAP SVM Creation Script

Script automatizado para la creación y configuración completa de Storage Virtual Machines (SVMs) en NetApp ONTAP usando la API REST oficial.

## Descripción

Este script de Python automatiza todo el proceso de creación de una SVM en NetApp ONTAP, incluyendo:

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
CreateSVM/
├── create_svm.py      # Script principal
├── config.yaml        # Archivo de configuración
├── requirements.txt   # Dependencias Python
├── README.md          # Esta documentación
└── logs/              # Logs JSON generados automáticamente
    ├── create_svm_YYYYMMDD_HHMMSS.json
    ├── modify_svm_YYYYMMDD_HHMMSS.json
    ├── fcp_create_YYYYMMDD_HHMMSS.json
    ├── configure_protocols_YYYYMMDD_HHMMSS.json
    ├── create_network_interfaces_YYYYMMDD_HHMMSS.json
    ├── create_management_interface_YYYYMMDD_HHMMSS.json
    └── event_logs_YYYYMMDD_HHMMSS.json
```

## Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno:

### 1. Configuración del Cluster
```yaml
cluster:
  host: cluster1.demo.netapp.com
  username: admin
  password: Netapp1!
```

### 2. Configuración de la SVM
```yaml
svm: 
  name: svm_demo2
  ipspace: Default  
  aggregate: cluster1_01_SSD_1
  language: c.utf_8
  security_style: unix
  
  # Parámetros de modificación
  aggr_list:
    - cluster1_01_SSD_1
    - cluster1_02_SSD_1
  is_space_reporting_logical: true
  is_space_enforcement_logical: true
  
  # Parámetros FCP
  fcp_status_admin: true  # true = up, false = down
  
  # Protocolos permitidos
  protocols:
    cifs: false
    nfs: false
    fcp: true
    iscsi: true
```

### 3. Interfaces de Red FCP
Puedes definir múltiples interfaces FCP:

```yaml
net_interfaces:
  - lif: LIF1
    data_protocol: fcp
    home_node: cluster1-01
    home_port: e1a  # Debe incluir prefijo 'e' para ethernet
    status_admin: true
  
  - lif: LIF2
    data_protocol: fcp
    home_node: cluster1-02
    home_port: e1b
    status_admin: true
```

### 4. Interfaz de Management
```yaml
mgmt_interface:
  lif: lif_mgmt
  service_policy: default-management
  address: 192.168.0.1
  netmask: 255.255.255.0
  home_node: cluster1-01
  home_port: e0a
  status_admin: true
  auto_revert: false
  failover_group: Default
```

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

### Ejemplo de Uso de Logs
```bash
# Ver último log de creación de SVM
cat logs/create_svm_*.json | tail -1 | jq .

# Extraer UUIDs de todas las SVMs creadas
cat logs/create_svm_*.json | jq -r '.uuid'

# Ver event logs más recientes
cat logs/event_logs_*.json | tail -1 | jq '.events[] | select(.severity=="alert")'
```

## Uso

### Ejecución Básica
```bash
python create_svm.py
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

### Ejemplo de Salida
```
Starting SVM creation script...
Config.yaml loader: config.yaml
Configuration loaded successfully
Target cluster: cluster1.demo.netapp.com
SVM to create: svm_demo2

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: 9.14.1

[*] Creating SVM: svm_demo2
[+] SVM 'svm_demo2' created successfully!

[SUCCESS] SVM creation completed!
...
```

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

## Notas Importantes

### Failover Policy y Firewall Policy

**IMPORTANTE**: En ONTAP moderno, estos parámetros están controlados automáticamente por el `service_policy`:

- `failover_policy` - **NO configurable directamente**. El service-policy lo determina automáticamente.
- `firewall_policy` - **DEPRECATED**. Ya no se usa en ONTAP 9.6+.

Cuando usas `service_policy: default-management`, ONTAP asigna:
- `failover_policy: system-defined` (equivale a `broadcast_domain_only`)
- `firewall_policy: mgmt` (valor legacy, ignorado)

### Prefijos de Puertos

Los puertos deben incluir su prefijo:
- **Ethernet**: `e0a`, `e1a`, `e2a`, etc.
- **FCoE**: `a0a`, `a0b`, etc.

### Protocolos FCP vs NFS/CIFS

- **FCP/FC-NVMe**: Usan `FcInterface` (no requieren IP)
- **NFS/CIFS/iSCSI**: Usan `IpInterface` (requieren IP address)

## Troubleshooting

### Error: "SVM already exists"
```
[ERROR] SVM 'svm_name' already exists with UUID: xxx
```
**Solución**: Cambia el nombre de la SVM en `config.yaml` o elimina la SVM existente.

### Error: "Aggregate doesn't exist"
```
[ERROR] - Aggregate 'aggr1' doesn't exist (check aggregate name)
```
**Solución**: Verifica los agregados disponibles con `storage aggregate show`.

### Error: "Invalid port name"
```
[ERROR] "1a" is an invalid value for field "location.home_port.name"
```
**Solución**: Añade el prefijo al puerto (ej: `e1a` en lugar de `1a`).

### Error: "Authentication failed"
```
[ERROR] Invalid username or password
```
**Solución**: Verifica las credenciales en `config.yaml`.

## Comandos CLI Equivalentes

Este script automatiza los siguientes comandos CLI:

```bash
# Crear SVM
vserver create -vserver svm_name -rootvolume root -aggregate aggr1 \
  -rootvolume-security-style unix -language C.UTF-8

# Modificar SVM
vserver modify -vserver svm_name -aggr-list aggr1,aggr2 \
  -is-space-reporting-logical true -is-space-enforcement-logical true

# Crear servicio FCP
vserver fcp create -vserver svm_name -status-admin up

# Configurar protocolos
vserver remove-protocols -vserver svm_name -protocols cifs,nfs
vserver add-protocols -vserver svm_name -protocols fcp,iscsi

# Crear interfaz FCP
network interface create -vserver svm_name -lif lif1 \
  -data-protocol fcp -home-node node1 -home-port e1a -status-admin up

# Crear interfaz management
network interface create -vserver svm_name -lif lif_mgmt \
  -service-policy default-management -address 192.168.0.1 \
  -netmask 255.255.255.0 -home-node node1 -home-port e0a \
  -status-admin up -auto-revert false
```

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
**Última actualización**: Enero 2026  
**Compatible con**: ONTAP 9.6+
