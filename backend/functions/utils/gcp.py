"""
GCP utilities for Firestore operations
"""

# Mock Firestore client for development
class MockFirestoreClient:
    def __init__(self):
        self.collections = {}

    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.documents = {}

    def document(self, doc_id):
        return MockDocument(doc_id, self)

    def where(self, field, op, value):
        return MockQuery(self, field, op, value)

    def limit(self, count):
        return self

    def get(self):
        return [MockDocumentRef(doc_id, self) for doc_id in self.documents.keys()]

class MockDocument:
    def __init__(self, doc_id, collection):
        self.id = doc_id
        self.collection = collection

    def set(self, data):
        self.collection.documents[self.id] = data

    def get(self):
        return MockDocumentRef(self.id, self.collection)

    def update(self, data):
        if self.id in self.collection.documents:
            self.collection.documents[self.id].update(data)
        else:
            self.collection.documents[self.id] = data

    def delete(self):
        if self.id in self.collection.documents:
            del self.collection.documents[self.id]

class MockDocumentRef:
    def __init__(self, doc_id, collection):
        self.id = doc_id
        self.collection = collection

    def to_dict(self):
        return self.collection.documents.get(self.id, {})

    def exists(self):
        return self.id in self.collection.documents

class MockQuery:
    def __init__(self, collection, field, op, value):
        self.collection = collection
        self.field = field
        self.op = op
        self.value = value

    def get(self):
        results = []
        for doc_id, data in self.collection.documents.items():
            if self.field in data:
                doc_value = data[self.field]
                if self.op == "==" and doc_value == self.value:
                    results.append(MockDocumentRef(doc_id, self.collection))
                elif self.op == ">" and doc_value > self.value:
                    results.append(MockDocumentRef(doc_id, self.collection))
                elif self.op == "<" and doc_value < self.value:
                    results.append(MockDocumentRef(doc_id, self.collection))
        return results

# Global Firestore client instance
_firestore_client = None

def get_firestore():
    """
    Get Firestore client instance
    Returns a mock client for development/testing
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = MockFirestoreClient()
