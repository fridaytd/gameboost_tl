import os
from datetime import datetime
import time
from seleniumbase import SB
from threading import Thread
from queue import Queue

from app import logger, config
from app.shared.paths import SRC_PATH
from app.sheet.models import RowModel
from pydantic import ValidationError
from app.shared.utils import formated_datetime
from app.processes.main_process import process
from app.shared.decorators import retry_on_fail
from app.service.data_cache import initialize_cache, get_cache


def update_error_to_cache(index: int, error_msg: str):
    try:
        now = datetime.now()
        cache = get_cache()
        cache.update_fields(
            index=index,
            note=f"{formated_datetime(now)}: {error_msg}",
            last_update=formated_datetime(now)
        )
    except Exception as e:
        logger.exception(f"Failed to update error to cache: {e}")


def worker(index_queue: Queue, cookies_path: str, worker_id: int):
    thread_prefix = f"[Worker-{worker_id}]"
    
    with SB(uc=True, headless=True, disable_js=True) as sb:
        sb.activate_cdp_mode("https://google.com")
        sb.cdp.load_cookies(cookies_path)
        
        while True:
            index = index_queue.get()
            if index is None:
                index_queue.task_done()
                break
            
            logger.info(f"{thread_prefix} INDEX (ROW): {index}")
            try:
                cache = get_cache()
                cached_row = cache.get(index)
                
                if cached_row is None:
                    logger.error(f"{thread_prefix} Row {index} not found in cache")
                    index_queue.task_done()
                    continue
                
                process(sb, cached_row)
                logger.info(f"{thread_prefix} Sleep for {cached_row.Relax_time}s")
                time.sleep(cached_row.Relax_time)
                
            except ValidationError as e:
                logger.exception(f"{thread_prefix} VALIDATION ERROR AT ROW: {index}")
                logger.exception(e.errors())
                update_error_to_cache(index, f"VALIDATION ERROR: {e.errors()}")
                
            except Exception as e:
                logger.exception(f"{thread_prefix} FAILED AT ROW: {index}")
                update_error_to_cache(index, f"FAILED: {e}")
                time.sleep(20)
                
            finally:
                index_queue.task_done()

def main():
    logger.info("Start running")

    run_indexes = RowModel.get_run_indexes(
        sheet_id=config.SHEET_ID, 
        sheet_name=config.SHEET_NAME, 
        col_index=1
    )
    
    if not run_indexes:
        logger.info("No rows to process")
        return
    
    thread_number = config.THREAD_NUMBER
    logger.info(f"Run indexes: {run_indexes}")
    logger.info(f"Thread number: {thread_number}")
    
    cache_file = SRC_PATH / "data" / "cache.csv"
    initialize_cache(cache_file, config.SHEET_ID, config.SHEET_NAME, run_indexes)
    
    # index_queue = Queue() 
    # cookies_path = str(SRC_PATH / "data" / "cookies.txt")
    
    # for index in run_indexes:
    #     index_queue.put(index)

    # threads = []
    # for i in range(thread_number):
    #     t = Thread(
    #         target=worker, 
    #         args=(index_queue, cookies_path, i+1),
    #         daemon=True,
    #         name=f"Worker-{i+1}"
    #     )
    #     t.start()
    #     threads.append(t)
    #     logger.info(f"Started worker thread {i+1}/{thread_number}")

    # index_queue.join()
    
    # for _ in range(thread_number):
    #     index_queue.put(None)
    
    # for t in threads:
    #     t.join(timeout=60)

    # logger.info("Flushing updates to Google Sheet...")
    # cache = get_cache()
    # cache.flush_updates_to_sheet(config.SHEET_ID, config.SHEET_NAME)
    
    # logger.info(f"Completed processing {len(run_indexes)} rows")
    # logger.info(f"Sleep for {os.getenv('RELAX_TIME_EACH_ROUND', '10')}s")
    # time.sleep(int(os.getenv("RELAX_TIME_EACH_ROUND", "10")))


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
    # set_cookies()
    logger.info("Cookies set.")

    while True:
        main()