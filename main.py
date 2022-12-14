# Decoding the organization's IP address from csv using ipinfo
from sys import exit
from pandas import read_csv
from sqlite3 import connect
from requests import get
from numpy import nan
from datetime import datetime, timedelta
from const.constants import (IPINFO_URL, ITERATOR_TOKENS,
                             IN_FILE, SEPARATOR,
                             OUT_FILE_ALL_IP, OUT_FILE_UKR_IP,
                             OUT_FILE_UKR_MOBILE_IP,
                             DB_NAME, LIMIT_DAY, QUERIES as q)


def get_next_token():
    try:
        token = next(ITERATOR_TOKENS, '-1')
        if token == '-1':
            exit('TOKENS ARE ENDED !!!')
        print('Run ' + token)
        return token
    except Exception as e_tkn:
        print(f'Token assignment error: {str(e_tkn)}')


def get_response(url, ip_address, token):
    try:
        response = get(url + ip_address + token)
        print(response.status_code.__str__() + ' ' + ip_address + ' ' + url + ip_address + token)
        if response.status_code == 200:
            result = (f"{response.json()['city'] if 'city' in response.json() else 'No City'}, "
                      f"{response.json()['country'] if 'country' in response.json() else 'No Country'}, "
                      f"{response.json()['org'] if 'org' in response.json() else 'No Organisation'}")
            if type(result) is tuple:
                result = result[0]
            return result, token
        elif response.status_code == 429:
            token = get_next_token()
            return get_response(url, ip_address, token), token
    except Exception as e_req:
        print(f'Request execution error: {url + ip_address + token} ({str(e_req)})')


def handler(input_file, delimiter, url, token, output_file_all_ip, output_file_ukr_ip, output_file_ukr_mobile_ip):
    try:
        df = read_csv(input_file, delimiter=delimiter, index_col='ID')
        ip_list = list(df.get('IP Address'.strip()))
        result_list = []
        count_resp_db = 0
        count_resp_ipinfo = 0
        count_insert_db = 0
        count_update_db = 0
        try:
            with connect(DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute(q['CREATE_TABLE'])
                for ip in range(0, len(ip_list)):
                    if ip_list[ip] is not nan:
                        if str(ip_list[ip]).strip():
                            cur.execute(q['GET_IP'], (ip_list[ip],))
                            row = cur.fetchone()
                            # check if IP exists in DB
                            if row is None:
                                # IP absent then make a request and insert result into DB
                                whois, token = get_response(url, ip_list[ip], token)
                                count_resp_ipinfo += 1
                                result_list.append(whois)
                                cur.execute(q['INSERT_IP'], (ip_list[ip], whois,))
                                conn.commit()
                                count_insert_db += 1
                            else:
                                # IP exist in DB
                                # get date now and calculate out of date (limit_date)
                                db_update_at = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                                today = datetime.now().replace(microsecond=0)
                                limit_date = today - timedelta(days=LIMIT_DAY)
                                # if IP date in DB is out of date
                                # then make a request and update IP date in DB
                                if db_update_at < limit_date:
                                    whois, token = get_response(url, ip_list[ip], token)
                                    count_resp_ipinfo += 1
                                    result_list.append(whois)
                                    cur.execute(q['UPDATE_IP'], (whois, today, ip_list[ip],))
                                    conn.commit()
                                    count_update_db += 1
                                else:
                                    # IP date in DB is fresh
                                    whois = row[2]
                                    result_list.append(whois)
                                    count_resp_db += 1
                        else:  # value of ip_list[ip] is empty
                            result_list.append('')
                    else:  # value of ip_list[ip] is nan
                        result_list.append('')
        except Exception as e_db:
            print(f'DB error: {str(e_db)}')
        df.insert(11, 'Organisation', result_list)
        # -sig is necessary so that the Cyrillic alphabet does not move out and not on Apple (Windows, Android)
        df.to_csv(output_file_all_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        df_ukr_ip = df[(df['Organisation'].str.contains('UA'))]
        df_ukr_mobile_ip = df[(df['Organisation'].str.contains('AS15895')) |
                              (df['Organisation'].str.contains('AS21497')) |
                              (df['Organisation'].str.contains('AS34058'))]
        df_ukr_ip.to_csv(output_file_ukr_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        df_ukr_mobile_ip.to_csv(output_file_ukr_mobile_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        print(f'Number of responses from the database: {count_resp_db}')
        print(f'Number of responses from {IPINFO_URL}: {count_resp_ipinfo}')
        print(f'Number of ip inserted into the database: {count_insert_db}')
        print(f'Number of ip updated in the database: {count_update_db}')
    except Exception as e_csv:
        print(f'CSV error: {str(e_csv)}')


if __name__ == '__main__':
    tkn = get_next_token()
    if LIMIT_DAY == 0:
        LIMIT_DAY = 1
    handler(IN_FILE, SEPARATOR, IPINFO_URL, tkn, OUT_FILE_ALL_IP, OUT_FILE_UKR_IP, OUT_FILE_UKR_MOBILE_IP)
