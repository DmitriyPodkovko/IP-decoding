# Decoding the organization's IP address from csv using ipinfo
# use nmap - optional
import nmap3
from sys import exit
from pandas import read_csv
from sqlite3 import connect
from requests import get
from numpy import nan
from datetime import datetime, timedelta
from const import constants as c
from db import queries as q


def get_next_token():
    try:
        token = next(c.ITERATOR_TOKENS, '-1')
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
            return result, token
        elif response.status_code == 429:
            token = get_next_token()
            return get_response(url, ip_address, token), token
    except Exception as e_req:
        print(f'Request execution error: {url + ip_address + token} ({str(e_req)})')


def get_cpe(list_cpe, count_cpe):
    result = ''
    for i in range(count_cpe):
        result = (f"{result}"
                  f"{list_cpe[i].get('cpe')} ")
    return result


def get_nmap(ip_address):
    try:
        result = ''
        nmap = nmap3.Nmap()
        response = nmap.nmap_version_detection(ip_address)
        if ip_address in response:
            cnt_ports = len(response.get(ip_address).get('ports')) if 'ports' in response.get(ip_address) else 0
            for i in range(cnt_ports):
                result = (f"{result}"
                          f"{response.get(ip_address).get('ports')[i].get('portid') if 'portid' in response.get(ip_address).get('ports')[i] else ''}/"
                          f"{response.get(ip_address).get('ports')[i].get('protocol') + ' ' if 'protocol' in response.get(ip_address).get('ports')[i] else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('state') + ' ' if 'state' in response.get(ip_address).get('ports')[i] else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('name') + ' ' if 'name' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('product') + ' ' if 'product' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('version') + ' ' if 'version' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('hostname') + ' ' if 'hostname' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('devicetype') + ' ' if 'devicetype' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('ostype') + ' ' if 'ostype' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{response.get(ip_address).get('ports')[i].get('service').get('extrainfo') + ' ' if 'extrainfo' in response.get(ip_address).get('ports')[i].get('service') else ''}" 
                          f"{response.get(ip_address).get('ports')[i].get('service').get('tunnel') + ' ' if 'tunnel' in response.get(ip_address).get('ports')[i].get('service') else ''}"
                          f"{get_cpe(response.get(ip_address).get('ports')[i].get('cpe'), len(response.get(ip_address).get('ports')[i].get('cpe'))) if 'cpe' in response.get(ip_address).get('ports')[i] and len(response.get(ip_address).get('ports')[i].get('cpe')) > 0 else ''}"
                          f"\n")
        print(f'Nmap {ip_address}:\n{result}')
        return result
    except Exception as e_nmap:
        print(f'Nmap execution error: {ip_address} ({str(e_nmap)})')


def handler(input_file, delimiter, url, token, output_file_all_ip, output_file_ukr_ip, output_file_ukr_mobile_ip):
    try:
        df = read_csv(input_file, delimiter=delimiter, index_col='ID')
        ip_list = list(df.get('IP Address'.strip()))
        result_list = []
        if c.NMAP == 1:
            nmap_list = []
            nmap_dict = {}
        count_resp_db = 0
        count_resp_ipinfo = 0
        count_insert_db = 0
        count_update_db = 0
        try:
            with connect(c.DB_NAME) as conn:
                cur = conn.cursor()
                cur.execute(q.QUERIES['CREATE_TABLE'])  # IF NOT EXISTS
                for ip in range(0, len(ip_list)):
                    if ip_list[ip] is not nan:
                        if str(ip_list[ip]).strip():
                            # Select from {DB_NAME}.db
                            cur.execute(q.QUERIES['GET_IP'], (ip_list[ip],))
                            row = cur.fetchone()
                            # check if IP exists in {DB_NAME}.db
                            if row is None:
                                # IP absent then make a request and insert result into {DB_NAME}.db
                                whois, token = get_response(url, ip_list[ip], token)
                                if type(whois) is tuple:
                                    whois = whois[0]
                                count_resp_ipinfo += 1
                                result_list.append(whois)
                                cur.execute(q.QUERIES['INSERT_IP'], (ip_list[ip], whois,))
                                conn.commit()
                                count_insert_db += 1
                            else:
                                # IP exist in {DB_NAME}.db
                                # get date now and calculate out of date (limit_date)
                                db_update_at = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                                today = datetime.now().replace(microsecond=0)
                                limit_date = today - timedelta(days=c.LIMIT_DAY)
                                # if IP date in {DB_NAME}.db is out of date
                                # then make a request and update IP date in {DB_NAME}.db
                                if db_update_at < limit_date:
                                    whois, token = get_response(url, ip_list[ip], token)
                                    count_resp_ipinfo += 1
                                    result_list.append(whois)
                                    cur.execute(q.QUERIES['UPDATE_IP'], (whois, today, ip_list[ip],))
                                    conn.commit()
                                    count_update_db += 1
                                else:
                                    # IP date in {DB_NAME}.db is fresh
                                    whois = row[2]
                                    result_list.append(whois)
                                    count_resp_db += 1
                            if c.NMAP == 1:
                                if ip_list[ip] in nmap_dict:
                                    nmap_list.append(nmap_dict.get(ip_list[ip]))
                                else:
                                    ip_nmap = get_nmap(ip_list[ip])
                                    nmap_dict[ip_list[ip]] = ip_nmap
                                    nmap_list.append(ip_nmap)
                        else:  # value of ip_list[ip] is empty
                            result_list.append('')
                            if c.NMAP == 1:
                                nmap_list.append('')
                    else:  # value of ip_list[ip] is nan
                        result_list.append('')
                        if c.NMAP == 1:
                            nmap_list.append('')
        except Exception as e_db:
            print(f'DB error: {str(e_db)}')
        df.insert(11, 'Organisation', result_list)
        if c.NMAP == 1:
            df.insert(12, 'Nmap', nmap_list)
        # -sig is necessary so that the Cyrillic alphabet does not move out and not on Apple (Windows, Android)
        df.to_csv(output_file_all_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        df_ukr_ip = df[(df['Organisation'].str.contains('UA'))]
        df_ukr_mobile_ip = df[(df['Organisation'].str.contains('AS15895')) |
                              (df['Organisation'].str.contains('AS21497')) |
                              (df['Organisation'].str.contains('AS34058'))]
        df_ukr_ip.to_csv(output_file_ukr_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        df_ukr_mobile_ip.to_csv(output_file_ukr_mobile_ip, sep=delimiter, index=True, header=True, encoding='utf-8-sig')
        print(f'Number of responses from the database: {count_resp_db}')
        print(f'Number of responses from {c.IPINFO_URL}: {count_resp_ipinfo}')
        print(f'Number of ip inserted into the database: {count_insert_db}')
        print(f'Number of ip updated in the database: {count_update_db}')
    except Exception as e_csv:
        print(f'CSV error: {str(e_csv)}')


if __name__ == '__main__':
    tkn = get_next_token()
    if c.LIMIT_DAY == 0:
        c.LIMIT_DAY = 1
    handler(c.IN_FILE, c.SEPARATOR, c.IPINFO_URL, tkn, c.OUT_FILE_ALL_IP, c.OUT_FILE_UKR_IP, c.OUT_FILE_UKR_MOBILE_IP)
