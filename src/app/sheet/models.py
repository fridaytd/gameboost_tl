from typing import Annotated, Final, Self, TypeVar, Generic

from pydantic import BaseModel, ConfigDict

from app.gsheet_cache_manager import gsheet_cache_manager

from ..shared.decorators import retry_on_fail
from .enums import CheckType
from .exceptions import SheetError

T = TypeVar("T")

COL_META: Final[str] = "col_name_xxx"
IS_UPDATE_META: Final[str] = "is_update_xxx"
IS_NOTE_META: Final[str] = "is_note_xxx"


class NoteMessageUpdatePayload(BaseModel):
    index: int
    message: str


class BatchCellUpdatePayload(BaseModel, Generic[T]):
    cell: str
    value: T


class ColSheetModel(BaseModel):
    # Model config
    model_config = ConfigDict(arbitrary_types_allowed=True)

    sheet_id: str
    sheet_name: str
    index: int

    @classmethod
    def mapping_fields(cls) -> dict:
        mapping_fields = {}
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if COL_META in metadata:
                        mapping_fields[field_name] = metadata[COL_META]
                        break

        return mapping_fields

    @classmethod
    def updated_mapping_fields(cls) -> dict:
        """
        Get a mapping of model field names to column names for fields that are marked as updatable.
        Returns:
            dict: Mapping of updatable field names to column names.
        """
        mapping_fields = {}
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if (
                        COL_META in metadata
                        and IS_UPDATE_META in metadata
                        and metadata[IS_UPDATE_META]
                    ):
                        mapping_fields[field_name] = metadata[COL_META]
                        break

        return mapping_fields

    @classmethod
    def get(
        cls,
        sheet_id: str,
        sheet_name: str,
        index: int,
    ) -> Self:
        mapping_dict = cls.mapping_fields()

        model_dict = {
            "index": index,
            "sheet_id": sheet_id,
            "sheet_name": sheet_name,
        }

        for k, v in mapping_dict.items():
            model_dict[k] = gsheet_cache_manager.get_value(
                sheet_id=sheet_id,
                sheet_name=sheet_name,
                cell=f"{v}{index}",
            )

        return cls.model_validate(model_dict)

    def update(
        self,
    ) -> None:
        mapping_dict = self.updated_mapping_fields()
        model_dict = self.model_dump(mode="json")

        update_cells: list[str] = []

        for k, v in mapping_dict.items():
            update_cell = f"{v}{self.index}"
            update_cells.append(update_cell)
            gsheet_cache_manager.update_value(
                sheet_id=self.sheet_id,
                sheet_name=self.sheet_name,
                cell=update_cell,
                value=model_dict[k],
            )

    def flush_to_sheet(
        self,
    ) -> None:
        mapping_dict = self.updated_mapping_fields()

        update_cells: list[str] = []

        for k, v in mapping_dict.items():
            update_cell = f"{v}{self.index}"
            update_cells.append(update_cell)

        gsheet_cache_manager.flush_to_sheet(
            sheet_id=self.sheet_id,
            sheet_name=self.sheet_name,
            cells=update_cells,
        )

    @classmethod
    @retry_on_fail(max_retries=3, sleep_interval=30)
    def batch_update(
        cls,
        sheet_id: str,
        sheet_name: str,
        list_object: list[Self],
    ) -> None:
        """
        Batch update multiple rows in the sheet with the provided list of model instances.
        Args:
            sheet_id (str): The ID of the Google Sheet.
            sheet_name (str): The name of the worksheet.
            list_object (list[Self]): List of model instances to update.
        Returns:
            None
        """
        mapping_dict = cls.updated_mapping_fields()
        update_cells: list[str] = []

        for object in list_object:
            model_dict = object.model_dump(mode="json")

            for k, v in mapping_dict.items():
                update_cell = f"{v}{object.index}"
                update_cells.append(update_cell)
                gsheet_cache_manager.update_value(
                    sheet_id=sheet_id,
                    sheet_name=sheet_name,
                    cell=update_cell,
                    value=model_dict[k],
                )

        @classmethod
        def flush_batch_to_sheet(
            cls,
            sheet_id: str,
            sheet_name: str,
            list_object: list[Self],
        ) -> None:
            """
            Batch flush multiple rows in the sheet with the provided list of model instances.
            Args:
                sheet_id (str): The ID of the Google Sheet.
                sheet_name (str): The name of the worksheet.
                list_object (list[Self]): List of model instances to flush.
            Returns:
                None
            """
            mapping_dict = cls.updated_mapping_fields()
            update_cells: list[str] = []

            for object in list_object:
                for k, v in mapping_dict.items():
                    update_cell = f"{v}{object.index}"
                    update_cells.append(update_cell)

            gsheet_cache_manager.flush_to_sheet(
                sheet_id=sheet_id,
                sheet_name=sheet_name,
                cells=update_cells,
            )

    @classmethod
    def update_note(
        cls,
        sheet_id: str,
        sheet_name: str,
        index: int,
        note: str,
    ) -> None:
        col_name = None
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, "metadata"):
                for metadata in field_info.metadata:
                    if IS_NOTE_META in metadata and metadata[IS_NOTE_META]:
                        col_name = metadata[COL_META]
                        break
            if col_name is not None:
                break

        if col_name is None:
            raise SheetError("No note column found in the model.")

        cell = f"{col_name}{index}"
        gsheet_cache_manager.update_value(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            cell=cell,
            value=note,
        )


