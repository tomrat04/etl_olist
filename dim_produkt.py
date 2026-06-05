import pandas as pd

#tworzymy dataframy z pliu csv
dim_produkt = pd.read_csv('olist_products_dataset.csv')
translation = pd.read_csv('product_category_name_translation.csv')

#laczymy, aby dostac angielskie nazwy kategorii
dim_produkt = pd.merge(dim_produkt, translation, on='product_category_name', how='left')

#usuwamy i zmieniamy nazwy kolumn
dim_produkt.drop(columns=["product_name_lenght","product_description_lenght","product_photos_qty"], inplace=True)
dim_produkt.columns = ['product_id', 'kategoria_oryginalna', 'waga_g', 'dlugosc_cm', 'wysokosc_cm', 'szerokosc_cm', 'kategoria_en']

#zmieniamy pozycje kolumny
kat = dim_produkt.pop('kategoria_en')
dim_produkt.insert(2, 'kategoria_en', kat)

#usuwamy duplikaty, nie chcemy 2 takich samych produktów
dim_produkt.drop_duplicates(inplace=True)

#tworzymy klucz sk
dim_produkt['product_sk'] = range(1, len(dim_produkt) + 1)
klucz_sk = dim_produkt.pop('product_sk')
dim_produkt.insert(0, 'product_sk', klucz_sk)

#zamiana wartości object na varchar
dim_produkt['product_id'] = dim_produkt['product_id'].astype('string')
dim_produkt['kategoria_oryginalna'] = dim_produkt['kategoria_oryginalna'].astype('string')
dim_produkt['kategoria_en'] = dim_produkt['kategoria_en'].astype('string')

print(dim_produkt.info())