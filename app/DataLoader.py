from config.db import prodcode_engine
from app.helpers import create_session
from sqlalchemy import MetaData, Table, select

from datetime import datetime

import json
import os
import traceback

class FetchProdCode():
    def __init__(self):
        self.Session = create_session(prodcode_engine)
    
    def process_fetching(self):
        session = self.Session()

        try:
            metadata = MetaData()
            product_code_table = Table(
                "tbl_prod01", 
                metadata, 
                autoload_with=prodcode_engine
            )
            prodcode_col = product_code_table.columns["T_PRODCODE"]

            stmt = select(prodcode_col.distinct())

            results = session.execute(stmt).fetchall()
            codes = [ row[0] for row in results ]

            # STORE THE PRODUCTION CODES IN A JSON FILE
            payload = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "data": codes,
                "total_length": len(codes)
            }

            # WRITE JSON STRING
            self._store_to_json_path(data=payload)

        except Exception as e:
            print(f"Error filtering product codes: {e}")
            traceback.print_exc()
        finally:
            session.close()
    
    def _store_to_json_path(self, data: list):
        current_dir = os.path.dirname(__file__)
        cached_dir = os.path.join(current_dir, "views", "cache")
        os.makedirs(cached_dir, exist_ok=True)

        json_path = os.path.join(cached_dir, "prodcode.json")

        length_validation = self._check_length_in_json_data(json_path)

        if length_validation == data.get("total_length"):
            print("Same length on the validation. No need to store to the json file")
            return

        try:
            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"Save to: {json_path}")
        except Exception:
            print("Error writing json:\n")
            
            traceback.print_exc()

    def _check_length_in_json_data(self, json_path: str):
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                total_length = data.get("total_length", 0)

                return total_length
        except FileNotFoundError:
            print(f"File not found error: {json_path}")
            traceback.print_exc()
            
            return 0


# instance = FetchProdCode()
# instance.process_fetching()
        