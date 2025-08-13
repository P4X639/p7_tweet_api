import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient

# Charger les variables depuis le fichier .env
load_dotenv('.env')

# Récupération des variables d'environnement
AZ_CLIENT_ID = os.environ.get('AZ_CLIENT_ID')
AZ_CLIENT_SECRET = os.environ.get('AZ_CLIENT_SECRET')
AZ_TENANT_ID = os.environ.get('AZ_TENANT_ID')
AZ_SUBSCRIPTION_ID = os.environ.get('AZ_SUBSCRIPTION_ID')

# Vérification que toutes les variables sont définies
if not all([AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_TENANT_ID, AZ_SUBSCRIPTION_ID]):
    print("Erreur: Variables d'environnement manquantes")
    print(f"AZ_CLIENT_ID: {'✓' if AZ_CLIENT_ID else '✗'}")
    print(f"AZ_CLIENT_SECRET: {'✓' if AZ_CLIENT_SECRET else '✗'}")
    print(f"AZ_TENANT_ID: {'✓' if AZ_TENANT_ID else '✗'}")
    print(f"AZ_SUBSCRIPTION_ID: {'✓' if AZ_SUBSCRIPTION_ID else '✗'}")
    exit(1)

print("Variables d'environnement chargées depuis .env :")
print(f"AZ_CLIENT_ID: {AZ_CLIENT_ID}")
print(f"AZ_TENANT_ID: {AZ_TENANT_ID}")
print(f"AZ_SUBSCRIPTION_ID: {AZ_SUBSCRIPTION_ID}")
print("AZ_CLIENT_SECRET: [MASQUÉ]")

# Test de connexion Azure
try:
    credential = ClientSecretCredential(
        tenant_id=AZ_TENANT_ID,
        client_id=AZ_CLIENT_ID,
        client_secret=AZ_CLIENT_SECRET
    )
    
    client = ResourceManagementClient(credential, AZ_SUBSCRIPTION_ID)
    
    resource_groups = list(client.resource_groups.list())
    print("Connexion réussie !")
    print("Groupes de ressources disponibles :")
    for rg in resource_groups:
        print(f"- {rg.name} (Région: {rg.location})")
        
except Exception as e:
    print(f"Erreur de connexion : {e}")
