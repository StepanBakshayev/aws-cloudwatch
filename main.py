import codecs
import logging
from contextlib import ExitStack, closing
from datetime import datetime, timezone
from io import BytesIO
from itertools import chain
from operator import itemgetter
from queue import Empty, SimpleQueue
from signal import SIGINT, SIGTERM, Signals, getsignal, signal, sigtimedwait
from threading import Event, Thread
from time import monotonic, sleep
from typing import Iterator, NamedTuple

import boto3
import docker
import typer
from botocore.config import Config

logging.basicConfig(level=logging.INFO)


class Original(NamedTuple):
    timestamp: datetime
    message: bytes


def collecting(client, pipe: SimpleQueue, terminate: Event):
    stream = client.logs(stream=True)
    with closing(stream):
        for chunk in stream:
            if terminate.is_set():
                break
            # XXX: time.monotonic?
            pipe.put_nowait(Original(datetime.now(timezone.utc), chunk))


class LogEvent(NamedTuple):
    timestamp: int
    message: str
    memory: int


# numbers are from https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.put_log_events
MEMORY_BUDGET = 1_048_576
MEMORY_ITEM_COST = 26
MESSAGE_MAXIMUM_MEMORY = MEMORY_BUDGET - MEMORY_ITEM_COST
FREQUENCY = 10  # in seconds, must be less than 24 hours.
COUNT_BUDGET = 10_000
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


UTF8Reader = codecs.getreader("utf-8")


def aws_cloudwatch_log_split_by_budget(stream: bytes) -> Iterator[str]:
    # XXX: this is insane. They limit by bytes, but accept str. Money doesn't smell for them.
    # XXX: User's data is king for me.
    reader = UTF8Reader(BytesIO(stream), errors="replace")
    while chunk := reader.read(size=MESSAGE_MAXIMUM_MEMORY):
        yield chunk


def transferring(client, group, stream, pipe: SimpleQueue, terminate: Event, logger):
    batch: list[LogEvent] = []
    last_beat = monotonic()
    memory = 0
    while not terminate.is_set():
        try:
            raw: Original = pipe.get(timeout=FREQUENCY)
        except Empty:
            pass
        else:
            timestamp = int((raw.timestamp - EPOCH).total_seconds() * 1000)
            for chunk in aws_cloudwatch_log_split_by_budget(raw.message):
                chunk_memory = len(chunk.encode("utf-8")) + MEMORY_ITEM_COST
                memory += chunk_memory
                batch.append(LogEvent(timestamp, chunk, chunk_memory))

        if not batch:
            last_beat = monotonic()
            continue

        beat_interval_exceeded = monotonic() - last_beat > FREQUENCY
        count_exceeded = len(batch) >= COUNT_BUDGET
        memory_exceeded = memory >= MEMORY_BUDGET
        if beat_interval_exceeded or count_exceeded or memory_exceeded:
            # XXX: how to handle backpressure situation?
            drain_memory = 0
            for i, e in enumerate(batch):
                if i >= COUNT_BUDGET:
                    break
                drain_memory += e.memory
                if drain_memory >= MEMORY_BUDGET:
                    break
            drain, batch = batch[:i], batch[i + 1 :]
            response = client.put_log_events(
                logGroupName=group,
                logStreamName=stream,
                logEvents=[{"timestamp": e.timestamp, "message": e.message} for e in drain],
            )
            last_beat = monotonic()
            memory = 0
            logger.info(
                "Log sent. Count is %d. Memory is %d. Oversize is %d. Response is %r.",
                len(drain),
                drain_memory,
                len(batch),
                response,
            )


def main(
    docker_image: str = typer.Option("python"),
    bash_command: str = typer.Option(
        r"""pip install pip -U && pip install tqdm && python -u -c "import time
counter = 0
while True:
    print(counter)
    counter = counter + 1
    time.sleep(0.1)
" """
    ),
    aws_cloudwatch_group: str = typer.Option("irequestedawsregistrationcodetwice"),
    aws_cloudwatch_stream: str = typer.Option("gotnothing"),
    aws_access_key_id: str = typer.Option(...),
    aws_secret_access_key: str = typer.Option(...),
    aws_region: str = typer.Option("eu-west-3"),
):
    logger = logging.getLogger("tt")
    logger.info("Starting...")
    with ExitStack() as stack:
        runner = docker.from_env()
        stack.enter_context(closing(runner))
        logger.info("Docker client is created.")

        config = Config(
            region_name=aws_region,
        )
        logs = boto3.client(
            "logs",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=config,
        )
        stack.enter_context(closing(logs))
        logger.info("AWS CloudWatch Logs client is created.")

        paginator = logs.get_paginator("describe_log_groups")
        for description in chain.from_iterable(
            map(itemgetter("logGroups"), paginator.paginate(logGroupNamePrefix=aws_cloudwatch_group))
        ):
            if description["logGroupName"] == aws_cloudwatch_group:
                break
        else:
            logs.create_log_group(logGroupName=aws_cloudwatch_group)
            logger.info("AWS CloudWatch Logs group %r is created.", aws_cloudwatch_group)

        paginator = logs.get_paginator("describe_log_streams")
        for description in chain.from_iterable(
            map(
                itemgetter("logStreams"),
                paginator.paginate(logGroupName=aws_cloudwatch_group, logStreamNamePrefix=aws_cloudwatch_stream),
            )
        ):
            if description["logStreamName"] == aws_cloudwatch_stream:
                break
        else:
            logs.create_log_stream(logGroupName=aws_cloudwatch_group, logStreamName=aws_cloudwatch_stream)
            logger.info("AWS CloudWatch Logs stream %r is created.", aws_cloudwatch_stream)

        container = runner.containers.run(docker_image, ["sh", "-c", bash_command], detach=True)
        stack.push(lambda exc_type, exc_value, traceback: container.stop(timeout=1) and False)
        logger.info("Docker container %r id is started.", container.id)

        pipe = SimpleQueue()
        terminate = Event()
        collector = Thread(target=collecting, args=(container, pipe, terminate), daemon=False)
        transporter = Thread(
            target=transferring,
            args=(logs, aws_cloudwatch_group, aws_cloudwatch_stream, pipe, terminate, logger),
            daemon=False,
        )

        def handler(signal):
            logger.info("exiting by signal %r...", Signals(signal))
            terminate.set()

        signal(SIGINT, lambda si, st: handler(si))
        signal(SIGTERM, lambda si, st: handler(si))

        logger.info("Collector is started.")
        collector.start()
        logger.info("Transporter is started.")
        transporter.start()

        try:
            while collector.is_alive() and transporter.is_alive():
                sleep(1)

        finally:
            terminate.set()
            logger.info("Waiting collector to exit.")
            collector.join(timeout=10)
            logger.info("Waiting transporter to exit.")
            transporter.join(timeout=10)
            logger.info(
                "Exit. Collector is alive %r. Transporter is alive %r.", collector.is_alive(), transporter.is_alive()
            )


if __name__ == "__main__":
    typer.run(main)
