# services/processors.py
from typing import Dict, Any
from abc import ABC, abstractmethod
import json
class BaseProcessor(ABC):
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class TextAnalysisProcessor(BaseProcessor):
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Text analysis logic here
        text = data.get('text', '')
        # Process text...
        return {
            'result': 'text analyzed',
            'data': {'analyzed_text': text}
        }

class InvoiceProcessor(BaseProcessor):
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Invoice processing logic here
        invoice_data = json.loads(data.get('text', '{}'))
        # Process invoice...
        return {
            'result': 'invoice processed',
            'data': invoice_data
        }