import pandas as pd

from dim_klient import dim_klient
from dim_czas import dim_czas

#tworzymy dataframy z plikow csv
reviews = pd.read_csv('olist_order_reviews_dataset.csv')
orders = pd.read_csv('olist_orders_dataset.csv', usecols=['order_id', 'customer_id'])

#laczymy opinie z zamowieniami, aby uzyskac klienta
fakt_opinie = pd.merge(reviews, orders, on='order_id', how='inner')

fakt_opinie['review_creation_date'] = pd.to_datetime(fakt_opinie['review_creation_date'])
fakt_opinie['review_answer_timestamp'] = pd.to_datetime(fakt_opinie['review_answer_timestamp'])

#laczymy z wymiarami
fakt_opinie = pd.merge(fakt_opinie, dim_klient, on='customer_id', how='inner')

fakt_opinie['data_opinii'] = fakt_opinie['review_creation_date'].dt.normalize()
dim_czas_lookup = dim_czas[['time_sk', 'data']].copy()
fakt_opinie = pd.merge(fakt_opinie, dim_czas_lookup, left_on='data_opinii', right_on='data', how='inner', suffixes=('', '_czas'))

#liczba ocen w ramach zamowienia
liczba_ocen_zamowienia = fakt_opinie.groupby('order_id')['review_id'].transform('count')

#metryki opinii
fakt_opinie['ocena_klienta'] = fakt_opinie['review_score'].astype('int8')
fakt_opinie['liczba_ocen'] = liczba_ocen_zamowienia.astype('int8')
fakt_opinie['czas_odpowiedzi_h'] = (
    (fakt_opinie['review_answer_timestamp'] - fakt_opinie['review_creation_date']).dt.total_seconds() / 3600
).round(2)

#wybieramy kolumny zgodne ze schematem
fakt_opinie = fakt_opinie[[
    'review_id', 'order_id', 'customer_sk', 'time_sk',
    'ocena_klienta', 'liczba_ocen', 'czas_odpowiedzi_h'
]].copy()

#usuwamy duplikaty opinii
fakt_opinie.drop_duplicates(subset=['review_id'], inplace=True)

#zamiana wartosci object na varchar
fakt_opinie['review_id'] = fakt_opinie['review_id'].astype('string')
fakt_opinie['order_id'] = fakt_opinie['order_id'].astype('string')

#tworzymy klucz sk
fakt_opinie['review_sk'] = range(1, len(fakt_opinie) + 1)
klucz_sk = fakt_opinie.pop('review_sk')
fakt_opinie.insert(0, 'review_sk', klucz_sk)

print(fakt_opinie.info())
print(fakt_opinie.head())
