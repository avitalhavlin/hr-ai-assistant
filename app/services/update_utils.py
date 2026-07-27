def apply_updates(obj, updates: dict, nullable_fields: frozenset[str] = frozenset()) -> None:
    """Apply a partial-update dict (already filtered to fields the caller set) onto a model.

    Rejects an explicit null for any field not in `nullable_fields` with a ValueError,
    so callers can turn it into a 400 instead of letting it hit a NOT NULL column and
    crash with an uncaught IntegrityError/TypeError.
    """
    for field, value in updates.items():
        if value is None and field not in nullable_fields:
            raise ValueError(f"{field} cannot be null")
        setattr(obj, field, value)
