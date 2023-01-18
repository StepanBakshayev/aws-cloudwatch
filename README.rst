========================
AWS CloudWatch something
========================

It is a python program, a docker, a AWS CloudWatch using.


Setup
=====

.. code-block:: sh

    $ pipx install pdm
    $ pdm install


Execute
=======

.. code-block:: sh

    $ pdm run python main.py --help
    Usage: main.py [OPTIONS]

    Options:
      --docker-image TEXT           [default: python]
      --bash-command TEXT           [default: $'pip install pip -U && pip install
                                    tqdm && python -c \"import time\ncounter =
                                    0\nwhile True:\n\tprint(counter)\n\tcounter =
                                    counter + 1\n\ttime.sleep(0.1)\"']
      --aws-cloudwatch-group TEXT   [default: test-task-group-1]
      --aws-cloudwatch-stream TEXT  [default: test-task-stream-1]
      --aws-access-key-id TEXT      [required]
      --aws-secret-access-key TEXT  [required]
      --aws-region TEXT             [required]
      --help                        Show this message and exit.
