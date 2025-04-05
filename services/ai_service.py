import pika
import json
import uuid
import logging
import sys
from typing import Optional, Dict, Any
import time

# Set up logging properly
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.responses = {}
        # Define available event types and their queues
        self.queues = {
            'text_analysis': 'text_analysis_queue',
            'invoice': 'invoice_queue',
            'responses': 'response_queue'
        }
    
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
    
    def process_text(self, text: str, event_type: str = 'text_analysis', timeout: int = 30) -> Optional[dict]:
        """
        Send text to AI service and wait for response
        Args:
            text: The text to process
            event_type: Type of event ('text_analysis' or 'invoice')
            timeout: How long to wait for response in seconds
        Returns:
            Optional[dict]: The response from the AI service or None if timeout
        """
        if event_type not in self.queues:
            logger.error(f"Unsupported event type: {event_type}")
            raise ValueError(f"Unsupported event type: {event_type}")
            
        connection = None
        channel = None
        try:
            logger.info(f"Processing {event_type} request")
            # Create a new connection for this request
            connection, channel = self._create_connection()
            
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Prepare message with event type
            message = {
                'request_id': request_id,
                'event_type': event_type,
                'text': text
            }
            
            logger.debug(f"Sending {event_type} message: {message}")
            
            # Set up response consumer before publishing
            channel.basic_consume(
                queue=self.queues['responses'],
                on_message_callback=self._on_response,
                auto_ack=True
            )
            
            # Publish message to appropriate queue
            channel.basic_publish(
                exchange='',
                routing_key=self.queues[event_type],
                body=json.dumps(message)
            )
            
            # Wait for response
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
            
            logger.warning(f"Timeout reached waiting for {event_type} response")
            return None
            
        except Exception as e:
            logger.error(f"Error processing {event_type}: {str(e)}", exc_info=True)
            raise
        finally:
            try:
                if channel and channel.is_open:
                    channel.close()
                if connection and not connection.is_closed:
                    connection.close()
            except Exception as e:
                logger.error(f"Error closing connections: {str(e)}", exc_info=True)

    def process_invoice(self, invoice_data: Dict[str, Any], timeout: int = 30) -> Optional[dict]:
        """
        Convenience method for processing invoices
        """
        try:
            # Convert invoice data to string if it's not already
            if not isinstance(invoice_data, str):
                invoice_data = json.dumps(invoice_data)
            
            logger.debug(f"Processing invoice data: {invoice_data}")
            return self.process_text(
                text=invoice_data,
                event_type='invoice',
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Error in process_invoice: {str(e)}", exc_info=True)
            raise