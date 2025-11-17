from .utils import ShelfValidators

class ShelfContext:
    """Shared context for shelf-related classes."""

    def __init__(self, plugin_name: str, validators: ShelfValidators) -> None:
        self.plugin_name = plugin_name
        self.validators = validators
