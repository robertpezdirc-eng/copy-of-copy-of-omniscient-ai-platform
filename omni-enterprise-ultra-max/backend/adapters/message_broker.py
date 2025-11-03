import os
import json
import asyncio
import logging
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("adapters.message_broker")

@dataclass
class BrokerConfig:
    broker_type: str = os.environ.get("BROKER_TYPE", "memory")  # kafka|rabbitmq|memory
    kafka_bootstrap: Optional[str] = os.environ.get("KAFKA_BOOTSTRAP", None)
    rabbitmq_url: Optional[str] = os.environ.get("RABBITMQ_URL", None)
    namespace: str = os.environ.get("BROKER_NAMESPACE", "omni")

class MessageBrokerAdapter:
    """
    Enoten adapter za Kafka, RabbitMQ in in-memory fallback.
    API:
    - publish(topic, message)
    - subscribe(topic, handler)
    - start()/stop() za async lifecycle
    """
    def __init__(self, config: Optional[BrokerConfig] = None) -> None:
        self.config = config or BrokerConfig()
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any]], asyncio.Future]] = {}
        self._loop = asyncio.get_event_loop()
        logger.info(f"MessageBroker inicializiran: type={self.config.broker_type}")

    async def start(self) -> None:
        self._running = True
        logger.info("MessageBroker start")
        if self.config.broker_type == "memory":
            # Ni potrebe po posebni povezavi
            return
        # Za kafka/rabbitmq bi tukaj inicializirali odjemalce
        logger.warning("Kafka/RabbitMQ niso implementirani v tem okolju, uporabljam memory fallback")

    async def stop(self) -> None:
        self._running = False
        for task in list(self._tasks.values()):
            task.cancel()
        self._tasks.clear()
        logger.info("MessageBroker stop")

    def _topic(self, topic: str) -> str:
        return f"{self.config.namespace}.{topic}"

    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        full_topic = self._topic(topic)
        payload = {
            "topic": full_topic,
            "message": message,
        }
        if self.config.broker_type == "memory":
            q = self._queues.setdefault(full_topic, asyncio.Queue())
            await q.put(payload)
            logger.info(f"[memory] publish {full_topic}: {json.dumps(message)[:200]}")
        else:
            # Poenostavljen fallback
            q = self._queues.setdefault(full_topic, asyncio.Queue())
            await q.put(payload)
            logger.info(f"[fallback] publish {full_topic}: {json.dumps(message)[:200]}")

    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        full_topic = self._topic(topic)
        self._handlers[full_topic] = handler
        if full_topic in self._tasks:
            return
        q = self._queues.setdefault(full_topic, asyncio.Queue())
        self._tasks[full_topic] = self._loop.create_task(self._consume_loop(full_topic, q))
        logger.info(f"Subscribed to {full_topic}")

    async def _consume_loop(self, full_topic: str, q: asyncio.Queue) -> None:
        while self._running:
            try:
                item = await q.get()
                handler = self._handlers.get(full_topic)
                if handler:
                    try:
                        res = handler(item["message"])  # handler lahko vrne coroutine ali sync
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception as e:
                        logger.error(f"Handler error for {full_topic}: {e}")
                q.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consume loop error: {e}")
                await asyncio.sleep(0.1)

# Globalni broker za enostavno uporabo
_global_broker: Optional[MessageBrokerAdapter] = None

async def get_broker() -> MessageBrokerAdapter:
    global _global_broker
    if _global_broker is None:
        _global_broker = MessageBrokerAdapter()
        await _global_broker.start()
    return _global_broker