"""Console / module entry point: ``python -m matchstick_man``."""

from matchstick_man.app import App


def main() -> None:
    """Construct the Pyxel application and start its run loop."""
    App().run()


if __name__ == "__main__":
    main()
