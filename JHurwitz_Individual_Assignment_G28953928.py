# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 10:51:27 2015

@author: jhurwitz
GWID: G28953928
Individual Assignment

"""

#############################################################################
#   Import Modules
#############################################################################

from pandas.io import wb
import pandas as pd
from pandas.io import sql
import sqlite3 as db
import os

#############################################################################
#   Download World Bank Data Indicators
#############################################################################

# SP.DYN.CBRT.IN: Birth rate, crude (per 1,000 people) 
#   http://data.worldbank.org/indicator/SP.DYN.CBRT.IN

# NY.GNP.PCAP.CD: GNI per capita, Atlas method (current US$)
#   http://data.worldbank.org/indicator/NY.GNP.PCAP.CD

# GC.REV.SOCL.ZS: Social contributions (% of revenue)
#   http://data.worldbank.org/indicator/GC.REV.SOCL.ZS

# SP.POP.65UP.TO.ZS: Population ages 65 and above (% of total)
#   http://data.worldbank.org/indicator/SP.POP.65UP.TO.ZS

df_source = wb.download(indicator=['SP.DYN.CBRT.IN', 'NY.GNP.PCAP.CD', 'GC.REV.SOCL.ZS', 'SP.POP.65UP.TO.ZS'],\
 country='all', start=1960, end=2015)

# Reset index to columns
df_source.reset_index(inplace=True) 

# Rename columns
df_source.columns = ['country', 'year', 'birth_rate', 'gni', 'social_contr', 'age_65' ]

# Fill missing values: http://stackoverflow.com/questions/30587728/pandas-backfilling-a-dataframegroupby-object
df_all = df_source.groupby(df_source.country).apply(lambda g: g.bfill())

# Load country metadata from downloaded file saved in current working directory
wd = os.getcwd()
meta = pd.ExcelFile(wd+'\sp.dyn.cbrt.in_Indicator_en_excel_v2.xls')
meta_df = meta.parse('Metadata - Countries')

#############################################################################
#   Configure SQLite database and plot settings
#############################################################################

# Prepare SQLite db
cnx = db.connect(':memory:')
c = cnx.cursor()
c.execute("drop table if exists wb_data")

# Store meta_df as sql table wb_meta
sql.to_sql(meta_df, name='wb_meta', con=cnx)

# Store df_all as sql table wb_data
sql.to_sql(df_all, name='wb_data', con=cnx)

# Create colors dictionary to display Denmark as red in bar graphs
colors = {'': 'b', 'Denmark': 'r'}

#############################################################################
#   Analysis 1: Denmark's 2013 birth rate relative to world 
#############################################################################

birth_rank_global = sql.read_sql("select a.country, a.birth_rate, \
    case when a.country = 'Denmark' then 'Denmark' else '' end as 'target_country' from wb_data as a join wb_meta as b \
    on a.country = b.[country name] \
    where a.year = 2013 and a.birth_rate > 0 and b.region is not null order by a.birth_rate desc", con=cnx)
# Denmark ranks 184 out of 207, bottom 11%

ax = birth_rank_global[['target_country','birth_rate']].plot(x='target_country', kind='bar', title ="Global Birth Rate Comparison", figsize=(100,20),legend=False, fontsize=12, color=list(birth_rank_global['target_country'].map(colors)))

#############################################################################
#   Analysis 2: Denmark's 2013 birth rate relative to Europe
#############################################################################

birth_rank_europe = sql.read_sql("select a.country, a.birth_rate, case when a.country = 'Denmark' then 'Denmark' else '' end as 'target_country' from wb_data as a join wb_meta as b \
     on a.country = b.[country name] \
     where a.year = 2013 and a.birth_rate > 0 and b.region = 'Europe & Central Asia' order by a.birth_rate desc", con=cnx)
# Denmark ranks 39 out of 56, bottom 30%
     
ax = birth_rank_europe[['country','birth_rate']].plot(x='country', kind='bar', title ="Europe Birth Rate Comparison", figsize=(100,50),legend=False, fontsize=12, color=list(birth_rank_europe['target_country'].map(colors)))

#############################################################################
#   Analysis 3: Denmark's 2013 birth rate relative to High Income OECD countries
#############################################################################

birth_rank_high_income = sql.read_sql("select a.country, a.birth_rate, case when a.country = 'Denmark' then 'Denmark' else '' end as 'target_country' from wb_data as a join wb_meta as b \
     on a.country = b.[country name] \
     where a.year = 2013 and a.birth_rate > 0 and b.IncomeGroup = 'High income: OECD' order by a.birth_rate desc", con=cnx)
# Denmark ranks 22 out of 33, bottom 33%
     
ax = birth_rank_high_income[['country','birth_rate']].plot(x='country', kind='bar', title ="High Income OECD Birth Rate Comparison", figsize=(100,50),legend=False, fontsize=12, color=list(birth_rank_high_income['target_country'].map(colors)))

#############################################################################
#   Analysis 4: Denmark's historical birth rate and 65+ popuulation over time
#############################################################################

birth_rank_dk_historical = sql.read_sql("select country, year, birth_rate, age_65 from wb_data where country = 'Denmark' and year <= 2013 order by year", con=cnx)

ax = birth_rank_dk_historical[['age_65','birth_rate', 'year']].plot(x='year', kind='line', title ="Denmark's Birth Rate Over Time", figsize=(100,50),legend=True, fontsize=12)

#############################################################################
#   Analysis 5: Denmark's historical birth rate relative to peer groups
#############################################################################

birth_rank_historical_europe = sql.read_sql("select country, year, birth_rate from wb_data \
    where country in ('Denmark', 'European Union', 'High income: OECD') \
    and year <= 2013 order by country, year", con=cnx)
pivoted = birth_rank_historical_europe.pivot(columns='country', index='year', values='birth_rate')
pivoted.reset_index(inplace=True)

ax = pivoted[['Denmark','European Union', 'High income: OECD', 'year']].plot(x='year', kind='line', title ="Denmark's Birth Rate Over Time Comparison", figsize=(100,50),legend=True, fontsize=12)

#############################################################################
#   Analysis 6: Denmark's historical age 65 population relative to peer groups
#############################################################################

age_65_historical_europe = sql.read_sql("select country, year, age_65 from wb_data \
    where country in ('Denmark', 'European Union', 'High income: OECD') \
    and year <= 2013 order by country, year", con=cnx)
pivoted = age_65_historical_europe.pivot(columns='country', index='year', values='age_65')
pivoted.reset_index(inplace=True)

ax = pivoted[['Denmark','European Union', 'High income: OECD', 'year']].plot(x='year', kind='line', title ="Denmark's Age 65 Population Over Time Comparison", figsize=(100,50),legend=True, fontsize=12)

#############################################################################
#   Analysis 7: Denmark's historical GNI relative to peer groups
#############################################################################

gni_historical = sql.read_sql("select country, year, gni from wb_data \
    where country in ('Denmark', 'European Union', 'High income: OECD') \
    and year <= 2013 order by country, year", con=cnx)
pivoted = gni_historical.pivot(columns='country', index='year', values='gni')
pivoted.reset_index(inplace=True)

ax = pivoted[['Denmark','European Union', 'High income: OECD', 'year']].plot(x='year', kind='line', title ="Denmark's GNI Over Time Comparison", figsize=(100,50),legend=True, fontsize=12)

#############################################################################
#   Analysis 8: Denmark's historical social contribuutions relative to peer groups
#############################################################################

sc_historical = sql.read_sql("select country, year, social_contr from wb_data \
    where country in ('Denmark', 'European Union', 'High income: OECD') \
    and year <= 2013 and year >= 1995 order by country, year", con=cnx)
pivoted = sc_historical.pivot(columns='country', index='year', values='social_contr')
pivoted.reset_index(inplace=True)

ax = pivoted[['Denmark','European Union', 'High income: OECD', 'year']].plot(x='year', kind='line', title ="Denmark's Social Contributions Over Time Comparison", figsize=(100,50),legend=True, fontsize=12)
