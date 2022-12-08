IPINFO_URL = 'https://ipinfo.io/'
ITERATOR_TOKENS = iter(('', '', '', '', ''))
IN_FILE = 'example.csv'
SEPARATOR = ';'
OUT_FILE_ALL_IP = 'result_all_ip_' + IN_FILE
OUT_FILE_UKR_IP = 'result_ukr_ip_' + IN_FILE
OUT_FILE_UKR_MOBILE_IP = 'result_ukr_mobile_ip_' + IN_FILE
DB_NAME = 'ip_resolved_list.db'
QUERIES = dict(
    CREATE_TABLE="""
        CREATE TABLE IF NOT EXISTS ip (
        ip_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL UNIQUE,
        whois TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        update_at TEXT DEFAULT CURRENT_TIMESTAMP)
    """,
    GET_IP="""SELECT * FROM ip WHERE ip=?""",
    INSERT_IP="""INSERT INTO ip(ip, whois) VALUES(?,?)"""
)
