from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Cluster, Svm, FcpService, FcInterface, IpInterface
import yaml

print("\nCREATE SVM SCRIPT USING NETAPP ONTAP PYTHON CLIENT LIBRARY")
print("[*] Starting SVM creation script...")

def config_loader(path="config.yaml"):
    """
    Carga la configuración desde un archivo YAML con validación completa
    
    Lee el archivo de configuración y valida que contenga las secciones
    necesarias para crear una SVM en NetApp ONTAP.
    
    Args:
        path: Ruta al archivo de configuración (por defecto 'config.yaml')
    
    Returns:
        dict: Diccionario con la configuración cargada, o None si falla
    """
    try:
        print(f"[+] Config.yaml loader: {path}")
        
        # Abrir y leer el contenido del archivo YAML
        with open(path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
        # VALIDACIONES
        # Validar que el archivo no esté vacío
        if config_data is None:
            print(f"[ERROR] File '{path}' is empty or doen't contain valid YAML")
            return None
        
        # Validar estructura: debe contener seccion 'cluster'
        if 'cluster' not in config_data:
            print(f"[ERROR]Incomplete configuration: missing 'cluster' section")
            return None
        
        # Validar estructura: debe contener seccion 'svm'
        if 'svm' not in config_data:
            print(f"[ERROR] Incomplete configuration: missing 'svm' section")
            return None
        
        print(f"[+] Configuration loaded successfully")

        # Mostrar resumen de la configuración cargada
        print(f"[+] Target cluster: {config_data['cluster'].get('host', 'N/A')}")
        print(f"[+] SVM to create: {config_data['svm'].get('name', 'N/A')}")
        
        return config_data
    
    # CONTROL DE ERRORES
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        print(f"[ERROR] Please check the path and try again")
        return None
    
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML format in '{path}'")
        print(f"[ERROR] Detail: {str(e)}")
        return None
    
    except PermissionError:
        print(f"[ERROR] Insufficient permissions to read: {path}")
        return None
    
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return None


def cluster_connection(cluster_config):
    """
    Establece conexión con la cabina NetApp ONTAP y verifica acceso
    
    Conecta con el cluster usando las credenciales proporcionadas y realiza
    una consulta de prueba para validar que el acceso es correcto.
    
    Args:
        cluster_config: Diccionario con claves 'host', 'username', 'password'
    
    Returns:
        bool: True si conexión exitosa, False si hay errores
    """
    try:
        print(f"\n[*] Establishing connection to cluster: {cluster_config.get('host', 'N/A')}")
        
        # Validar que existan todos los campos necesarios
        required_keys = ['host', 'username', 'password']
        # Itera por cada clave requerida y guarda en una lista las que faltan
        missing_keys = [key for key in required_keys if key not in cluster_config]
        
        if missing_keys:
            print(f"[ERROR] Missing required fields in cluster config: {', '.join(missing_keys)}")
            return False
        
        # Establecer conexión con la cabina
        config.CONNECTION = HostConnection(
            cluster_config['host'],
            username=cluster_config['username'],
            password=cluster_config['password'],
            verify=False 
        )
        
        # Verificar acceso haciendo una consulta al cluster
        cluster_info = Cluster()
        cluster_info.get()
        
        print(f"[+] Connection successful!")
        print(f"[+] Cluster name: {cluster_info.name}")
        print(f"[+] ONTAP version: {cluster_info.version.full}")

        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp REST API error")
        print(f"[ERROR] HTTP status: {error.status_code}")
        
        # Detallar el tipo de error según el código HTTP
        if error.status_code == 401:
            print(f"[ERROR] Authentication failed")
            print(f"[ERROR] Invalid username or password for user '{cluster_config.get('username')}'")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
        elif error.status_code == 404:
            print(f"[ERROR] Resource not found - Check cluster URL")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Configuration error - Missing key: {str(e)}")
        return False
    
    except ConnectionError:
        print(f"[ERROR] Cannot reach host '{cluster_config.get('host')}'")
        print(f"[ERROR] Check network connectivity and hostname/IP")
        return False
    
    except TimeoutError:
        print(f"[ERROR] Connection timeout to '{cluster_config.get('host')}'")
        print(f"[ERROR] Cluster is not responding")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return False


def create_svm(svm_config):
    """
    Crea una SVM en NetApp ONTAP con los parámetros del config.yaml
    
    Args:
        svm_config: Diccionario con la configuración de la SVM desde config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer parámetros del config.yaml
        svm_name = svm_config.get('name')
        ipspace = svm_config.get('ipspace')
        language = svm_config.get('language')
        security_style = svm_config.get('security_style')
        aggregate = svm_config.get('aggregate')
        
        # VALIDACIONES
        # Validar que exista el valor obligatorio 'name'
        if not svm_name:
            print(f"[ERROR] 'name' is required in svm configuration")
            return False
        
        print(f"\n[*] Creating SVM: {svm_name}")
        
        # Verificar si la SVM ya existe
        print(f"[*] Checking if SVM already exists...")
        existing_svm = Svm.find(name=svm_name)
        if existing_svm:
            print(f"[ERROR] SVM '{svm_name}' already exists on the cluster")
            return False
        
        # SVM
        # Crear objeto SVM
        new_svm = Svm()
        new_svm.name = svm_name
        
        # DATOS ENVIADOS AL CLÚSTER DESDE EL CONFIG.YAML
        # Configurar IPspace 
        if ipspace:
            new_svm.ipspace = {'name': ipspace}
            print(f"[*] IPspace: {ipspace}")
        
        # Configurar idioma
        if language:
            new_svm.language = language
            print(f"[*] Language: {language}")
        
        # Configurar security style
        if security_style:
            new_svm.security_style = security_style
            print(f"[*] Security Style: {security_style}")
        
        # Especificar el agregado para el volumen raíz
        new_svm.aggregates = [{'name': aggregate}]
        print(f"[*] Aggregate: {aggregate}")
        
        # Enviar petición de creación al cluster
        print(f"[*] Sending creation request...")
        new_svm.post()
        
        print(f"[+] SVM '{svm_name}' created successfully!")
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during SVM creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        # Proporcionar información detallada según el error
        if error.status_code == 409:
            print(f"[ERROR] Conflict - SVM may already exist or name is in use")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
            print(f"[ERROR] Common causes:")
            print(f"[ERROR] - Aggregate 'aggr1' doesn't exist (check aggregate name)")
            print(f"[ERROR] - Invalid ipspace name")
            print(f"[ERROR] - Invalid language code")
            print(f"[ERROR] Response: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Response: {error.http_err_response.http_response.text}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Missing required configuration key: {str(e)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during SVM creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def modify_svm(svm_config):
    """
    Modifica una SVM configurando parámetros de espacio lógico
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se modificó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer lista de agregados del config.yaml
        aggr_list = svm_config.get('aggr_list', [])

        # Extraer valores de espacio lógico del config.yaml
        space_reporting = svm_config.get('is_space_reporting_logical', False)
        space_enforcement = svm_config.get('is_space_enforcement_logical', False)
        
        
        print(f"\n[*] Modifying SVM: {svm_name}")
        
        # Buscar la SVM
        svm = Svm.find(name=svm_name)
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found")
            return False
        
        # Configurar lista de agregados desde config.yaml
        if aggr_list:
            svm.aggregates = [{'name': aggr} for aggr in aggr_list]
            print(f"[*] Aggregate list: {', '.join(aggr_list)}")
        
        # Configurar parámetros de espacio lógico desde config.yaml
        svm.is_space_reporting_logical = space_reporting
        svm.is_space_enforcement_logical = space_enforcement
        
        print(f"[*] is_space_reporting_logical: {space_reporting}")
        print(f"[*] is_space_enforcement_logical: {space_enforcement}")
        
        # Aplicar cambios
        print(f"[*] Applying changes...")
        svm.patch()
        
        print(f"[+] SVM '{svm_name}' modified successfully!")
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def fcp_create(svm_config):
    """
    Crea un servicio FCP en la SVM y lo configura con status-admin desde config.yaml
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer status_admin del config.yaml 
        fcp_status_admin = svm_config.get('fcp_status_admin', False)
        
        print(f"\n[*] Creating FCP service on SVM: {svm_name}")
        
        # Crear objeto FCP service
        fcp = FcpService()
        fcp.svm = {'name': svm_name}
        fcp.enabled = fcp_status_admin
        
        # Crear el servicio FCP
        print(f"[*] Creating FCP service...")
        fcp.post()
        
        # Mostrar estado del servicio como up/down
        status_text = "up" if fcp_status_admin else "down"
        print(f"[+] FCP service created successfully!")
        print(f"[*] Status admin: {status_text}")
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during FCP creation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 409:
            print(f"[ERROR] FCP service may already exist on this SVM")
        elif error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid parameters")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during FCP creation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def configure_protocols(svm_config):
    """
    Configura los protocolos permitidos en la SVM (allowed=true/false)
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
                    Debe incluir la sección 'protocols' con cada protocolo y su valor
    
    Returns:
        bool: True si se configuró exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer diccionario de protocolos del config.yaml
        protocols_config = svm_config.get('protocols', {})
        
        # Validar que haya protocolos para configurar
        if not protocols_config:
            print(f"[WARNING] No protocol configuration found in config.yaml")
            return True
        
        print(f"\n[*] Configuring protocols for SVM: {svm_name}")
        
        # Buscar la SVM
        svm = Svm.find(name=svm_name)
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found")
            return False
        
        # Obtener el objeto SVM completo
        svm_obj = Svm(uuid=svm.uuid)
        
        # Configurar cada protocolo según el config.yaml
        for protocol, allowed in protocols_config.items():
            # Convertir el nombre del protocolo a minúsculas por si acaso
            protocol_name = protocol.lower()
            
            # Configurar el protocolo con el valor allowed
            setattr(svm_obj, protocol_name, {'allowed': allowed})
            
            status_text = "enabled" if allowed else "disabled"
            print(f"[*] Protocol {protocol_name.upper()}: {status_text}")
        
        # Aplicar cambios a la SVM
        print(f"[*] Applying protocol changes...")
        svm_obj.patch()
        
        print(f"[+] Protocol configuration applied successfully!")
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during protocol configuration")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 400:
            print(f"[ERROR] Bad request - Invalid protocol configuration")
            print(f"[ERROR] Check that protocol names are valid")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during protocol configuration: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def create_network_interfaces(svm_name, net_interfaces_config):
    """
    Crea network interfaces (LIFs) usando la API REST de ONTAP

    Args:
        svm_name: Nombre de la SVM
        net_interfaces_config: Lista de diccionarios con configuración de interfaces
    
    Returns:
        bool: True si todas se crearon exitosamente
    """
    try:
        # Validar que haya interfaces para crear
        if not net_interfaces_config:
            print(f"[WARNING] No network interfaces configured")
            return True
        
        print(f"\n[*] Creating {len(net_interfaces_config)} network interface(s) for SVM: {svm_name}")
        
        # Iterar por cada configuración de interfaz del config.yaml 
        for idx, interface_config in enumerate(net_interfaces_config, start=1):
            lif_name = interface_config.get('lif')
            data_protocol = interface_config.get('data_protocol')
            home_node = interface_config.get('home_node')
            home_port = interface_config.get('home_port')
            status_admin = interface_config.get('status_admin', False)
            
            if not all([lif_name, home_node, home_port]):
                print(f"[ERROR] Interface #{idx}: Missing required fields (lif, home_node, home_port)")
                return False
            
            print(f"\n[*] Creating interface #{idx}: {lif_name}")
            
            # Crear objeto FcInterface para protocolos FCP (SAN)
            net_interface = FcInterface()
            net_interface.name = lif_name
            net_interface.svm = {'name': svm_name}
            
            # Configurar location (home_node y home_port con node)
            net_interface.location = {
                'home_node': {'name': home_node},
                'home_port': {
                    'name': home_port,
                    'node': {'name': home_node}
                }
            }
            
            # Configurar data_protocol
            net_interface.data_protocol = data_protocol

            # Configurar status-admin (enabled: true=up, false=down)
            if status_admin:
                net_interface.enabled = 'up'
            else:
                net_interface.enabled = 'down'
            
            # POST a la API
            net_interface.post()
            
            print(f"[+] Interface '{lif_name}' created successfully")
            print(f"    - Home: {home_node}:{home_port}")
            print(f"    - Protocol: {data_protocol}")
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def show_network_interfaces(svm_name, lif_names):
    """
    Muestra información de las network interfaces creadas
    
    API: GET /api/network/fc/interfaces
    Equivalente CLI: network interface show -vserver <svm> -lif <name>
    
    Args:
        svm_name: Nombre de la SVM
        lif_names: Lista de nombres de LIFs a mostrar
    
    Returns:
        bool: True si se consultó exitosamente
    """
    try:
        if not lif_names:
            return True
        
        print(f"\n[*] Showing network interfaces for SVM: {svm_name}")
        print(f"{'='*80}")
        
        for lif_name in lif_names:
            # GET usando la API REST con filtros
            interfaces = FcInterface.get_collection(
                **{'svm.name': svm_name, 'name': lif_name}
            )
            
            for interface in interfaces:
                # Obtener detalles completos del objeto
                interface.get()
                
                print(f"\nLIF: {interface.name}")
                print(f"  SVM: {interface.svm.name}")
                print(f"  Home Node: {interface.location.home_node.name}")
                print(f"  Home Port: {interface.location.home_port.name}")
                print(f"  Data Protocol: {interface.data_protocol if hasattr(interface, 'data_protocol') else 'fcp'}")
                print(f"  State: {interface.state if hasattr(interface, 'state') else 'N/A'}")
                if hasattr(interface, 'uuid'):
                    print(f"  UUID: {interface.uuid}")
                if hasattr(interface, 'wwpn'):
                    print(f"  WWPN: {interface.wwpn}")
        
        print(f"{'='*80}")
        return True
    
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


def create_management_interface(svm_name, mgmt_config):
    """
    Crea una interfaz de management (LIF) usando la API REST de ONTAP
    
    API: POST /api/network/ip/interfaces
    Basado en: https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/ip_interface.html
    
    Equivalente CLI: network interface create -vserver <svm> -lif <name> 
                     -service-policy <policy> -address <ip> -netmask <mask>
                     -home-node <node> -home-port <port> -status-admin <up|down>
                     -auto-revert <true|false> -failover-group <group>
    
    Args:
        svm_name: Nombre de la SVM
        mgmt_config: Diccionario con configuración de la interfaz del config.yaml
    
    Returns:
        bool: True si se creó exitosamente
    """
    try:
        if not mgmt_config:
            print(f"[WARNING] No management interface configured")
            return True
        
        # Extraer todos los parámetros del config.yaml (sin valores por defecto hardcodeados)
        lif = mgmt_config.get('lif')
        service_policy = mgmt_config.get('service_policy')
        address = mgmt_config.get('address')
        netmask = mgmt_config.get('netmask')
        home_node = mgmt_config.get('home_node')
        home_port = mgmt_config.get('home_port')
        status_admin = mgmt_config.get('status_admin', True)
        auto_revert = mgmt_config.get('auto_revert', False)
        failover_group = mgmt_config.get('failover_group')
        
        # Validar campos obligatorios
        if not all([lif, service_policy, address, netmask, home_node, home_port]):
            print(f"[ERROR] Management interface: Missing required fields")
            print(f"[ERROR] Required: lif, service_policy, address, netmask, home_node, home_port")
            return False
        
        print(f"\n[*] Creating management interface: {lif}")
        print(f"[*] Service Policy: {service_policy}")
        print(f"[*] Address: {address}/{netmask}")
        print(f"[*] Home: {home_node}:{home_port}")
        print(f"[*] Auto Revert: {auto_revert}")
        if failover_group:
            print(f"[*] Failover Group: {failover_group}")
        
        # Crear objeto IpInterface usando la API REST
        interface = IpInterface()
        interface.name = lif
        interface.svm = {'name': svm_name}
        
        # Configurar dirección IP y máscara
        interface.ip = {
            'address': address,
            'netmask': netmask
        }
        
        # Configurar location (home_node, home_port, auto_revert)
        interface.location = {
            'home_node': {'name': home_node},
            'home_port': {
                'name': home_port,
                'node': {'name': home_node}
            },
            'auto_revert': auto_revert
        }
        
        # Configurar service policy
        interface.service_policy = {'name': service_policy}
        
        # Configurar failover group si se especifica
        if failover_group:
            interface.location['failover_group'] = {'name': failover_group}
        
        # Configurar enabled (status-admin: up=true, down=false)
        interface.enabled = status_admin
        
        # POST a la API
        interface.post()
        
        print(f"[+] Management interface '{lif}' created successfully")
        
        return True
    
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# CONFIG YAML LOADER
# Cargar la configuración desde el archivo YAML
config_data = config_loader()

# Verificar que la configuración se cargó exitosamente
if config_data is None:
    print("\n[ERROR] Cannot continue without valid configuration")
    print("[ERROR] Check the config.yaml file and try again")
    exit(1)
else:
    print("\n[SUCCESS] Configuration loaded - Proceeding with pre-checks")

# CLUSTER CONNECTION CHECK
# Establecer conexión y verificar acceso a la cabina NetApp
if not cluster_connection(config_data['cluster']):
    print("\n[ERROR] Failed to connect to NetApp cluster")
    print("[ERROR] Fix connection issues before continuing")
    exit(1)

print("\n[+] All pre-checks passed - Ready to create SVM")

# Crear la SVM
if create_svm(config_data['svm']):
    print("\n[SUCCESS] SVM creation completed!")
else:
    print("\n[FAILED] SVM creation failed")
    exit(1)

# Modificar la SVM
if modify_svm(config_data['svm']):
    print("\n[SUCCESS] SVM modification completed!")
else:
    print("\n[FAILED] SVM modification failed")
    exit(1)

# Crear servicio FCP en la SVM
if fcp_create(config_data['svm']):
    print("\n[SUCCESS] FCP service creation completed!")
else:
    print("\n[FAILED] FCP service creation failed")
    exit(1)

# Configurar protocolos permitidos en la SVM
if configure_protocols(config_data['svm']):
    print("\n[SUCCESS] Protocol configuration completed!")
else:
    print("\n[FAILED] Protocol configuration failed")
    exit(1)

# Crear network interfaces
net_interfaces = config_data.get('net_interfaces', [])
if create_network_interfaces(config_data['svm']['name'], net_interfaces):
    print("\n[SUCCESS] Network interfaces creation completed!")
    
    # Mostrar las interfaces creadas
    lif_names = [iface.get('lif') for iface in net_interfaces if iface.get('lif')]
    if lif_names:
        show_network_interfaces(config_data['svm']['name'], lif_names)
else:
    print("\n[FAILED] Network interfaces creation failed")
    exit(1)

'''
# Crear management interface
mgmt_interface = config_data.get('mgmt_interface')
if create_management_interface(config_data['svm']['name'], mgmt_interface):
    print("\n[SUCCESS] Management interface creation completed!")
else:
    print("\n[FAILED] Management interface creation failed")
    exit(1)


print("\n[+] Script completed successfully!")

'''
