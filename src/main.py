import os
from datetime import datetime
import time
from seleniumbase import SB
from gspread.worksheet import Worksheet


from app.utils.logger import logger
from app.utils.gsheet import worksheet
from app.models.gsheet_models import Product
from app.process import run, last_update_message
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
    for index in run_indexes:
        logger.info(f"INDEX (ROW): {index}")
        try:
            product = Product.get(worksheet, index)

            run(sb, product)
            logger.info(f"Sleep for {product.Relax_time}s")
            time.sleep(product.Relax_time)
        except ValidationError as e:
            logger.exception(f"VALIDATION ERROR AT ROW: {index}")
            logger.exception(e.errors())
            try:
                now = datetime.now()
                worksheet.batch_update(
                    [
                        {
                            "range": f"C{index}",
                            "values": [
                                [
                                    f"{last_update_message(now)}: VALIDATION ERROR AT ROW: {index}"
                                ]
                            ],
                        }
                    ]
                )
            except Exception as e:
                logger.exception(e)
                time.sleep(10)

        except Exception as e:
            logger.exception(f"FAILED AT ROW: {index}")
            try:
                now = datetime.now()
                worksheet.batch_update(
                    [
                        {
                            "range": f"C{index}",
                            "values": [[f"{last_update_message(now)}: FAILED: {e}"]],
                        }
                    ]
                )
            except Exception as e1:
                logger.exception(e1)
                time.sleep(10)
            logger.exception(e, exc_info=True)
            time.sleep(20)

    logger.info(f"Sleep for {os.getenv('RELAX_TIME_EACH_ROUND', '10')}s")
    time.sleep(
        int(
            os.getenv(
                "RELAX_TIME_EACH_ROUND",
                "10",
            )
        )
    )


with SB(uc=True, headless=True, disable_js=True) as sb:
    sb.activate_cdp_mode("https://google.com")

    while True:
        main(sb)
