from contextlib import ExitStack

import docker
import typer
from devtools import debug


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
    # aws_cloudwatch_group: str = typer.Option("test-task-group-1"),
    # aws_cloudwatch_stream: str = typer.Option("test-task-stream-1"),
    # aws_access_key_id: str = typer.Option(...),
    # aws_secret_access_key: str = typer.Option(...),
    # aws_region: str = typer.Option(...),
):
    client = docker.from_env()
    with ExitStack() as stack:
        container = client.containers.run(docker_image, ["sh", "-c", bash_command], detach=True)
        stack.push(lambda exc_type, exc_value, traceback: (container.stop(timeout=1)) and False)
        for chunk in container.logs(stream=True):
            print(f"{chunk.decode('utf-8', errors='replace')!r}")


if __name__ == "__main__":
    typer.run(main)
