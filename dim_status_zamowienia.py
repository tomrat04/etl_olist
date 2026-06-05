import pandas as pd

#tworzymy dataframe z pliku csv
orders = pd.read_csv('olist_orders_dataset.csv', usecols=['order_status'])

#wyciagamy unikalne statusy zamowien
dim_status_zamowienia = orders.drop_duplicates().dropna()
dim_status_zamowienia.columns = ['status_zamowienia']

#sortujemy, aby statusy byly uporzadkowane
dim_status_zamowienia = dim_status_zamowienia.sort_values('status_zamowienia').reset_index(drop=True)

#zamiana wartosci object na varchar
dim_status_zamowienia['status_zamowienia'] = dim_status_zamowienia['status_zamowienia'].astype('string')

#tworzymy klucz sk
dim_status_zamowienia['status_sk'] = range(1, len(dim_status_zamowienia) + 1)
klucz_sk = dim_status_zamowienia.pop('status_sk')
dim_status_zamowienia.insert(0, 'status_sk', klucz_sk)

print(dim_status_zamowienia.info())
print(dim_status_zamowienia.head(10))
