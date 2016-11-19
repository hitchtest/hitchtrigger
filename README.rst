HitchTrigger
============

HitchTrigger is a self contained build tool designed to trigger blocks of build commands when various conditions are met.

The conditions can be one or more combined of any of the following:

* A file or files (e.g. source files) have changed.
* A specified (build) directory did not exist.
* A period of time has elapsed.
* A 'watched' variable has changed its value.
* An exception occurred the previous time the commands were run.

To install from pypi::

  $ hitch install hitchtrigger


Use
---

.. code-block:: python

    import hitchtrigger

    mon = hitchtrigger.Monitor(
        "/path/to/monitor.sqlite",
    )

    # Will run in the following cases:
    #
    ## The command block has never been run before.
    ## Var "v=2" is changed (e.g. to "v=2").
    ## Either requirements.txt or dev_requirements.txt have been modified (file modification dates are monitored).
    ## A period of 7 days has elapsed
    ## The code surrounded by the context manager (with) triggered an exception on the previous run.

    with mon.watch(
        "virtualenv",
        mon.nonexistent("venv") | mon.not_run_since(days=7) |
        mon.modified(["requirements.txt", "dev_requirements.txt"]) | mon.var(v=1)
    ) as trigger:
        if trigger:
            print(trigger.why)  # Prints out reason for running

            Path("venv").rmtree(ignore_errors=True)
            virtualenv("venv").run()
            pip("install", "-r", "requirements.txt").run()
            pip("freeze").stdout(Path("freeze.txt")).run()
            pip("install", "dev_requirements.txt").run()
