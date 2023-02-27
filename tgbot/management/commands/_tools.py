from asgiref.sync import sync_to_async

from clients.models import Client
from products.models import Category, Product


@sync_to_async
def get_clients():
    clients = [client.tg_user_id for client in Client.objects.all()]
    return clients


@sync_to_async
def create_client(tg_user_id, first_name):
        client = Client.objects.get_or_create(
            tg_user_id=tg_user_id,
            first_name = first_name
        )
        return client


@sync_to_async
def get_catygories():
    pass