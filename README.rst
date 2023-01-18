========================
AWS CloudWatch something
========================

It is a python program, a docker, a AWS CloudWatch using. The purpose of the test task is defined by requirements.
They are:

  - The program should behave properly regardless of how much or what kind of logs the
    container output
  - The program should gracefully handle errors and interruptions

I don't see a trap (or hint) in logs. Amount would be issue (obstacles to handle) with subprocess interface
(pipe-transport). I believe requests-transport-provider under docker sdk handles stream properly. Types of logs are
stdout and stderr. Again docker sdk enables booth by default.

A requirement of gracefully handle errors is broad. For example, Google fuzz pyyaml to catch non-encapsulated
exceptions. In general, this is infinitive task, especially test task kind of activity. I treat the program as pipe
in between two services. Limitation of implementation will be freeing and closing resources on any exception.
Docker container would be stopped. AWS CloudWatch... I don't know what.


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
