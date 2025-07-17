from prometheus_client import Counter, REGISTRY

def get_or_create_counter(name, documentation, labelnames):
    # Search existing collectors
    for collector in list(REGISTRY._names_to_collectors.values()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector  # Already exists
    return Counter(name, documentation, labelnames)

api_call_counter = get_or_create_counter(
    'api_requests_total', 'Total API calls per endpoint', ['endpoint']
)

db_query_counter = get_or_create_counter(
    'database_queries_total', 'DB queries per endpoint', ['endpoint']
)