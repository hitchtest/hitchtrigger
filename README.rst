HitchTrigger
============

HitchTrigger is a self contained build tool designed to trigger a block of build commands when various conditions are met.

The conditions can be:

* A file or files (e.g. source files) have changed.
* A period of time has elapsed.
* A 'watched' flag has changed its value.
* An exception occurred the previous time the commands were run, necessitating a re-run.
* You told the monitor to forget all of the above and run the build block anyway.

Whenever a trigger is returned by the context manager, it evaluates to True/False and has a property "why"
which contains the reason for triggering the build block.


Install
-------

  $ hitch install hitchtrigger


Use
---

    import hitchtrigger

    # to_build = ["venv"] # Set this to list of trigger names order to override all over triggers and always build venv
    # to_build = None     # Default setting - follow other rules.

    trigmon = hitchtrigger.Monitor(
        "/path/to/monitor.sqlite",
        override=to_build,
    )

    # Will run in the following cases:
    #
    ## The commands have never been run before.
    ## Flag "v1" is changed (e.g. to "v2") or flag 'python_version's value has changed from the previous run.
    ## Either requirements.txt or dev_requirements.txt have been modified (file modification dates are monitored).
    ## A period of 7 days has elapsed
    ## The code surrounded by the context manager (with) triggered an exception on the previous run.

    with trigmon.watch(
        "virtualenv", flags={"v": "1", "python_version": python_version}, elapsed="7d",
        files=["requirements.txt", "dev_requirements.txt"],
    ) as trigger:
        if trigger:
            print(trigger.why)  # Prints out reason for running

            Path("venv").rmtree(ignore_errors=True)
            virtualenv("venv").run()
            pip("install", "-r", "requirements.txt").run()
            pip("freeze").stdout(Path("freeze.txt")).run()
            pip("install", "dev_requirements.txt").run()

