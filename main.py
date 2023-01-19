import logging
from contextlib import ExitStack, closing
from itertools import chain
from operator import itemgetter

import boto3
import docker
import typer
from botocore.config import Config
from devtools import debug

logging.basicConfig(level=logging.INFO)


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
        stack.push(lambda exc_type, exc_value, traceback: (container.stop(timeout=1)) and False)
        for chunk in container.logs(stream=True):
            print(f"{chunk.decode('utf-8', errors='replace')!r}")


if __name__ == "__main__":
    typer.run(main)
