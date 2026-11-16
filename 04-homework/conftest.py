import patch_agent  # noqa: F401  (importing it patches Agent.run)


def pytest_sessionfinish(session, exitstatus):
    patch_agent.display_total_usage()
