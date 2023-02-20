IPINFO_URL = 'https://ipinfo.io/'
# for example: iter(('', '?token=token1', '?token=token2', '?token=token3'))
ITERATOR_TOKENS = iter(('', '', '', '', ''))
IN_FILE = 'example.csv'
SEPARATOR = ';'
# if 1 then Nmap do
NMAP = 0
OUT_FILE_ALL_IP = 'result_all_ip_' + IN_FILE
OUT_FILE_UKR_IP = 'result_ukr_ip_' + IN_FILE
OUT_FILE_UKR_MOBILE_IP = 'result_ukr_mobile_ip_' + IN_FILE
DB_NAME = 'ip_resolved_list.db'
# how many days to consider the 'whois' field is out of date
# and need to updated at the time of the request
LIMIT_DAY = 5
