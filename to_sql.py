import urllib.parse

import pandas as pd
from sqlalchemy import create_engine, event, text

SERVER = 'localhost'
BAZA = 'OlistDW'
STEROWNIK = 'ODBC Driver 17 for SQL Server'
UZYTKOWNIK = ''
HASLO = ''
WINDOWS_AUTH = True

#importujemy gotowe ramki danych z etl
from dim_klient import dim_klient
from dim_produkt import dim_produkt
from dim_lokalizacja import dim_lokalizacja
from dim_waluta import dim_waluta
from dim_czas import dim_czas
from dim_sprzedawca import dim_sprzedawca
from dim_status_zamowienia import dim_status_zamowienia
from fakt_zamowienie import fakt_zamowienie
from fakt_platnosci import fakt_platnosci
from fakt_opinie import fakt_opinie


def utworz_polaczenie(baza=BAZA):
    if WINDOWS_AUTH:
        connection_string = (
            f'DRIVER={{{STEROWNIK}}};'
            f'SERVER={SERVER};'
            f'DATABASE={baza};'
            f'Trusted_Connection=yes;'
        )
    else:
        connection_string = (
            f'DRIVER={{{STEROWNIK}}};'
            f'SERVER={SERVER};'
            f'DATABASE={baza};'
            f'UID={UZYTKOWNIK};'
            f'PWD={HASLO};'
        )

    odbc_connect = urllib.parse.quote_plus(connection_string)
    engine = create_engine(f'mssql+pyodbc:///?odbc_connect={odbc_connect}')

    #przyspiesza wsadowe inserty w sql server
    @event.listens_for(engine, 'before_cursor_execute')
    def wlacz_fast_executemany(conn, cursor, statement, params, context, executemany):
        if executemany:
            cursor.fast_executemany = True

    return engine


def utworz_baze():
    engine_master = utworz_polaczenie('master')
    with engine_master.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.execute(text(
            f"IF DB_ID('{BAZA}') IS NULL CREATE DATABASE [{BAZA}]"
        ))


def usun_tabele(engine):
    polecenia = [
        "IF OBJECT_ID('dbo.fakt_zamowienie', 'U') IS NOT NULL DROP TABLE dbo.fakt_zamowienie",
        "IF OBJECT_ID('dbo.fakt_platnosci', 'U') IS NOT NULL DROP TABLE dbo.fakt_platnosci",
        "IF OBJECT_ID('dbo.fakt_opinie', 'U') IS NOT NULL DROP TABLE dbo.fakt_opinie",
        "IF OBJECT_ID('dbo.dim_klient', 'U') IS NOT NULL DROP TABLE dbo.dim_klient",
        "IF OBJECT_ID('dbo.dim_produkt', 'U') IS NOT NULL DROP TABLE dbo.dim_produkt",
        "IF OBJECT_ID('dbo.dim_lokalizacja', 'U') IS NOT NULL DROP TABLE dbo.dim_lokalizacja",
        "IF OBJECT_ID('dbo.dim_waluta', 'U') IS NOT NULL DROP TABLE dbo.dim_waluta",
        "IF OBJECT_ID('dbo.dim_czas', 'U') IS NOT NULL DROP TABLE dbo.dim_czas",
        "IF OBJECT_ID('dbo.dim_sprzedawca', 'U') IS NOT NULL DROP TABLE dbo.dim_sprzedawca",
        "IF OBJECT_ID('dbo.dim_status_zamowienia', 'U') IS NOT NULL DROP TABLE dbo.dim_status_zamowienia",
    ]

    with engine.connect() as conn:
        for polecenie in polecenia:
            conn.execute(text(polecenie))
        conn.commit()


