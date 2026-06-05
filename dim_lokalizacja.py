import pandas as pd

#tworzymy dataframe z pliku csv
dim_lokalizacja = pd.read_csv('olist_geolocation_dataset.csv')

#usuwamy duplikaty, nie chcemy 2 takich samych lokalizacji
dim_lokalizacja.drop_duplicates(inplace=True)

#zmieniamy sobie nazwy
dim_lokalizacja.columns = ['zip', 'latitude', 'longitude', 'miasto', 'stan']

dim_lokalizacja['geo_sk'] = range(1, len(dim_lokalizacja) + 1)
klucz_sk = dim_lokalizacja.pop('geo_sk')
dim_lokalizacja.insert(0, 'geo_sk', klucz_sk)

dim_lokalizacja['miasto'] = dim_lokalizacja['miasto'].astype('string')
dim_lokalizacja['stan'] = dim_lokalizacja['stan'].astype('string')

print(dim_lokalizacja.info())