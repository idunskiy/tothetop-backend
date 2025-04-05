# services/processors.py
from typing import Dict, Any
from abc import ABC, abstractmethod
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        
class IntentProcessor(BaseProcessor):
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Parse the intent data
            intent_data = json.loads(data.get('text', '{}'))
            logger.debug(f"Processing intent data: {intent_data}")
            
            # Here you can process the specific fields we sent
            analysis_result = {
                'analyzed_text': intent_data.get('full_text'),
                'url': intent_data.get('url'),
                'title': intent_data.get('title'),
                'meta_description': intent_data.get('meta_description'),
                'keywords_analyzed': intent_data.get('target_keywords'),
                # Add your intent analysis results here
                'detected_intent': 'informational',  # Example
                'content_suggestions': [
                    {
                        'section': 'Introduction',
                        'suggestion': 'Add more context about...'
                    }
                ]
            }
            
            logger.debug(f"Analysis result: {analysis_result}")
            
            return {
                'result': 'intent processed',
                'data': analysis_result
            }
        except Exception as e:
            logger.error(f"Error processing intent: {str(e)}")
            return {
                'result': 'error',
                'error': str(e)
            }