def utworz_tabele(engine):
    ddl = """
    CREATE TABLE dbo.dim_klient (
        customer_sk INT NOT NULL PRIMARY KEY,
        customer_id VARCHAR(64) NOT NULL,
        zip_klienta VARCHAR(10) NOT NULL,
        miasto VARCHAR(100) NOT NULL,
        stan CHAR(2) NOT NULL
    );

    CREATE TABLE dbo.dim_produkt (
        product_sk INT NOT NULL PRIMARY KEY,
        product_id VARCHAR(64) NOT NULL,
        kategoria_oryginalna VARCHAR(100) NULL,
        kategoria_en VARCHAR(100) NULL,
        waga_g FLOAT NULL,
        dlugosc_cm FLOAT NULL,
        wysokosc_cm FLOAT NULL,
        szerokosc_cm FLOAT NULL
    );

    CREATE TABLE dbo.dim_lokalizacja (
        geo_sk INT NOT NULL PRIMARY KEY,
        zip INT NOT NULL,
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL,
        miasto VARCHAR(100) NOT NULL,
        stan CHAR(2) NOT NULL
    );

    CREATE TABLE dbo.dim_waluta (
        waluta_sk INT NOT NULL PRIMARY KEY,
        data DATE NOT NULL,
        kurs DECIMAL(10, 6) NOT NULL
    );

    CREATE TABLE dbo.dim_czas (
        time_sk INT NOT NULL PRIMARY KEY,
        data DATE NOT NULL,
        dzien TINYINT NOT NULL,
        miesiac TINYINT NOT NULL,
        nazwa_miesiaca VARCHAR(20) NOT NULL,
        kwartal TINYINT NOT NULL,
        oznaczenie_kwartalu VARCHAR(10) NOT NULL,
        pora_roku VARCHAR(20) NOT NULL,
        rok SMALLINT NOT NULL
    );

    CREATE TABLE dbo.dim_sprzedawca (
        seller_sk INT NOT NULL PRIMARY KEY,
        seller_id VARCHAR(64) NOT NULL,
        zip_sprzedawcy VARCHAR(10) NOT NULL,
        miasto_sprzedawcy VARCHAR(100) NOT NULL,
        stan_sprzedawcy CHAR(2) NOT NULL
    );

    CREATE TABLE dbo.dim_status_zamowienia (
        status_sk INT NOT NULL PRIMARY KEY,
        status_zamowienia VARCHAR(30) NOT NULL
    );

    CREATE TABLE dbo.fakt_zamowienie (
        order_item_sk BIGINT NOT NULL PRIMARY KEY,
        order_id VARCHAR(64) NOT NULL,
        order_item_id TINYINT NOT NULL,
        customer_sk INT NOT NULL,
        product_sk INT NOT NULL,
        seller_sk INT NOT NULL,
        time_sk INT NOT NULL,
        geo_sk INT NOT NULL,
        waluta_sk INT NOT NULL,
        status_sk INT NOT NULL,
        cena_BRL DECIMAL(12, 2) NOT NULL,
        cena_PLN DECIMAL(12, 2) NOT NULL,
        cena_BRL_skorygowana DECIMAL(12, 2) NULL,
        freight_value DECIMAL(12, 2) NOT NULL,
        delay_days SMALLINT NULL,
        is_late BIT NOT NULL,
        is_delivered BIT NOT NULL
    );

    CREATE TABLE dbo.fakt_platnosci (
        payment_sk BIGINT NOT NULL PRIMARY KEY,
        order_id VARCHAR(64) NOT NULL,
        customer_sk INT NOT NULL,
        time_sk INT NOT NULL,
        waluta_sk INT NOT NULL,
        typ_platnosci VARCHAR(30) NOT NULL,
        wartosc_platnosci_BRL DECIMAL(12, 2) NOT NULL,
        wartosc_platnosci_PLN DECIMAL(12, 2) NOT NULL,
        liczba_rat TINYINT NOT NULL
    );

    CREATE TABLE dbo.fakt_opinie (
        review_sk BIGINT NOT NULL PRIMARY KEY,
        review_id VARCHAR(64) NOT NULL,
        order_id VARCHAR(64) NOT NULL,
        customer_sk INT NOT NULL,
        time_sk INT NOT NULL,
        ocena_klienta TINYINT NOT NULL,
        liczba_ocen TINYINT NOT NULL,
        czas_odpowiedzi_h DECIMAL(8, 2) NULL
    );
    """

    with engine.connect() as conn:
        for polecenie in ddl.strip().split(';'):
            if polecenie.strip():
                conn.execute(text(polecenie))
        conn.commit()


