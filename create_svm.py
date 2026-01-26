from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Svm
import yaml

print()

config.CONNECTION = HostConnection(
    'cluster1.demo.netapp.com',
    username='admin',
    password='Netapp1!',
    verify=False
)

