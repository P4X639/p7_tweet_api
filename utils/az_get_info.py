# Authentification et récupération de l'ID de souscription
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import json

# Authentification avec les credentials par défaut
credential = DefaultAzureCredential()

# Création du client pour accéder aux informations de souscription
resource_client = ResourceManagementClient(credential, subscription_id="")

# Alternative : utiliser Azure CLI pour lister les souscriptions
import subprocess
result = subprocess.run(['az', 'account', 'list'], capture_output=True, text=True)
subscriptions = json.loads(result.stdout)

print("Souscriptions disponibles :")
for sub in subscriptions:
    if "Azure for Students" in sub['name']:
        print(f"Nom: {sub['name']}")
        print(f"ID: {sub['id']}")
        print(f"État: {sub['state']}")
