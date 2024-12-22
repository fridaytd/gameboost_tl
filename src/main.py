import time
from seleniumbase import SB
from gspread.worksheet import Worksheet


from app.utils.logger import logger
from app.utils.gsheet import worksheet
from app.models.gsheet_models import Product
from app.process import run
from pydantic import ValidationError


def get_run_indexes(sheet: Worksheet) -> list[int]:
    run_indexes = []
    check_col = sheet.col_values(1)
    for idx, value in enumerate(check_col):
        idx += 1
        if isinstance(value, int):
            if value == 1:
                run_indexes.append(idx)
        if isinstance(value, str):
            try:
                int_value = int(value)
            except Exception:
                continue
            if int_value == 1:
                run_indexes.append(idx)

    return run_indexes


def main(sb):
    logger.info("Start running")
    run_indexes = get_run_indexes(worksheet)
    logger.info(f"Run index: {run_indexes}")
    for index in run_indexes[2:]:
        logger.info(f"INDEX (ROW): {index}")
        try:
            product = Product.get(worksheet, index)
            run(sb, product)
        except ValidationError as e:
            logger.error(f"VALIDATION ERROR AT ROW: {index}")
            logger.error(e.errors())

        except Exception as e:
            logger.error(f"FAILED AT ROW: {index}")
            logger.exception(e, exc_info=True)

        time.sleep(2)


with SB(uc=True, headless=True) as sb:
    while True:
        main(sb)
