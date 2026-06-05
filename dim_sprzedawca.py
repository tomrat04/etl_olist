import pandas as pd

#tworzymy dataframe z pliku csv
dim_sprzedawca = pd.read_csv('olist_sellers_dataset.csv')

#zmiana nazw kolumn
dim_sprzedawca.columns = ['seller_id', 'zip_sprzedawcy', 'miasto_sprzedawcy', 'stan_sprzedawcy']

#usuwamy duplikaty, nie chcemy 2 takich samych sprzedawcow
dim_sprzedawca.drop_duplicates(inplace=True)

#zamiana wartosci object na varchar
dim_sprzedawca['seller_id'] = dim_sprzedawca['seller_id'].astype('string')
dim_sprzedawca['zip_sprzedawcy'] = dim_sprzedawca['zip_sprzedawcy'].astype('string')
dim_sprzedawca['miasto_sprzedawcy'] = dim_sprzedawca['miasto_sprzedawcy'].astype('string')
dim_sprzedawca['stan_sprzedawcy'] = dim_sprzedawca['stan_sprzedawcy'].astype('string')

#tworzymy klucz sk
dim_sprzedawca['seller_sk'] = range(1, len(dim_sprzedawca) + 1)
klucz_sk = dim_sprzedawca.pop('seller_sk')
dim_sprzedawca.insert(0, 'seller_sk', klucz_sk)

print(dim_sprzedawca.info())
print(dim_sprzedawca.head())
