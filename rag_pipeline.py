"""Backward-compatible entry point — delegates to app.py."""

from app import configure_environment, create_query_engine, query_with_context

if __name__ == "__main__":
    from app import main

    main()
