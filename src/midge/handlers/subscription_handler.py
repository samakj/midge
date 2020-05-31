import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from paho.mqtt.client import Client as MQTTClient
from .models.response_code import ResponseCode
from .models.error_codes import ErrorCodesMaps

LOG = logging.getLogger(__name__)


class SubscriptionHandler:
    def __init__(self, client):
        self.client = client
        self.subscriptions = {}
        self._topic_subscribe_handler_map: Dict[str, Dict[int, Callable]] = {}
        self._topic_unsubscribe_handler_map: Dict[str, Dict[int, Callable]] = {}
        self._mid_topic_map: Dict[int, str] = {}

    def lazy_subscribe(
        self,
        topic: str,
        qos: int = 0,
        options: Dict[str, Any] = None,
        properties: Dict[str, Any] = None,
    ) -> None:
        self.subscriptions[topic] = {
            "qos": qos,
            "options": options,
            "properties": properties,
            "is_subscribed": False,
        }

    def subscribe(
        self,
        topic: str,
        qos: int = 0,
        options: Dict[str, Any] = None,
        properties: Dict[str, Any] = None,
    ) -> Tuple[ResponseCode, int]:
        self.subscriptions[topic] = {
            "qos": qos,
            "options": options,
            "properties": properties,
            "is_subscribed": True,
        }
        LOG.info(f"Subscribing to {topic}")
        error_code, mid = super(type(self.client), self.client).subscribe(
            topic=topic, qos=qos, options=options, properties=properties
        )
        self._mid_topic_map[mid] = topic

        return ErrorCodesMaps[error_code], mid

    def add_topic_subscribe_handler(self, topic: str, handler: Callable) -> int:
        handler_id: int = 0

        if topic in self._topic_subscribe_handler_map:
            handler_id = len(self._topic_subscribe_handler_map)
        else:
            self._topic_subscribe_handler_map[topic] = {}

        self._topic_subscribe_handler_map[topic][handler_id] = handler

        return handler_id

    def get_topic_subscribe_handler(
        self, topic: str, handler_id: int
    ) -> Optional[Callable]:
        return self._topic_subscribe_handler_map.get(topic, {}).get(handler_id, None)

    def get_topic_subscribe_handlers(self, topic: str) -> List[Callable]:
        handlers = []

        handlers.extend(self._topic_subscribe_handler_map.get(topic, {}).values())

        topic_split = topic.split("/")

        while topic_split:
            topic_split[-1] = "#"
            handlers.extend(self._topic_subscribe_handler_map.get("/".join(topic_split), {}).values())
            del topic_split[-1]

        return handlers

    def remove_topic_subscribe_handler(self, topic: str, handler_id: int) -> None:
        if (
            self.get_topic_subscribe_handler(topic=topic, handler_id=handler_id)
            is not None
        ):
            del self._topic_subscribe_handler_map[topic][handler_id]

    def handle_subscribe(
        self,
        _: MQTTClient,
        mid: int,
        granted_qos: bool,
        userdata: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        topic = self._mid_topic_map.get(mid, None)

        if topic is not None:
            for handler in self.get_topic_subscribe_handlers(topic=topic):
                try:
                    handler(
                        client=self.client,
                        user_data=userdata,
                        mid=mid,
                        granted_qos=granted_qos,
                        properties=properties,
                    )
                except Exception as Error:
                    LOG.exception(Error)
            del self._mid_topic_map[mid]

    def enact_subscriptions(self) -> None:
        for (topic, opts) in self.subscriptions.items():
            if not opts["is_subscribed"]:
                LOG.info(f"Subscribing to {topic}")
                result, mid = super(type(self.client), self.client).subscribe(
                    topic=topic,
                    qos=opts["qos"],
                    options=opts["options"],
                    properties=opts["properties"],
                )
                self._mid_topic_map[mid] = topic

    def unsubscribe(self, topic: str, properties: Dict[str, Any] = None) -> Optional[Tuple[ResponseCode, int]]:
        if topic in self.subscriptions:
            if self.subscriptions[topic]["is_subscribed"]:
                error_code, mid = self.client.unsubscribe(topic=topic, properties=properties)
                self._mid_topic_map[mid] = topic
                return ErrorCodesMaps[error_code], mid
            del self.subscriptions[topic]
        return None

    def add_topic_unsubscribe_handler(self, topic: str, handler: Callable) -> int:
        handler_id: int = 0

        if topic in self._topic_unsubscribe_handler_map:
            handler_id = len(self._topic_unsubscribe_handler_map)
        else:
            self._topic_unsubscribe_handler_map[topic] = {}

        self._topic_unsubscribe_handler_map[topic][handler_id] = handler

        return handler_id

    def get_topic_unsubscribe_handler(
        self, topic: str, handler_id: int
    ) -> Optional[Callable]:
        return self._topic_unsubscribe_handler_map.get(topic, {}).get(handler_id, None)

    def get_topic_unsubscribe_handlers(self, topic: str) -> List[Callable]:
        handlers = []

        handlers.extend(self._topic_unsubscribe_handler_map.get(topic, {}).values())

        topic_split = topic.split("/")

        while topic_split:
            topic_split[-1] = "#"
            handlers.extend(self._topic_unsubscribe_handler_map.get("/".join(topic_split), {}).values())
            del topic_split[-1]

        return handlers

    def remove_topic_unsubscribe_handler(self, topic: str, handler_id: int) -> None:
        if (
            self.get_topic_unsubscribe_handler(topic=topic, handler_id=handler_id)
            is not None
        ):
            del self._topic_unsubscribe_handler_map[topic][handler_id]

    def handle_unsubscribe(
        self, _: MQTTClient, mid: int, userdata: Optional[Dict[str, Any]] = None,
    ) -> None:
        topic = self._mid_topic_map.get(mid, None)

        if topic is not None:
            for handler in self.get_topic_unsubscribe_handlers(topic=topic):
                try:
                    handler(client=self.client, user_data=userdata, mid=mid)
                except Exception as Error:
                    LOG.exception(Error)

            del self._mid_topic_map[mid]
