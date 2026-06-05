import pandas as pd

#tworzymy dataframy z pliku csv
dim_klient = pd.read_csv('olist_customers_dataset.csv')

#usuwanie kolumn
dim_klient.drop(columns=['customer_unique_id'], inplace=True)

#zmiana nazw kolumn
dim_klient.columns = ['customer_id', 'zip_klienta', 'miasto', 'stan']

#zamiana wartości object na varchar
dim_klient['customer_id'] = dim_klient['customer_id'].astype('string')
dim_klient['zip_klienta'] = dim_klient['zip_klienta'].astype('string')
dim_klient['miasto'] = dim_klient['miasto'].astype('string')
dim_klient['stan'] = dim_klient['stan'].astype('string')

#usuwamy duplikaty, nie chcemy 2 takich samych klientów
dim_klient.drop_duplicates(inplace=True)

#dodanie sk
dim_klient['customer_sk'] = range(1, len(dim_klient) + 1)
klucz_sk = dim_klient.pop('customer_sk')
dim_klient.insert(0, 'customer_sk', klucz_sk)

print(dim_klient.info())
print(dim_klient.head())