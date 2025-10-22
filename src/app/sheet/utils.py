from gspread.utils import a1_range_to_grid_range, rowcol_to_a1
from pydantic import BaseModel


class GridRange(BaseModel):
    startRowIndex: int = 0
    endRowIndex: int = 0
    startColumnIndex: int = 0
    endColumnIndex: int = 0


def fri_a1_range_to_grid_range(name: str) -> GridRange:
    return GridRange.model_validate(a1_range_to_grid_range(name))


def fri_col_index_to_col_a1(col_index: int) -> str:
    """Convert a one-based column index to its corresponding A1 notation.

    Args:
        col_index (int): One-based column index (1 for 'A', 2 for 'B', etc.).

    Returns:
        str: Corresponding A1 notation for the column.
    """
    if col_index < 1:
        raise ValueError("Column index must be a positive integer.")

    return rowcol_to_a1(1, col_index).replace("1", "")
