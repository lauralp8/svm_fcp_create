from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Svm
import yaml

print("Starting SVM creation script...")

def config_loader(path="config.yaml"):
    print("Openning config.yaml for SVM creation parameters...")
    with open("config.yaml", 'r') as file:
        config_data = yaml.safe_load(file)
    print("Config data loaded successfully.")
    return config_data


config.CONNECTION = HostConnection(
    'cluster1.demo.netapp.com',
    username='admin',
    password='Netapp1!',
    verify=False
)

