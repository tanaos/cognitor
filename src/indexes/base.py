from abc import ABC, abstractmethod


class VectorIndex(ABC):
    
    @abstractmethod
    def add(self, vector, metadata):
        ...
        
    @abstractmethod
    def search(self, query_vector, top_k=5):
        ...
        
    @abstractmethod
    def delete(self, vector_id):
        ...
        
    @abstractmethod
    def save(self, file_path):
        ...
        
    @abstractmethod
    def load(self, file_path):
        ...