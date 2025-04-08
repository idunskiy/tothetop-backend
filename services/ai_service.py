import pika
import json
import uuid
import logging
import sys
from typing import Optional, Dict, Any, Protocol, Type
import time
from abc import ABC, abstractmethod
from services.event_handlers import TextAnalysisProcessor, InvoiceProcessor, IntentProcessor, AddKeywordsProcessor

# Set up logging properly
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

class MessageProcessor(Protocol):
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AIService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, 'initialized') or not self.initialized:
            self.responses = {}
            self.processors = {}
            # Register processors
            self.register_processor('text_analysis', TextAnalysisProcessor)
            self.register_processor('invoice', InvoiceProcessor)
            self.register_processor('intent', IntentProcessor)
            self.register_processor('add_keywords', AddKeywordsProcessor)
            
            # Queue configuration
            self.queues = {
                'text_analysis': 'text_analysis_queue',
                'invoice': 'invoice_queue',
                'responses': 'response_queue',
                'intent': 'intent_queue',
                'add_keywords': 'add_keywords_queue'
            }
            
            # Set up persistent connection and consumer for responses
            self._setup_response_consumer()
            self.initialized = True
    
    def register_processor(self, event_type: str, processor: Type[MessageProcessor]):
        """Register a processor for an event type"""
        self.processors[event_type] = processor
        logger.debug(f"Registered processor {processor.__name__} for event type {event_type}")
    
    def prepare_message(self, event_type: str, data: Any) -> Dict[str, Any]:
        """Prepare message based on event type"""
        print(f"prepare_message received data: {data}")
        request_id = str(uuid.uuid4())
        print(f"Request ID in prepare_message ai_service: {request_id}")

        
        # Add intent to the JSON conversion
        if event_type in ['invoice', 'intent'] and not isinstance(data, str):
            data = json.dumps(data)
            
        return {
            'request_id': request_id,
            'event_type': event_type,
            'text': data
        }
    
    def process_event(self, event_type: str, data: Any, timeout: int = 120) -> Optional[dict]:
        """Generic event processing method"""
        if event_type not in self.queues:
            logger.error(f"Unsupported event type: {event_type}")
            raise ValueError(f"Unsupported event type: {event_type}")
        
        processor = self.processors.get(event_type)
        if not processor:
            raise ValueError(f"No processor registered for event type: {event_type}")
            
        try:
            logger.info(f"Processing {event_type} request")
            
            # Create fresh connection and set up consumer first
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            
            # Declare all queues
            for queue_name in self.queues.values():
                channel.queue_declare(queue=queue_name)
            
            # Set up response consumer BEFORE sending request
            channel.basic_consume(
                queue=self.queues['responses'],
                on_message_callback=self._on_response,
                auto_ack=True
            )
            
            # Prepare and send message
            message = self.prepare_message(event_type, data)
            print(f"Sending request with ID: {message['request_id']}")
            
            # Start consuming events
            connection.process_data_events(time_limit=0)
            
            # Send the request
            channel.basic_publish(
                exchange='',
                routing_key=self.queues[event_type],
                body=json.dumps(message)
            )
            
            # Wait for response
            response = self._wait_for_response(connection, message['request_id'], timeout)
            if response:
                print(f"Response received: {response}")
            else:
                print(f"No response received after {timeout} seconds")
            return response
        except Exception as e:
            logger.error(f"Error in process_event: {str(e)}", exc_info=True)
            raise
        finally:
            if 'connection' in locals() and connection and not connection.is_closed:
                connection.close()
    
    def _wait_for_response(self, connection, request_id: str, timeout: int = 120) -> Optional[dict]:
        """Wait for response with timeout"""
        start_time = time.time()
        print(f"Waiting for response with request_id: {request_id}")
        
        while time.time() - start_time < timeout:
            # Process any pending events
            connection.process_data_events()
            
            # Check if we got the response
            if request_id in self.responses:
                response = self.responses.pop(request_id)
                print(f"Found and retrieved response for {request_id}: {response}")
                return response
                
            time.sleep(0.1)  # Short sleep to prevent CPU spinning
        
        print(f"Timeout waiting for response with request_id: {request_id}")
        return None

    # Convenience methods for specific event types
    def process_text(self, text: str, timeout: int = 30) -> Optional[dict]:
        """Process text analysis"""
        return self.process_event('text_analysis', text, timeout)
    
    def process_invoice(self, invoice_data: Dict[str, Any], timeout: int = 30) -> Optional[dict]:
        """Process invoice"""
        return self.process_event('invoice', invoice_data, timeout)
    
    def process_custom(self, event_type: str, data: Any, timeout: int = 30) -> Optional[dict]:
        """Process any registered event type"""
        return self.process_event(event_type, data, timeout)
    
    def process_intent(self, intent_data: Dict[str, Any], timeout: int = 30) -> Optional[dict]:
        """Process intent"""
        logger.debug(f"Processing intent with data: {intent_data}")
        return self.process_event('intent', intent_data, timeout)
    
    def add_keywords(self, optimization_data: Dict[str, Any], timeout: int = 120) -> Optional[dict]:
        """Optimize content"""
        return self.process_event('add_keywords', optimization_data, timeout)

    def _setup_response_consumer(self):
        """Set up a persistent connection to consume responses"""
        self.response_connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.response_channel = self.response_connection.channel()
        
        # Declare all queues
        for queue_name in self.queues.values():
            self.response_channel.queue_declare(queue=queue_name)
            
        print("Setting up response consumer...")
        self.response_channel.basic_consume(
            queue=self.queues['responses'],
            on_message_callback=self._on_response,
            auto_ack=True
        )
        
        # Start consuming in a separate thread
        import threading
        self.consumer_thread = threading.Thread(target=self._consume_responses, daemon=True)
        self.consumer_thread.start()
        print("Response consumer thread started")
        
    def _consume_responses(self):
        """Consume messages in a separate thread"""
        try:
            print("Starting to consume responses...")
            self.response_channel.start_consuming()
        except Exception as e:
            print(f"Error in consumer thread: {e}")
            
    def _on_response(self, ch, method, props, body):
        """Handle responses from AI service"""
        try:
            print(f"Received raw response: {body}")
            response = json.loads(body)
            request_id = response.get('request_id')
            if request_id:
                print(f"Got response for request {request_id}")
                self.responses[request_id] = response
            else:
                print(f"Response missing request_id: {response}")
        except Exception as e:
            print(f"Error processing response: {e}")