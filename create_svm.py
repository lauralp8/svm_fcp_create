from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Svm, FcpService
import yaml

print("Starting SVM creation script...")

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
        print(f"Config.yaml loader: {path}")
        
        # Abrir y leer el contenido del archivo YAML
        with open(path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
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
        
        print(f"Configuration loaded successfully")
        print(f"Target cluster: {config_data['cluster'].get('host', 'N/A')}")
        print(f"SVM to create: {config_data['svm'].get('name', 'N/A')}")
        
        return config_data
    
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


def connect_to_cluster(cluster_config):
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
        from netapp_ontap.resources import Cluster
        cluster_info = Cluster()
        cluster_info.get()
        
        print(f"[+] Connection successful!")
        print(f"[+] Cluster name: {cluster_info.name}")
        print(f"[+] ONTAP version: {cluster_info.version.full}")
        print(f"[+] Cluster UUID: {cluster_info.uuid}")
        
        return True
    
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
    Crea una SVM en NetApp ONTAP usando parámetros del config.yaml
    
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
        
        # Validar que exista el nombre (obligatorio)
        if not svm_name:
            print(f"[ERROR] 'name' is required in svm configuration")
            return False
        
        print(f"\n[*] Creating SVM: {svm_name}")
        
        # Verificar si la SVM ya existe
        print(f"[*] Checking if SVM already exists...")
        existing_svm = Svm.find(name=svm_name)
        if existing_svm:
            print(f"[ERROR] SVM '{svm_name}' already exists with UUID: {existing_svm.uuid}")
            return False
        
        # Crear objeto SVM
        new_svm = Svm()
        new_svm.name = svm_name
        
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
        
        # Configurar lista de agregados si se especifica
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
    
    Basado en: vserver fcp create -vserver <name> -status-admin <up|down>
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se creó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer status_admin del config.yaml (true = up, false = down)
        fcp_status_admin = svm_config.get('fcp_status_admin', False)
        
        print(f"\n[*] Creating FCP service on SVM: {svm_name}")
        
        # Crear objeto FCP service
        fcp = FcpService()
        fcp.svm = {'name': svm_name}
        fcp.enabled = fcp_status_admin
        
        # Crear el servicio FCP
        print(f"[*] Creating FCP service...")
        fcp.post()
        
        status_text = "up" if fcp_status_admin else "down"
        print(f"[+] FCP service created successfully!")
        print(f"[*] Status admin: {status_text}")
        
        return True
    
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


def protocols(svm_config):
    """
    Añade y elimina protocolos de una SVM
    
    Basado en: 
    - vserver add-protocols -vserver <name> -protocols <protocol1,protocol2>
    - vserver remove-protocols -vserver <name> -protocols <protocol1,protocol2>
    
    Args:
        svm_config: Diccionario con la configuración de la SVM del config.yaml
    
    Returns:
        bool: True si se ejecutó exitosamente, False si hubo error
    """
    try:
        # Extraer nombre de la SVM del config
        svm_name = svm_config.get('name')
        
        # Extraer lista de protocolos a añadir del config.yaml
        add_protocols_list = svm_config.get('add_protocols_list', [])
        # Extraer lista de protocolos a eliminar del config.yaml
        delete_protocols_list = svm_config.get('delete_protocols_list', [])
        
        if not add_protocols_list and not delete_protocols_list:
            print(f"[WARNING] No protocols specified in config.yaml")
            return True
        
        print(f"\n[*] Managing protocols for SVM: {svm_name}")
        
        # Buscar la SVM
        svm = Svm.find(name=svm_name)
        if not svm:
            print(f"[ERROR] SVM '{svm_name}' not found")
            return False
        
        # Obtener SVM completa
        svm.get()
        
        # Obtener protocolos actuales
        current_protocols = getattr(svm, 'allowed_protocols', []) or []
        print(f"[*] Current protocols: {', '.join(current_protocols) if current_protocols else 'None'}")
        
        # Eliminar protocolos primero
        if delete_protocols_list:
            print(f"\n[*] Removing protocols: {', '.join(delete_protocols_list)}")
            current_protocols = [i for i in current_protocols if i not in delete_protocols_list]
        
        # Añadir protocolos después
        if add_protocols_list:
            print(f"[*] Adding protocols: {', '.join(add_protocols_list)}")
            # Combinar protocolos existentes con nuevos (sin duplicados)
            current_protocols = list(set(current_protocols + add_protocols_list))
        
        # Aplicar cambios
        svm.allowed_protocols = current_protocols
        
        print(f"[*] Applying protocol changes...")
        svm.patch()
        
        print(f"[+] Protocols updated successfully!")
        print(f"[+] Final protocols: {', '.join(current_protocols) if current_protocols else 'None'}")
        
        return True
    
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during protocol management")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during protocol management: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# Cargar la configuración desde el archivo YAML
config_data = config_loader()

# Verificar que la configuración se cargó exitosamente
if config_data is None:
    print("\n[ERROR] Cannot continue without valid configuration")
    print("[ERROR] Check the config.yaml file and try again")
    exit(1)

# Establecer conexión y verificar acceso a la cabina NetApp
if not connect_to_cluster(config_data['cluster']):
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

# Añadir protocolos a la SVM
if protocols(config_data['svm']):
    print("\n[SUCCESS] Protocols added successfully!")
else:
    print("\n[FAILED] Failed to add protocols")
    exit(1)

print("\n[+] Script completed successfully!")


