import requests
import pandas as pd
from datetime import datetime, timedelta

#okres z jakiego chcemy dane
start_date = datetime.strptime("2016-09-04", "%Y-%m-%d")
end_date = datetime.strptime("2018-10-17", "%Y-%m-%d")

wszystkie_kursy = []
aktualna_data = start_date

while aktualna_data <= end_date:
    nastepna_data = aktualna_data + timedelta(days=365)

    if nastepna_data > end_date:
        nastepna_data = end_date

    str_od = aktualna_data.strftime("%Y-%m-%d")
    str_do = nastepna_data.strftime("%Y-%m-%d")

    #tabela A z kursem BRL/PLN z api.nbp.pl
    url = f"http://api.nbp.pl/api/exchangerates/rates/A/BRL/{str_od}/{str_do}/?format=json"
    response = requests.get(url)

    dane_json = response.json()
    wszystkie_kursy.extend(dane_json['rates'])
    aktualna_data = nastepna_data + timedelta(days=1)

dim_waluta = pd.DataFrame(wszystkie_kursy)
dim_waluta['effectiveDate'] = pd.to_datetime(dim_waluta['effectiveDate'])

kalendarz = pd.DataFrame({'effectiveDate': pd.date_range(start=start_date, end=end_date)})

dim_waluta = pd.merge(kalendarz, dim_waluta, on='effectiveDate', how='left')
dim_waluta['mid'] = dim_waluta['mid'].ffill().bfill()
dim_waluta['no'] = dim_waluta['no'].ffill().bfill()

#tworzymy klucz sk dla waluty
dim_waluta['waluta_sk'] = range(1, len(dim_waluta) + 1)
klucz_sk = dim_waluta.pop('waluta_sk')
dim_waluta.insert(0, 'waluta_sk', klucz_sk)

#usuwamy kolumnę 'no', która nie jest nam potrzebna
dim_waluta.drop(columns=['no'], inplace=True)

#podmieniamy nazwy kolumn
dim_waluta.columns = ['waluta_sk', 'data', 'kurs']

print(dim_waluta.info())
print(dim_waluta.head())