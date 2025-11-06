import csv
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from gspread.utils import ValueInputOption
from app.sheet.models import RowModel
from app import logger


@dataclass
class CachedRow:
    index: int
    Product_name: str
    Product_link: str
    Product_compare: str
    Category: str
    Check_product_compare: str
    min_price_value: Optional[float] 
    max_price_value: Optional[float]
    stock_value: Optional[int]
    blacklist_value: List[str] 
    include_keywords_value: Optional[List[str]]
    exclude_keywords_value: Optional[List[str]]
    DONGIAGIAM_MIN: float
    DONGIAGIAM_MAX: float
    DONGIA_LAMTRON: int
    Relax_time: float
    
    # Fields that will be updated
    Note: Optional[str] = None
    Last_update: Optional[str] = None


class DataCache:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.data: Dict[int, CachedRow] = {}
        self.lock = threading.Lock()
        self.pending_updates: Dict[int, Dict[str, Optional[str]]] = {}
        
    def load_from_sheet(self, sheet_id: str, sheet_name: str, run_indexes: List[int]) -> None:
        logger.info(f"Loading {len(run_indexes)} rows from Google Sheet...")
        
        loaded_count = 0
        skipped_count = 0
        skipped_rows = []
        
        for idx in run_indexes:
            try:
                # Try to get the row from sheet
                try:
                    row = RowModel.get(
                        sheet_id=sheet_id,
                        sheet_name=sheet_name,
                        index=idx
                    )
                except Exception as e:
                    logger.error(f"Row {idx} has invalid data, skipping: {e}")
                    skipped_count += 1
                    skipped_rows.append(idx)
                    continue
                
                # Get min_price with error handling
                min_price_value = None
                try:
                    min_price_value = row.min_price()
                except ValueError as e:
                    logger.warning(f"Row {idx}: Invalid min_price value - {e}. Using None.")
                except Exception as e:
                    logger.warning(f"Row {idx}: Could not get min_price - {e}. Using None.")
                
                # Get max_price with error handling
                max_price_value = None
                try:
                    max_price_value = row.max_price()
                except ValueError as e:
                    logger.warning(f"Row {idx}: Invalid max_price value - {e}. Using None.")
                except Exception as e:
                    logger.warning(f"Row {idx}: Could not get max_price - {e}. Using None.")
                
                # Get stock with error handling
                stock_value = None
                try:
                    stock_value = row.stock()
                except ValueError as e:
                    logger.warning(f"Row {idx}: Invalid stock value - {e}. Using None.")
                except Exception as e:
                    logger.warning(f"Row {idx}: Could not get stock - {e}. Using None.")
                
                # Get blacklist with error handling
                blacklist_value = []
                try:
                    blacklist_value = row.blacklist()
                except Exception as e:
                    logger.warning(f"Row {idx}: Could not get blacklist - {e}. Using empty list.")
                
                cached_row = CachedRow(
                    index=idx,
                    Product_name=row.Product_name,
                    Product_link=row.Product_link,
                    Product_compare=row.Product_compare,
                    Category=row.Category,
                    Check_product_compare=row.Check_product_compare,
                    min_price_value=min_price_value,
                    max_price_value=max_price_value,
                    stock_value=stock_value,
                    blacklist_value=blacklist_value,
                    include_keywords_value=row.include_keywords(),
                    exclude_keywords_value=row.exclude_keywords(),
                    DONGIAGIAM_MIN=row.DONGIAGIAM_MIN,
                    DONGIAGIAM_MAX=row.DONGIAGIAM_MAX,
                    DONGIA_LAMTRON=row.DONGIA_LAMTRON,
                    Relax_time=row.Relax_time,
                    Note=row.Note if row.Note else None,
                    Last_update=row.Last_update if row.Last_update else None
                )
                
                self.data[idx] = cached_row
                loaded_count += 1
                logger.info(f"Loaded row {idx}: {row.Product_name} ({loaded_count}/{len(run_indexes)})")
                
                # Sleep after every 10 rows to avoid Google Sheets rate limit
                if loaded_count % 10 == 0:
                    logger.info(f"Loaded {loaded_count} rows. Sleeping for 10 seconds to avoid rate limit...")
                    time.sleep(10)
                
            except Exception as e:
                logger.exception(f"Failed to load row {idx}: {e}")
                skipped_count += 1
                skipped_rows.append(idx)
        
        self.save_to_csv()
        logger.info(f"Successfully loaded {len(self.data)} rows into cache")
        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} rows due to errors: {skipped_rows}")
    
    def save_to_csv(self) -> None:
        with self.lock:
            try:
                with open(self.cache_file, 'w', newline='', encoding='utf-8') as f:
                    if not self.data:
                        return
                    
                    fieldnames = list(asdict(next(iter(self.data.values()))).keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for row in self.data.values():
                        row_dict = asdict(row)
                        if row_dict['blacklist_value']:
                            row_dict['blacklist_value'] = ';'.join(row_dict['blacklist_value'])
                        else:
                            row_dict['blacklist_value'] = ''
                            
                        if row_dict['include_keywords_value']:
                            row_dict['include_keywords_value'] = ';'.join(row_dict['include_keywords_value'])
                        else:
                            row_dict['include_keywords_value'] = ''
                            
                        if row_dict['exclude_keywords_value']:
                            row_dict['exclude_keywords_value'] = ';'.join(row_dict['exclude_keywords_value'])
                        else:
                            row_dict['exclude_keywords_value'] = ''
                        
                        # Handle None values for Note and Last_update
                        if row_dict['Note'] is None:
                            row_dict['Note'] = ''
                        if row_dict['Last_update'] is None:
                            row_dict['Last_update'] = ''
                        
                        # Handle None for max_price_value and stock_value and min_price_value
                        if row_dict['min_price_value'] is None:
                            row_dict['min_price_value'] = ''
                        if row_dict['max_price_value'] is None:
                            row_dict['max_price_value'] = ''
                        if row_dict['stock_value'] is None:
                            row_dict['stock_value'] = ''
                            
                        writer.writerow(row_dict)
                
                logger.info(f"Saved {len(self.data)} rows to {self.cache_file}")
            except Exception as e:
                logger.exception(f"Failed to save cache to CSV: {e}")
    
    def load_from_csv(self) -> None:
        with self.lock:
            try:
                self.data.clear()
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['index'] = int(row['index'])
                        
                        row['min_price_value'] = float(row['min_price_value']) if row['min_price_value'] and row['min_price_value'].strip() else None
                        
                        row['max_price_value'] = float(row['max_price_value']) if row['max_price_value'] and row['max_price_value'].strip() else None
                        
                        row['stock_value'] = int(row['stock_value']) if row['stock_value'] and row['stock_value'].strip() else None
                        
                        row['DONGIAGIAM_MIN'] = float(row['DONGIAGIAM_MIN'])
                        row['DONGIAGIAM_MAX'] = float(row['DONGIAGIAM_MAX'])
                        row['DONGIA_LAMTRON'] = int(row['DONGIA_LAMTRON'])
                        row['Relax_time'] = float(row['Relax_time'])
                        
                        row['blacklist_value'] = row['blacklist_value'].split(';') if row['blacklist_value'] and row['blacklist_value'].strip() else []
                        row['include_keywords_value'] = row['include_keywords_value'].split(';') if row['include_keywords_value'] and row['include_keywords_value'].strip() else None
                        row['exclude_keywords_value'] = row['exclude_keywords_value'].split(';') if row['exclude_keywords_value'] and row['exclude_keywords_value'].strip() else None
                        
                        row['Note'] = row['Note'] if row['Note'] and row['Note'].strip() else None
                        row['Last_update'] = row['Last_update'] if row['Last_update'] and row['Last_update'].strip() else None
                        
                        cached_row = CachedRow(**row)
                        self.data[cached_row.index] = cached_row
                
                logger.info(f"Loaded {len(self.data)} rows from {self.cache_file}")
            except FileNotFoundError:
                logger.warning(f"Cache file {self.cache_file} not found")
            except Exception as e:
                logger.exception(f"Failed to load cache from CSV: {e}")
    
    def get(self, index: int) -> Optional[CachedRow]:
        with self.lock:
            return self.data.get(index)
    
    def update_fields(self, index: int, note: Optional[str], last_update: Optional[str]) -> None:
        with self.lock:
            if index in self.data:
                self.data[index].Note = note
                self.data[index].Last_update = last_update
                self.pending_updates[index] = {
                    'Note': note,
                    'Last_update': last_update
                }
    
    def flush_updates_to_sheet(self, sheet_id: str, sheet_name: str) -> None:
        with self.lock:
            if not self.pending_updates:
                logger.info("No pending updates to flush")
                return
            
            try:
                worksheet = RowModel.get_worksheet(sheet_id, sheet_name)
                
                mapping_dict = RowModel.updated_mapping_fields()
                
                batch_data = []
                
                for index, updates in self.pending_updates.items():
                    if 'Note' in mapping_dict:
                        batch_data.append({
                            'range': f"{mapping_dict['Note']}{index}",
                            'values': [[updates['Note'] if updates['Note'] else '']]
                        })
                    
                    if 'Last_update' in mapping_dict:
                        batch_data.append({
                            'range': f"{mapping_dict['Last_update']}{index}",
                            'values': [[updates['Last_update'] if updates['Last_update'] else '']]
                        })
                
                if batch_data:
                    worksheet.batch_update(batch_data, value_input_option=ValueInputOption.user_entered)
                    logger.info(f"Flushed {len(self.pending_updates)} updates to Google Sheet")
                
                self.pending_updates.clear()
                self.save_to_csv()
                
            except Exception as e:
                logger.exception(f"Failed to flush updates to sheet: {e}")
    
    def get_all_indexes(self) -> List[int]:
        with self.lock:
            return list(self.data.keys())
    
    def count(self) -> int:
        with self.lock:
            return len(self.data)


# Global cache instance
_cache: Optional[DataCache] = None


def initialize_cache(cache_file: Path, sheet_id: str, sheet_name: str, run_indexes: List[int]) -> DataCache:
    global _cache
    _cache = DataCache(cache_file)
    _cache.load_from_sheet(sheet_id, sheet_name, run_indexes)
    return _cache


def get_cache() -> DataCache:
    if _cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first!!!")
    return _cache