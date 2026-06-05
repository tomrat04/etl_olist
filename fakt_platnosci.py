import pandas as pd

from dim_klient import dim_klient
from dim_waluta import dim_waluta
from dim_czas import dim_czas

#tworzymy dataframy z plikow csv
payments = pd.read_csv('olist_order_payments_dataset.csv')
orders = pd.read_csv('olist_orders_dataset.csv', usecols=['order_id', 'customer_id', 'order_purchase_timestamp'])

#laczymy platnosci z zamowieniami, aby uzyskac klienta i date zakupu
fakt_platnosci = pd.merge(payments, orders, on='order_id', how='inner')

fakt_platnosci['order_purchase_timestamp'] = pd.to_datetime(fakt_platnosci['order_purchase_timestamp'])

#laczymy z wymiarami
fakt_platnosci = pd.merge(fakt_platnosci, dim_klient, on='customer_id', how='inner')

fakt_platnosci['data_zakupu'] = fakt_platnosci['order_purchase_timestamp'].dt.normalize()
dim_czas_lookup = dim_czas[['time_sk', 'data']].copy()
fakt_platnosci = pd.merge(fakt_platnosci, dim_czas_lookup, left_on='data_zakupu', right_on='data', how='inner', suffixes=('', '_czas'))

dim_waluta_lookup = dim_waluta.copy()
dim_waluta_lookup['data'] = pd.to_datetime(dim_waluta_lookup['data']).dt.normalize()
fakt_platnosci = pd.merge(
    fakt_platnosci,
    dim_waluta_lookup[['waluta_sk', 'data', 'kurs']],
    left_on='data_zakupu',
    right_on='data',
    how='inner',
    suffixes=('', '_waluta')
)

#metryki platnosci
fakt_platnosci['wartosc_platnosci_BRL'] = fakt_platnosci['payment_value'].round(2)
fakt_platnosci['wartosc_platnosci_PLN'] = (fakt_platnosci['wartosc_platnosci_BRL'] * fakt_platnosci['kurs']).round(2)

#wybieramy kolumny zgodne ze schematem
fakt_platnosci = fakt_platnosci[[
    'order_id', 'customer_sk', 'time_sk', 'waluta_sk',
    'payment_type', 'wartosc_platnosci_BRL', 'wartosc_platnosci_PLN', 'payment_installments'
]].copy()

#zmiana nazw kolumn
fakt_platnosci.rename(columns={
    'payment_type': 'typ_platnosci',
    'payment_installments': 'liczba_rat'
}, inplace=True)

#usuwamy duplikaty platnosci
fakt_platnosci.drop_duplicates(inplace=True)

#zamiana wartosci object na varchar
fakt_platnosci['order_id'] = fakt_platnosci['order_id'].astype('string')
fakt_platnosci['typ_platnosci'] = fakt_platnosci['typ_platnosci'].astype('string')
fakt_platnosci['liczba_rat'] = fakt_platnosci['liczba_rat'].astype('int8')

#tworzymy klucz sk
fakt_platnosci['payment_sk'] = range(1, len(fakt_platnosci) + 1)
klucz_sk = fakt_platnosci.pop('payment_sk')
fakt_platnosci.insert(0, 'payment_sk', klucz_sk)

print(fakt_platnosci.info())
print(fakt_platnosci.head())
