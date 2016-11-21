HitchTrigger
============

HitchTrigger is a self contained build tool designed to trigger blocks of build commands when a condition is met
that necessitates a rebuild.

The conditions can be one or more combined of any of the following:

* A file or files (e.g. source files) have changed.
* A specified (build) directory did not exist.
* A period of time has elapsed.
* A 'watched' variable has changed its value.
* An exception occurred the previous time the commands were run (always by default).

To install from pypi::

  $ hitch install hitchtrigger


Use
---

.. code-block:: python

    import hitchtrigger

    monitor = hitchtrigger.Monitor(
        "/path/to/project.watch"
        #override=["virtualenv", ],
    )

    # Will run in the following cases:
    #
    ## The command block has never been run before.
    ## An exception was triggered within the context manager on the previous run.
    ## venv directory is non-existent.
    ## A period of 7 days has elapsed
    ## A previous block named 'previousblock' was run.
    ## Either requirements.txt or dev_requirements.txt have been modified (file modification dates are monitored).
    ## Var "v=1" is changed (e.g. to "v=2").
    ## The line 'override=["virtualenv", ]' is uncommented.

    with monitor.block(
        "virtualenv",
        monitor.nonexistent("venv") | monitor.not_run_since(days=7) | monitor.was_run("previousblock")
        monitor.modified(["requirements.txt", "dev_requirements.txt"]) | monitor.var(v=1)
    ).context() as trigger:
        if trigger:
            print(trigger.why)  # Prints out reason for running

            Path("venv").rmtree(ignore_errors=True)
            virtualenv("venv").run()
            pip("install", "-r", "requirements.txt").run()
            pip("freeze").stdout(Path("freeze.txt")).run()
            pip("install", "dev_requirements.txt").run()
