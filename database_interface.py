from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class DatabaseInterface(ABC):
    @abstractmethod
    def buscar_receitas(self, query: str) -> List[Dict]:
        pass
    
    @abstractmethod
    def adicionar_receita(self, receita: Dict) -> bool:
        pass
    
    @abstractmethod
    def buscar_receita_por_id(self, receita_id: str) -> Optional[Dict]:
        pass 