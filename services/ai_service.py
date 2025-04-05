import pika
import json
import uuid
import logging
import sys
from typing import Optional, Dict, Any, Protocol, Type
import time
from abc import ABC, abstractmethod
from services.event_handlers import TextAnalysisProcessor, InvoiceProcessor

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
    def __init__(self):
        self.responses = {}
        self.processors: Dict[str, Type[MessageProcessor]] = {}
        
        # Register processors
        self.register_processor('text_analysis', TextAnalysisProcessor)
        self.register_processor('invoice', InvoiceProcessor)
        
        # Queue configuration
        self.queues = {
            'text_analysis': 'text_analysis_queue',
            'invoice': 'invoice_queue',
            'responses': 'response_queue'
        }
    
    def register_processor(self, event_type: str, processor: Type[MessageProcessor]):
        """Register a processor for an event type"""
        self.processors[event_type] = processor
        logger.debug(f"Registered processor {processor.__name__} for event type {event_type}")
    
    def prepare_message(self, event_type: str, data: Any) -> Dict[str, Any]:
        """Prepare message based on event type"""
        request_id = str(uuid.uuid4())
        
        if event_type == 'invoice' and not isinstance(data, str):
            data = json.dumps(data)
            
        return {
            'request_id': request_id,
            'event_type': event_type,
            'text': data
        }
    
    def process_event(self, event_type: str, data: Any, timeout: int = 30) -> Optional[dict]:
        """Generic event processing method"""
        if event_type not in self.queues:
            logger.error(f"Unsupported event type: {event_type}")
            raise ValueError(f"Unsupported event type: {event_type}")
        
        processor = self.processors.get(event_type)
        if not processor:
            raise ValueError(f"No processor registered for event type: {event_type}")
            
        connection = None
        channel = None
        try:
            logger.info(f"Processing {event_type} request")
            connection, channel = self._create_connection()
            
            message = self.prepare_message(event_type, data)
            logger.debug(f"Prepared message: {message}")
            
            # Set up response consumer
            channel.basic_consume(
                queue=self.queues['responses'],
                on_message_callback=self._on_response,
                auto_ack=True
            )
            
            # Publish message
            channel.basic_publish(
                exchange='',
                routing_key=self.queues[event_type],
                body=json.dumps(message)
            )
            
            return self._wait_for_response(connection, message['request_id'], timeout)
            
        except Exception as e:
            logger.error(f"Error processing {event_type}: {str(e)}", exc_info=True)
            raise
        finally:
            self._cleanup_connections(channel, connection)
    
    def _wait_for_response(self, connection, request_id: str, timeout: int) -> Optional[dict]:
        """Wait for response with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                connection.process_data_events()
                if request_id in self.responses:
                    response = self.responses.pop(request_id)
                    logger.debug(f"Received response: {response}")
                    return response
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error while waiting for response: {str(e)}", exc_info=True)
                raise
        
        logger.warning("Timeout reached waiting for response")
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

    def _create_connection(self):
        """Create a new RabbitMQ connection and channel"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            channel = connection.channel()
            
            # Create all queues
            for queue_name in self.queues.values():
                channel.queue_declare(queue=queue_name)
            
            return connection, channel
        except Exception as e:
            logger.error(f"Failed to create RabbitMQ connection: {str(e)}")
            raise
    
    def _on_response(self, ch, method, props, body):
        """Handle responses from AI service"""
        try:
            logger.debug(f"Raw response received: {body}")
            response = json.loads(body)
            request_id = response.get('request_id')
            if request_id:
                logger.debug(f"Received response for request {request_id}")
                self.responses[request_id] = response
            else:
                logger.warning(f"Received response without request_id: {response}")
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}", exc_info=True)
    
    def _cleanup_connections(self, channel, connection):
        try:
            if channel and channel.is_open:
                channel.close()
            if connection and not connection.is_closed:
                connection.close()
        except Exception as e:
            logger.error(f"Error closing connections: {str(e)}", exc_info=True)