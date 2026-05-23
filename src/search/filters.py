from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from src.core.models import SearchResult


FilterSpec = dict[str, Any]


def apply(
    results: list["SearchResult"], spec: Optional[FilterSpec] = None
) -> list["SearchResult"]:
    """
    Return only the results whose metadata matches all key-value pairs in spec.
    
    Args:
        results: List of SearchResult objects to filter.
        spec: Dictionary of metadata key-value pairs to filter by. If None or empty, no filtering 
            is applied.
            
    Returns:
        Filtered list of SearchResult objects.
    """
    if not spec:
        return results
    return [r for r in results if all(r.metadata.get(k) == v for k, v in spec.items())]