def dodaj_klucze_obce(engine):
    fk = """
    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_klient FOREIGN KEY (customer_sk) REFERENCES dbo.dim_klient(customer_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_produkt FOREIGN KEY (product_sk) REFERENCES dbo.dim_produkt(product_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_sprzedawca FOREIGN KEY (seller_sk) REFERENCES dbo.dim_sprzedawca(seller_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_czas FOREIGN KEY (time_sk) REFERENCES dbo.dim_czas(time_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_lokalizacja FOREIGN KEY (geo_sk) REFERENCES dbo.dim_lokalizacja(geo_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_waluta FOREIGN KEY (waluta_sk) REFERENCES dbo.dim_waluta(waluta_sk);

    ALTER TABLE dbo.fakt_zamowienie
        ADD CONSTRAINT FK_fakt_zamowienie_status FOREIGN KEY (status_sk) REFERENCES dbo.dim_status_zamowienia(status_sk);

    ALTER TABLE dbo.fakt_platnosci
        ADD CONSTRAINT FK_fakt_platnosci_klient FOREIGN KEY (customer_sk) REFERENCES dbo.dim_klient(customer_sk);

    ALTER TABLE dbo.fakt_platnosci
        ADD CONSTRAINT FK_fakt_platnosci_czas FOREIGN KEY (time_sk) REFERENCES dbo.dim_czas(time_sk);

    ALTER TABLE dbo.fakt_platnosci
        ADD CONSTRAINT FK_fakt_platnosci_waluta FOREIGN KEY (waluta_sk) REFERENCES dbo.dim_waluta(waluta_sk);

    ALTER TABLE dbo.fakt_opinie
        ADD CONSTRAINT FK_fakt_opinie_klient FOREIGN KEY (customer_sk) REFERENCES dbo.dim_klient(customer_sk);

    ALTER TABLE dbo.fakt_opinie
        ADD CONSTRAINT FK_fakt_opinie_czas FOREIGN KEY (time_sk) REFERENCES dbo.dim_czas(time_sk);
    """

    with engine.connect() as conn:
        for polecenie in fk.strip().split(';'):
            if polecenie.strip():
                conn.execute(text(polecenie))
        conn.commit()


def przygotuj_ramke(df):
    ramka = df.copy()

    for kolumna in ramka.columns:
        if pd.api.types.is_datetime64_any_dtype(ramka[kolumna]):
            ramka[kolumna] = pd.to_datetime(ramka[kolumna]).dt.normalize()

    return ramka


def zaladuj_tabele(engine, nazwa_tabeli, ramka):
    ramka = przygotuj_ramke(ramka)
    #bez method='multi' - sql server ma limit 2100 parametrow na zapytanie
    ramka.to_sql(
        nazwa_tabeli,
        engine,
        schema='dbo',
        if_exists='append',
        index=False,
        chunksize=1000
    )
    print(f'Zaladowano {len(ramka)} wierszy do {nazwa_tabeli}')


utworz_baze()
engine = utworz_polaczenie()

usun_tabele(engine)
utworz_tabele(engine)

#najpierw wymiary, potem fakty
wymiary = [
    ('dim_klient', dim_klient),
    ('dim_produkt', dim_produkt),
    ('dim_lokalizacja', dim_lokalizacja),
    ('dim_waluta', dim_waluta),
    ('dim_czas', dim_czas),
    ('dim_sprzedawca', dim_sprzedawca),
    ('dim_status_zamowienia', dim_status_zamowienia),
]

fakty = [
    ('fakt_zamowienie', fakt_zamowienie),
    ('fakt_platnosci', fakt_platnosci),
    ('fakt_opinie', fakt_opinie),
]

for nazwa, ramka in wymiary:
    zaladuj_tabele(engine, nazwa, ramka)

for nazwa, ramka in fakty:
    zaladuj_tabele(engine, nazwa, ramka)

dodaj_klucze_obce(engine)
print('Zaladowano caly schemat do SQL Server.')
