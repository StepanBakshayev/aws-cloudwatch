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
    container = client.containers.run(docker_image, ["sh", "-c", bash_command], detach=True)
    debug(container, container.id, container.logs())
    import time

    time.sleep(5)
    debug(container, container.id, container.logs())
    container.stop()


if __name__ == "__main__":
    typer.run(main)
