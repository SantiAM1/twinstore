from customers.models import Client,Domain

def run():
    tenant = Client(schema_name='public', name='root')
    tenant.save()

    domain = Domain()
    domain.domain = 'localhost'
    domain.tenant = tenant
    domain.is_primary = True
    domain.save()