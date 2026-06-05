import pandas as pd

#pobieramy daty ze zbiorow, aby pokryc caly zakres wymiaru czasu
orders = pd.read_csv('olist_orders_dataset.csv', usecols=['order_purchase_timestamp'])
reviews = pd.read_csv('olist_order_reviews_dataset.csv', usecols=['review_creation_date'])

orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
reviews['review_creation_date'] = pd.to_datetime(reviews['review_creation_date'])

data_min = min(orders['order_purchase_timestamp'].min(), reviews['review_creation_date'].min()).normalize()
data_max = max(orders['order_purchase_timestamp'].max(), reviews['review_creation_date'].max()).normalize()

dim_czas = pd.DataFrame({'data': pd.date_range(start=data_min, end=data_max, freq='D')})

#atrybuty kalendarzowe
dim_czas['dzien'] = dim_czas['data'].dt.day.astype('int8')
dim_czas['miesiac'] = dim_czas['data'].dt.month.astype('int8')
dim_czas['rok'] = dim_czas['data'].dt.year.astype('int16')

nazwy_miesiecy = {
    1: 'Styczeń', 2: 'Luty', 3: 'Marzec', 4: 'Kwiecień',
    5: 'Maj', 6: 'Czerwiec', 7: 'Lipiec', 8: 'Sierpień',
    9: 'Wrzesień', 10: 'Październik', 11: 'Listopad', 12: 'Grudzień'
}
dim_czas['nazwa_miesiaca'] = dim_czas['miesiac'].map(nazwy_miesiecy).astype('string')

dim_czas['kwartal'] = dim_czas['data'].dt.quarter.astype('int8')
dim_czas['oznaczenie_kwartalu'] = ('Q' + dim_czas['kwartal'].astype(str)).astype('string')

def pora_roku(miesiac):
    if miesiac in [3, 4, 5]:
        return 'Wiosna'
    if miesiac in [6, 7, 8]:
        return 'Lato'
    if miesiac in [9, 10, 11]:
        return 'Jesień'
    return 'Zima'

dim_czas['pora_roku'] = dim_czas['miesiac'].apply(pora_roku).astype('string')

#tworzymy klucz sk
dim_czas['time_sk'] = range(1, len(dim_czas) + 1)
klucz_sk = dim_czas.pop('time_sk')
dim_czas.insert(0, 'time_sk', klucz_sk)

#data jako datetime bez czasu
dim_czas['data'] = pd.to_datetime(dim_czas['data']).dt.normalize()

print(dim_czas.info())
print(dim_czas.head())
