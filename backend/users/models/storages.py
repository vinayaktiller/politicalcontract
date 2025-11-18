from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    account_name = settings.AZURE_ACCOUNT_NAME  # your Azure account name
    account_key = settings.AZURE_ACCOUNT_KEY    # your Azure account key
    azure_container = settings.AZURE_CONTAINER  # container name e.g. 'media'
    expiration_secs = None
