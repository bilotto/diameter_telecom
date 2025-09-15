import csv
import os
import logging
logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    'time',
    'app_id',
    'pcap_filepath',
    'pkt_number',
    'session_id',
    'name',
    'msisdn',
    'imsi',
    'apn',
    'framed_ip_address',
    'sgsn_mcc_mnc',
    'result_code',
    'processing_time_microseconds'
]

class CsvFile:
    def __init__(self, filename: str, csv_columns: list = CSV_COLUMNS, replace_existing: bool = False):
        self.filename = filename
        if not os.path.exists(filename) or replace_existing:
            self.file_handler = open(filename, 'w')
            self.csv_writer = csv.DictWriter(self.file_handler, fieldnames=csv_columns)
            self.csv_writer.writeheader()
        else:
            self.file_handler = open(filename, 'a')
            self.csv_writer = csv.DictWriter(self.file_handler, fieldnames=csv_columns)
        self.n_records = 0

    def write_row(self, row: dict):
        self.csv_writer.writerow(row)
        self.n_records += 1

    def close(self):
        self.file_handler.close()

    def flush(self):
        self.file_handler.flush()

    def get_csv_columns(self):
        return self.csv_writer.fieldnames

from .diameter.message import DiameterMessage

def write_to_csv(csv_file: CsvFile,
                 diameter_message: DiameterMessage,
                 ):
        try:
            row = {}
            for column in csv_file.get_csv_columns():
                value = getattr(diameter_message, column)
                # Convert value to string and handle None values
                if value is None:
                    row[column] = ""
                else:
                    row[column] = str(value).strip()
            csv_file.write_row(row)
            csv_file.flush()
        except Exception as e:
            logger.error(f"Error writing to csv file - Error : {e}")
            pass