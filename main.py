import typer


def main(
    docker_image: str = typer.Option("python"),
    bash_command: str = typer.Option(
        r"""$'pip install pip -U && pip
install tqdm && python -c \"import time\ncounter = 0\nwhile
True:\n\tprint(counter)\n\tcounter = counter + 1\n\ttime.sleep(0.1)\"'"""
    ),
    aws_cloudwatch_group: str = typer.Option("test-task-group-1"),
    aws_cloudwatch_stream: str = typer.Option("test-task-stream-1"),
    aws_access_key_id: str = typer.Option(...),
    aws_secret_access_key: str = typer.Option(...),
    aws_region: str = typer.Option(...),
):
    print(f"Hello {{name}}")


if __name__ == "__main__":
    typer.run(main)
