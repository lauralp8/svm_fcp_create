# Sistema de Logging y Backup - NetApp ONTAP SVM Creation

## 📋 Descripción

Este script implementa un sistema completo de logging que **captura datos REALES de la cabina NetApp** después de cada operación, guardándolos en archivos JSON con timestamp.

## 📂 Estructura de Logs

```
CreateSVM/
├── logs/                                          # Carpeta creada automáticamente
│   ├── create_svm_20260129_112530_SUCCESS.json
│   ├── modify_svm_20260129_112531_SUCCESS.json
│   ├── fcp_create_20260129_112532_SUCCESS.json
│   ├── configure_protocols_20260129_112533_SUCCESS.json
│   ├── create_network_interfaces_20260129_112534_SUCCESS.json
│   └── create_management_interface_20260129_112535_SUCCESS.json
```

## 🔍 Funciones de Obtención de Datos (GET)

Todas las funciones implementan GETs según la **documentación oficial de NetApp ONTAP REST API**:

### 1. `get_svm_details(svm_name)`
**API Endpoint**: `GET /api/svm/svms/{uuid}`

**Datos obtenidos**:
- UUID de la SVM
- Estado (running/stopped)
- IPspace (nombre y UUID)
- Language
- Security style
- Agregados (lista con nombres y UUIDs)
- Logical space settings (reporting/enforcement)

### 2. `get_fcp_service_details(svm_name)`
**API Endpoint**: `GET /api/protocols/san/fcp/services`

**Datos obtenidos**:
- Estado enabled del servicio FCP
- Target name

### 3. `get_fc_interfaces_details(svm_name)`
**API Endpoint**: `GET /api/network/fc/interfaces`

**Datos obtenidos** (por cada interfaz):
- UUID de la interfaz
- Nombre
- Data protocol (fcp/fc-nvme)
- Estado enabled
- **WWPN** (World Wide Port Name) - Crítico para zonas FC
- Location (home_node, home_port)

### 4. `get_ip_interface_details(svm_name, lif_name)`
**API Endpoint**: `GET /api/network/ip/interfaces`

**Documentación**: [NetApp IP Interface API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/ip_interface.html)

**Datos obtenidos**:
- UUID de la interfaz
- Nombre y SVM (con UUID)
- Estado enabled y state
- IP address y netmask
- Location (home_node, home_port, auto_revert)
- Service policy (nombre y UUID)

### 5. `get_protocols_details(svm_name)`
**API Endpoint**: `GET /api/svm/svms/{uuid}`

**Datos obtenidos**:
- Estado allowed de cada protocolo (nfs, cifs, fcp, iscsi, nvme)
- Estado enabled de cada protocolo

## 📄 Formato del Log JSON

Cada archivo JSON contiene:

```json
{
  "operation": "create_svm",
  "timestamp": "2026-01-29T11:25:30.456789",
  "status": "SUCCESS",
  "configuration_sent": {
    "name": "SVMv2-cert-rhoso-san3000",
    "ipspace": "Default",
    "language": "es",
    "aggregate": "aggr1"
  },
  "cluster_response": {
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "SVMv2-cert-rhoso-san3000",
    "state": "running",
    "ipspace": {
      "name": "Default",
      "uuid": "12345678-1234-1234-1234-123456789abc"
    },
    "aggregates": [
      {
        "name": "aggr1",
        "uuid": "87654321-4321-4321-4321-210987654321"
      }
    ]
  },
  "error_message": null
}
```

## 🎯 Ventajas del Sistema

✅ **Trazabilidad completa**: Cada operación queda registrada con datos reales de la cabina  
✅ **UUIDs capturados**: Esenciales para operaciones futuras y auditoría  
✅ **Timestamps precisos**: Formato YYYYMMDD_HHMMSS para ordenación cronológica  
✅ **Comparación config vs reality**: Puedes validar que lo enviado coincide con lo creado  
✅ **Debugging profesional**: Logs de errores con código HTTP y detalles  
✅ **WWPNs guardados**: Críticos para configuración de SAN zones  
✅ **Auditoría y compliance**: Registro completo de todas las operaciones  

## 🔧 Uso Automático

El sistema funciona automáticamente en cada operación:

```python
# Ejemplo interno en create_svm()
new_svm.post()  # Crear SVM en la cabina

# Obtener datos REALES de la cabina
cluster_data = get_svm_details(svm_name)

# Guardar log con datos reales
save_operation_log('create_svm', svm_config, 
                   cluster_response=cluster_data, 
                   status='SUCCESS')
```

## 📊 Operaciones Registradas

| Operación | Nombre del Log | Datos de Cabina Incluidos |
|-----------|----------------|---------------------------|
| Crear SVM | `create_svm_TIMESTAMP_SUCCESS.json` | UUID, estado, aggregates, ipspace |
| Modificar SVM | `modify_svm_TIMESTAMP_SUCCESS.json` | Aggregates, logical space settings |
| Crear servicio FCP | `fcp_create_TIMESTAMP_SUCCESS.json` | Estado enabled, target name |
| Configurar protocolos | `configure_protocols_TIMESTAMP_SUCCESS.json` | Estado allowed/enabled por protocolo |
| Crear interfaces FC | `create_network_interfaces_TIMESTAMP_SUCCESS.json` | UUIDs, WWPNs, location, estado |
| Crear interfaz mgmt | `create_management_interface_TIMESTAMP_SUCCESS.json` | UUID, IP, service policy, location |

## 🚨 Logs de Error

En caso de error, se genera un log con sufijo `_ERROR.json`:

```json
{
  "operation": "create_svm",
  "timestamp": "2026-01-29T11:25:30.456789",
  "status": "ERROR",
  "configuration_sent": { ... },
  "cluster_response": null,
  "error_message": "HTTP 400: Aggregate 'aggr99' does not exist"
}
```

## 🔍 Consultar Logs

```powershell
# Ver todos los logs exitosos
Get-ChildItem logs\*_SUCCESS.json | Sort-Object Name

# Ver logs de errores
Get-ChildItem logs\*_ERROR.json

# Leer un log específico
Get-Content logs\create_svm_20260129_112530_SUCCESS.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

## 📚 Referencias API NetApp

- [SVM API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/svm.html)
- [IP Interface API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/ip_interface.html)
- [FC Interface API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/fc_interface.html)
- [FCP Service API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/fcp_service.html)

---

**Nota**: Los logs contienen datos REALES obtenidos de la cabina mediante GETs, no solo la configuración enviada.
