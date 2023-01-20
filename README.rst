========================
AWS CloudWatch something
========================

Abstract
========

The program transfers logs from docker to aws cloudwatch logs. The obstacles are restriction and design of services from
well paid, from most famous companies, high qualified programmers from docker, amazon. The purpose of a test task is
checking adoption, resource management, operating system aware, concurrency magic skills.


Design
======

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

Let me second try to consider gracefully handle errors. I could trace some errors to root of the programme options to
show user a context.

The main pain is AWS. It has so complicated restricted unreasonable
`rules <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.put_log_events>`_.
There is error reporting addition to exception which is nonsense. I take care only for total size of messages and
span of batch.

Tests are excluded from the project. It is most API centric and data-transferring. I don't regret to skip tests
this time. (I am lazy to bring up docker, aws, imagine some meaningfully command to run, dive deeper into AWS to use API
to check appearance of log on it side).


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
