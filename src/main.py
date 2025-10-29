import os
from datetime import datetime
import time
from seleniumbase import SB
from gspread.worksheet import Worksheet


from app import logger, config
from app.shared.paths import SRC_PATH
from app.sheet.models import RowModel
from pydantic import ValidationError
from app.shared.utils import formated_datetime
from app.processes.main_process import process
from app.shared.decorators import retry_on_fail
from app.crwl.crwl import currencies_extract


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

    run_indexes = RowModel.get_run_indexes(
        sheet_id=config.SHEET_ID, sheet_name=config.SHEET_NAME, col_index=1
    )
    logger.info(f"Run index: {run_indexes}")
    for index in run_indexes:
        logger.info(f"INDEX (ROW): {index}")
        try:
            product = RowModel.get(
                sheet_id=config.SHEET_ID,
                sheet_name=config.SHEET_NAME,
                index=index,
            )

            process(sb, product)
            logger.info(f"Sleep for {product.Relax_time}s")
            time.sleep(product.Relax_time)
        except ValidationError as e:
            logger.exception(f"VALIDATION ERROR AT ROW: {index}")
            logger.exception(e.errors())
            try:
                now = datetime.now()
                worksheet = RowModel.get_worksheet(
                    sheet_id=config.SHEET_ID, sheet_name=config.SHEET_NAME
                )
                worksheet.batch_update(
                    [
                        {
                            "range": f"C{index}",
                            "values": [
                                [
                                    f"{formated_datetime(now)}: VALIDATION ERROR AT ROW: {index}"
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
                worksheet = RowModel.get_worksheet(
                    sheet_id=config.SHEET_ID, sheet_name=config.SHEET_NAME
                )
                worksheet.batch_update(
                    [
                        {
                            "range": f"C{index}",
                            "values": [[f"{formated_datetime(now)}: FAILED: {e}"]],
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


@retry_on_fail(max_retries=10, sleep_interval=1)
def set_cookies():
    with SB(
        uc=True,
        headless=True,
        disable_js=False,
    ) as sb:
        sb.activate_cdp_mode("https://gameboost.com")
        sb.cdp.sleep(2)
        sb.cdp.wait_for_text("Change language and currency")
        logger.info("Click change language and currency")
        sb.cdp.click('span:contains("Change language and currency")')
        sb.cdp.sleep(0.5)
        logger.info("Click currency")
        sb.cdp.mouse_click('label:contains("Currency") ~ button')
        sb.cdp.sleep(0.5)
        logger.info("Click Euro")
        sb.cdp.mouse_click('div[aria-selected] span:contains("Euro")')
        sb.cdp.sleep(0.5)
        logger.info("Click Save Changes")
        sb.cdp.find_element_by_text("Save Changes").click()
        sb.cdp.sleep(2)
        sb.cdp.save_cookies(SRC_PATH / "data" / "cookies.txt")


if __name__ == "__main__":
    logger.info("=== STARTING SCRIPT ===")

    logger.info("Setting cookies...")
    set_cookies()
    logger.info("Cookies set.")

    with SB(uc=True, headless=True, disable_js=True) as sb:
        sb.activate_cdp_mode("https://google.com")

        sb.cdp.load_cookies(SRC_PATH / "data" / "cookies.txt")

        while True:
            main(sb)