class RowModel(ColSheetModel):
    CHECK: Annotated[int, {COL_META: "A"}]
    Product_name: Annotated[str, {COL_META: "B"}]
    Note: Annotated[str | None, {COL_META: "C", IS_UPDATE_META: True}] = None
    Last_update: Annotated[str | None, {COL_META: "D", IS_UPDATE_META: True}] = None
    Category: Annotated[str, {COL_META: "E"}]
    Product_link: Annotated[str, {COL_META: "F"}]
    Check_product_compare: Annotated[str, {COL_META: "G"}]
    Product_compare: Annotated[str, {COL_META: "H"}]
    DONGIAGIAM_MIN: Annotated[float, {COL_META: "I"}]
    DONGIAGIAM_MAX: Annotated[float, {COL_META: "J"}]
    DONGIA_LAMTRON: Annotated[int, {COL_META: "K"}]
    IDSHEET_MIN: Annotated[str, {COL_META: "L"}]
    SHEET_MIN: Annotated[str, {COL_META: "M"}]
    CELL_MIN: Annotated[str, {COL_META: "N"}]
    IDSHEET_MAX: Annotated[str | None, {COL_META: "O"}] = None
    SHEET_MAX: Annotated[str | None, {COL_META: "P"}] = None
    CELL_MAX: Annotated[str | None, {COL_META: "Q"}] = None
    IDSHEET_STOCK: Annotated[str | None, {COL_META: "R"}] = None
    SHEET_STOCK: Annotated[str | None, {COL_META: "S"}] = None
    CELL_STOCK: Annotated[str | None, {COL_META: "T"}] = None
    IDSHEET_BLACKLIST: Annotated[str | None, {COL_META: "U"}] = None
    SHEET_BLACKLIST: Annotated[str | None, {COL_META: "V"}] = None
    CELL_BLACKLIST: Annotated[str | None, {COL_META: "W"}] = None
    Relax_time: Annotated[float, {COL_META: "X"}]
    INCLUDE_KEYWORDS: Annotated[str | None, {COL_META: "Y"}] = None
    EXCLUDE_KEYWORDS: Annotated[str | None, {COL_META: "Z"}] = None

    def min_price(self) -> float:
        gsheet_cache_manager.add_sheet(
            sheet_id=self.IDSHEET_MIN,
            sheet_name=self.SHEET_MIN,
        )

        min_value = gsheet_cache_manager.get_value(
            sheet_id=self.IDSHEET_MIN, sheet_name=self.SHEET_MIN, cell=self.CELL_MIN
        )

        if min_value is not None:
            return float(min_value)

        raise SheetError(
            f"{self.IDSHEET_MIN}->{self.SHEET_MIN}->{self.CELL_MIN} is None"
        )

    def max_price(self) -> float | None:
        if self.IDSHEET_MAX is None or self.SHEET_MAX is None or self.CELL_MAX is None:
            return None

        gsheet_cache_manager.add_sheet(
            sheet_id=self.IDSHEET_MAX,
            sheet_name=self.SHEET_MAX,
        )

        max_value = gsheet_cache_manager.get_value(
            sheet_id=self.IDSHEET_MAX, sheet_name=self.SHEET_MAX, cell=self.CELL_MAX
        )
        if max_value is not None:
            return float(max_value)

        return None

    def stock(self) -> int:
        if not self.IDSHEET_STOCK or not self.SHEET_STOCK or not self.CELL_STOCK:
            raise SheetError("Missing STOCK configuration")

        gsheet_cache_manager.add_sheet(
            sheet_id=self.IDSHEET_STOCK,
            sheet_name=self.SHEET_STOCK,
        )
        stock_value = gsheet_cache_manager.get_value(
            sheet_id=self.IDSHEET_STOCK,
            sheet_name=self.SHEET_STOCK,
            cell=self.CELL_STOCK,
        )

        if stock_value is not None:
            return int(stock_value)

        raise SheetError(
            f"{self.IDSHEET_STOCK}->{self.SHEET_STOCK}->{self.CELL_STOCK} is None"
        )

    def blacklist(self) -> list[str]:
        if (
            not self.IDSHEET_BLACKLIST
            or not self.SHEET_BLACKLIST
            or not self.CELL_BLACKLIST
        ):
            return []

        gsheet_cache_manager.add_sheet(
            sheet_id=self.IDSHEET_BLACKLIST,
            sheet_name=self.SHEET_BLACKLIST,
        )

        blacklist = gsheet_cache_manager.get_range(
            sheet_id=self.IDSHEET_BLACKLIST,
            sheet_name=self.SHEET_BLACKLIST,
            a1_range=self.CELL_BLACKLIST,
        )

        if blacklist:
            res = []
            for blist in blacklist:
                for i in blist:
                    res.append(i)
            return res

        return []

    def include_keywords(self) -> list[str] | None:
        if self.INCLUDE_KEYWORDS is None:
            return None

        if self.INCLUDE_KEYWORDS.strip() == "":
            return None

        return [keyword.strip() for keyword in self.INCLUDE_KEYWORDS.split(";")]

    def exclude_keywords(self) -> list[str] | None:
        if self.EXCLUDE_KEYWORDS is None:
            return None

        if self.EXCLUDE_KEYWORDS.strip() == "":
            return None

        return [keyword.strip() for keyword in self.EXCLUDE_KEYWORDS.split(";")]

    @classmethod
    @retry_on_fail(max_retries=5, sleep_interval=10)
    def get_run_indexes(
        cls, sheet_id: str, sheet_name: str, col_range: str
    ) -> list[int]:
        run_indexes = []
        check_col = gsheet_cache_manager.get_range(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            a1_range=col_range,
        )
        for idx, value in enumerate(check_col):
            idx += 1
            _value = value[0]
            if not isinstance(_value, str):
                _value = str(_value)
            if _value in [type.value for type in CheckType]:
                run_indexes.append(idx)

        return run_indexes
