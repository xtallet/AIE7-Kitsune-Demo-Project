from app.domain.ports.cache_port import Cache


class FakeCache(Cache):
    def __init__(self):
        self.store = {}

    def save_to_cache(self, key, data):
        self.store[key] = data

    def get_from_cache(self, key):
        return self.store.get(key)


# Fake for Knowledge Base
class FakeKnowledgeBase:
    def search(self, query):
        return {"result": f"Fake knowledge base result for '{query}'"}


# Fake for Kitsune DB
class FakeKitsuneDB:
    def run_sql_query(self, query):
        return {"data": f"Fake database result for '{query}'"}


# Fake for LLM
class FakeLLM:
    def generate_response(self, prompt):
        return f"Fake LLM response for '{prompt}'"
