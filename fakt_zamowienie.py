import pandas as pd
import numpy as np

from dim_klient import dim_klient
from dim_produkt import dim_produkt
from dim_lokalizacja import dim_lokalizacja
from dim_waluta import dim_waluta
from dim_czas import dim_czas
from dim_sprzedawca import dim_sprzedawca
from dim_status_zamowienia import dim_status_zamowienia

#tworzymy dataframy z plikow csv
order_items = pd.read_csv('olist_order_items_dataset.csv')
orders = pd.read_csv('olist_orders_dataset.csv')

#laczymy pozycje zamowien z naglowkami zamowien
fakt_zamowienie = pd.merge(order_items, orders, on='order_id', how='inner')

#konwersja dat
fakt_zamowienie['order_purchase_timestamp'] = pd.to_datetime(fakt_zamowienie['order_purchase_timestamp'])
fakt_zamowienie['order_delivered_customer_date'] = pd.to_datetime(fakt_zamowienie['order_delivered_customer_date'])
fakt_zamowienie['order_estimated_delivery_date'] = pd.to_datetime(fakt_zamowienie['order_estimated_delivery_date'])

#laczymy z wymiarami
fakt_zamowienie = pd.merge(fakt_zamowienie, dim_klient, on='customer_id', how='inner')
fakt_zamowienie = pd.merge(fakt_zamowienie, dim_produkt[['product_sk', 'product_id']], on='product_id', how='inner')
fakt_zamowienie = pd.merge(fakt_zamowienie, dim_sprzedawca[['seller_sk', 'seller_id']], on='seller_id', how='inner')
fakt_zamowienie = pd.merge(fakt_zamowienie, dim_status_zamowienia, left_on='order_status', right_on='status_zamowienia', how='inner')

#dla lokalizacji bierzemy pierwszy rekord dla kombinacji zip+miasto+stan
geo_lookup = dim_lokalizacja.drop_duplicates(subset=['zip', 'miasto', 'stan'], keep='first').copy()
geo_lookup['zip'] = geo_lookup['zip'].astype('string')
fakt_zamowienie = pd.merge(
    fakt_zamowienie,
    geo_lookup[['geo_sk', 'zip', 'miasto', 'stan']],
    left_on=['zip_klienta', 'miasto', 'stan'],
    right_on=['zip', 'miasto', 'stan'],
    how='inner'
)

#laczymy z wymiarem czasu po dacie zakupu
fakt_zamowienie['data_zakupu'] = fakt_zamowienie['order_purchase_timestamp'].dt.normalize()
dim_czas_lookup = dim_czas[['time_sk', 'data']].copy()
fakt_zamowienie = pd.merge(fakt_zamowienie, dim_czas_lookup, left_on='data_zakupu', right_on='data', how='inner', suffixes=('', '_czas'))

#laczymy z wymiarem waluty po dacie zakupu
dim_waluta_lookup = dim_waluta.copy()
dim_waluta_lookup['data'] = pd.to_datetime(dim_waluta_lookup['data']).dt.normalize()
fakt_zamowienie = pd.merge(
    fakt_zamowienie,
    dim_waluta_lookup[['waluta_sk', 'data', 'kurs']],
    left_on='data_zakupu',
    right_on='data',
    how='inner',
    suffixes=('', '_waluta')
)

#przygotowanie wspolczynnika inflacji do korekty cen BRL
inflacja = pd.read_csv('brazil_inflation.csv', sep=';', skiprows=1, names=['okres', 'inflacja_miesieczna'])
inflacja['okres'] = pd.to_datetime(inflacja['okres'], format='%m/%Y')
inflacja['inflacja_miesieczna'] = inflacja['inflacja_miesieczna'].astype(float)
inflacja['wspolczynnik'] = 1 + inflacja['inflacja_miesieczna'] / 100
inflacja['indeks_cpi'] = inflacja['wspolczynnik'].cumprod()
indeks_bazowy = inflacja['indeks_cpi'].iloc[-1]

fakt_zamowienie['okres_zakupu'] = fakt_zamowienie['order_purchase_timestamp'].dt.to_period('M').dt.to_timestamp()
inflacja_lookup = inflacja[['okres', 'indeks_cpi']].rename(columns={'okres': 'okres_zakupu'})
fakt_zamowienie = pd.merge(fakt_zamowienie, inflacja_lookup, on='okres_zakupu', how='left')
fakt_zamowienie['indeks_cpi'] = fakt_zamowienie['indeks_cpi'].ffill().bfill()

#metryki zamowienia
fakt_zamowienie['cena_BRL'] = fakt_zamowienie['price'].round(2)
fakt_zamowienie['cena_PLN'] = (fakt_zamowienie['cena_BRL'] * fakt_zamowienie['kurs']).round(2)
fakt_zamowienie['cena_BRL_skorygowana'] = (
    fakt_zamowienie['cena_BRL'] * (indeks_bazowy / fakt_zamowienie['indeks_cpi'])
).round(2)
fakt_zamowienie['freight_value'] = fakt_zamowienie['freight_value'].round(2)

fakt_zamowienie['is_delivered'] = (fakt_zamowienie['order_status'] == 'delivered').astype('int8')
fakt_zamowienie['delay_days'] = np.where(
    fakt_zamowienie['is_delivered'] == 1,
    (fakt_zamowienie['order_delivered_customer_date'] - fakt_zamowienie['order_estimated_delivery_date']).dt.days,
    np.nan
)
fakt_zamowienie['delay_days'] = fakt_zamowienie['delay_days'].astype('Int16')
fakt_zamowienie['is_late'] = (
    (fakt_zamowienie['is_delivered'] == 1) & (fakt_zamowienie['delay_days'] > 0)
).fillna(False).astype('int8')

#wybieramy kolumny zgodne ze schematem
fakt_zamowienie = fakt_zamowienie[[
    'order_id', 'order_item_id', 'customer_sk', 'product_sk', 'seller_sk', 'time_sk',
    'geo_sk', 'waluta_sk', 'status_sk', 'cena_BRL', 'cena_PLN', 'cena_BRL_skorygowana',
    'freight_value', 'delay_days', 'is_late', 'is_delivered'
]].copy()

#usuwamy duplikaty pozycji zamowien
fakt_zamowienie.drop_duplicates(subset=['order_id', 'order_item_id'], inplace=True)

#zamiana wartosci object na varchar
fakt_zamowienie['order_id'] = fakt_zamowienie['order_id'].astype('string')
fakt_zamowienie['order_item_id'] = fakt_zamowienie['order_item_id'].astype('int8')

#tworzymy klucz sk
fakt_zamowienie['order_item_sk'] = range(1, len(fakt_zamowienie) + 1)
klucz_sk = fakt_zamowienie.pop('order_item_sk')
fakt_zamowienie.insert(0, 'order_item_sk', klucz_sk)

print(fakt_zamowienie.info())
print(fakt_zamowienie.head())