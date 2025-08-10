import asyncio
import json
import logging
import re
import signal
import sys

import aiohttp
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

KAFKA_BOOTSTRAP_SERVERS = "pallma-kafka:9092"
CONSUME_TOPIC = "otel-traces"
PRODUCE_TOPIC = "output-topic"
GROUP_ID = "otel-traces-group"
PREDICTOR_HOST = "http://pallma-predictor:8000"

# Configuration constants
MAX_CONCURRENT_TASKS = 10
MAX_TRACES_IN_MEMORY = 10000
HTTP_TIMEOUT_SECONDS = 30


# Setup structured JSON logging
logger = logging.getLogger("llm-scanner")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class TraceProcessor:
    """
    Processes OpenTelemetry traces to extract user prompts based on a key pattern.
    """

    def __init__(self, max_traces=10000):
        self.traces = {}
        self.max_traces = max_traces
        self._lock = asyncio.Lock()

    def _get_attribute_value(self, attribute):
        for key in ["stringValue", "intValue", "doubleValue", "boolValue"]:
            if key in attribute:
                return attribute[key]
        return None

    async def process_message(self, message):
        trace_id = message.get("trace_id")
        if not trace_id:
            return

        async with self._lock:
            if trace_id not in self.traces:
                # Clean up old traces if we exceed the limit
                if len(self.traces) >= self.max_traces:
                    # Remove oldest traces (simple FIFO approach)
                    oldest_traces = list(self.traces.keys())[:len(self.traces) // 2]
                    for old_trace_id in oldest_traces:
                        del self.traces[old_trace_id]
                    logger.info(f"Cleaned up {len(oldest_traces)} old traces")

                self.traces[trace_id] = {"trace_id": trace_id, "user_inputs": []}

            attributes = message.get("attributes", [])
            
            # Create a lookup map for attributes to avoid nested loops
            attr_map = {attr.get("key", ""): attr for attr in attributes}

            for key, attr in attr_map.items():
                match = re.match(r"gen_ai\.prompt\.(\d+)\.role", key)
                if match:
                    value = self._get_attribute_value(attr.get("value", {}))
                    if value == "user":
                        user_prompt_index = match.group(1)
                        content_key = f"gen_ai.prompt.{user_prompt_index}.content"
                        
                        if content_key in attr_map:
                            user_prompt_content = self._get_attribute_value(
                                attr_map[content_key].get("value", {})
                            )
                            if (
                                user_prompt_content
                                and user_prompt_content
                                not in self.traces[trace_id]["user_inputs"]
                            ):
                                self.traces[trace_id]["user_inputs"].append(
                                    user_prompt_content
                                )

    async def get_processed_trace(self, trace_id):
        async with self._lock:
            trace = self.traces.get(trace_id)
            if trace and trace.get("user_inputs"):
                # Remove the trace after processing to prevent memory leaks
                del self.traces[trace_id]
                return trace
        return None


def otlp_trace_to_dict(otlp_trace_request: ExportTraceServiceRequest):
    """
    Converts OTLP trace protobuf message to a list of simplified span dictionaries.
    """
    spans_list = []
    dict_trace = MessageToDict(otlp_trace_request)
    for resource_span in dict_trace.get("resourceSpans", []):
        for scope_span in resource_span.get("scopeSpans", []):
            for span in scope_span.get("spans", []):
                simplified_span = {
                    "trace_id": span.get("traceId"),
                    "span_id": span.get("spanId"),
                    "name": span.get("name"),
                    "attributes": span.get("attributes", []),
                }
                spans_list.append(simplified_span)
    return spans_list


# class ScanDecision(Enum):
#     ALLOW = "allow"
#     HUMAN_IN_THE_LOOP_REQUIRED = "human_in_the_loop_required"
#     BLOCK = "block"


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(aiohttp.ClientError),
)
async def call_http_service(session, payload):
    logger.info(f"Sending payload to HTTP service: {json.dumps(payload)}")
    # TODO: Implement the endpoint
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
    async with session.post(f"{PREDICTOR_HOST}/filter", json=payload, timeout=timeout) as resp:
        if resp.status != 200:
            logger.error(f"HTTP service returned error: {resp.status}")
            raise aiohttp.ClientError(f"HTTP {resp.status}")
        logger.info("Successfully sent payload to HTTP service.")
        return await resp.json()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
)
async def produce_message(producer, topic, value):
    try:
        # Attempt to serialize the value as JSON
        payload = json.dumps(value).encode()
    except TypeError:
        # If serialization fails, log a warning and serialize a string representation
        logger.warning(
            f"Could not serialize value of type {type(value)} to JSON. "
            f"Producing string representation instead. Value: {value}"
        )
        payload = json.dumps(str(value)).encode()

    await producer.send_and_wait(topic, payload)


async def consume():
    consumer = AIOKafkaConsumer(
        CONSUME_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        enable_auto_commit=False,
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    session = aiohttp.ClientSession()

    trace_processor = TraceProcessor(max_traces=MAX_TRACES_IN_MEMORY)

    await consumer.start()
    await producer.start()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    tasks = set()
    shutting_down = asyncio.Event()

    async def process_message_batch(msg):
        async with semaphore:
            try:
                otlp_req = ExportTraceServiceRequest()
                otlp_req.ParseFromString(msg.value)
            except Exception as e:
                logger.error(f"Failed to parse protobuf message: {e}")
                # Still commit to avoid reprocessing the same message
                await consumer.commit()
                return

            spans = otlp_trace_to_dict(otlp_req)
            processed_trace_ids = set()

            for span in spans:
                await trace_processor.process_message(span)
                processed_trace_ids.add(span.get("trace_id"))

            for trace_id in processed_trace_ids:
                processed_trace = await trace_processor.get_processed_trace(trace_id)
                if processed_trace:
                    try:
                        # Send the processed trace data to the HTTP service
                        response = await call_http_service(session, processed_trace)
                        # Produce the response to another Kafka topic
                        await produce_message(producer, PRODUCE_TOPIC, response)

                    except Exception as e:
                        logger.error(f"Failed processing trace_id={trace_id}: {e}")

            # Commit the Kafka offset for the original message
            await consumer.commit()
            logger.info(f"Successfully processed and committed offset={msg.offset}")

    async def shutdown():
        shutting_down.set()
        logger.info("Shutdown signal received, waiting for tasks to finish...")
        await asyncio.gather(*tasks, return_exceptions=True)
        await consumer.stop()
        await producer.stop()
        await session.close()
        logger.info("Shutdown complete.")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    try:
        async for msg in consumer:
            if shutting_down.is_set():
                break
            task = asyncio.create_task(process_message_batch(msg))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
    except Exception as e:
        logger.error(f"Consumer crashed: {e}")
    finally:
        if not shutting_down.is_set():
            await shutdown()


async def main():
    await consume()


if __name__ == "__main__":
    asyncio.run(main())
