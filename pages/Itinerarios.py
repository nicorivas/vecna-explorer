import streamlit as st
from load import load_itinerarios
from tools.tools import setup_ambient, agrid_options
from st_aggrid import AgGrid
import pandas as pd
import duckdb

ARAUCO = True

setup_ambient()

st.set_page_config(layout="wide")

st.write("# Itinerarios")

#df = load_itinerarios()

@st.cache_data
def load_itinerarios():
   con = duckdb.connect('itineraries.db')
   df = con.execute("SELECT * FROM itineraries").fetchdf()

   df.loc[:,"carrier_scac"] = df.loc[:,"carrier"].apply(lambda x: x["scac"])
   df.loc[:,"carrier"] = df.loc[:,"carrier"].apply(lambda x: x["short_name"])
   df.loc[:,"pol_name"] = df.loc[:,"pol"].apply(lambda x: x["name"])
   df.loc[:,"pol"] = df.loc[:,"pol"].apply(lambda x: x["locode"])
   df.loc[:,"pod_name"] = df.loc[:,"pod"].apply(lambda x: x["name"])
   df.loc[:,"pod"] = df.loc[:,"pod"].apply(lambda x: x["locode"])
   
   # Drop alliance column
   df = df.drop(columns=["alliance","uuid_p2p","p2p_id","id"])
   
   # Transform timestamp to datetime
   df["etd"] = df["etd"].apply(lambda x: pd.to_datetime(x))
   df["eta"] = df["eta"].apply(lambda x: pd.to_datetime(x))
   df["etd_local"] = df["etd_local"].apply(lambda x: pd.to_datetime(x))
   df["eta_local"] = df["eta_local"].apply(lambda x: pd.to_datetime(x))
   
   # Transhipments
   df.loc[:,"transhipments"] = df.loc[:,"legs"].apply(lambda x: [[y["pol"]["locode"]+"-"+y["pod"]["locode"]] for y in x])
   df.loc[:,"transhipments_name"] = df.loc[:,"legs"].apply(lambda x: [[y["pol"]["name"]+"-"+y["pod"]["name"]] for y in x])
   for i in range(5):
      df["transhipments_name_"+str(i+1)] = df["legs"].apply(lambda x: x[i]["pod"]["name"] if len(x)>i+1 else None)
   df["transhipments_name_1"] = df["transhipments_name_1"].apply(lambda x: x if x is not None else "DIRECT")
   df.loc[:,"vessel"] = df.loc[:,"legs"].apply(lambda x: [y["vessel"]["shipname"] for y in x])

   # Services
   df["service"] = df.apply(lambda y: [x["service_name"] for x in y["legs"]], axis=1)

   # Drop legs column
   df = df.drop(columns=["legs"])

   # Remove timezone of all datetime columns in df
   df["etd"] = df["etd"].apply(lambda x: x.replace(tzinfo=None))
   df["eta"] = df["eta"].apply(lambda x: x.replace(tzinfo=None))
   df["etd_local"] = df["etd_local"].apply(lambda x: x.replace(tzinfo=None))
   df["eta_local"] = df["eta_local"].apply(lambda x: x.replace(tzinfo=None))

   #df["a"] = df.apply(lambda x: (x["pod_name"] == x['transhipments_name_1'])|(x["pod_name"] == x['transhipments_name_2']),axis=1)

   # Leave only the following ports: Coronel – Lirquén – San Vicente – San Antonio – Valparaíso
   df = df[df["pol_name"].isin(["Coronel","Lirquén","San Vicente","Talcahuano","Talcahuano (San Vicente)","San Antonio","Valparaiso"])].copy()
   df = df[df["carrier_scac"].isin(["CMDU","COSU","EGLV","EVRG","HLCU","SUDU","MSCU","MAEU","ONEY","ZIMU"])].copy()

   return df

df = load_itinerarios()

def convert_df_to_csv(df):

   cols_in = [
      "carrier",
      "pol",
      "pol_name",
      "pod",
      "pod_name",
      "eta",
      "etd",
      "transshipment_count",
      "transit_time",
      "transhipments_name_1",
      "transhipments_name_2",
      "transhipments_name_3",
      "transhipments_name_4",
      "vessel",
      "service"
   ]

   df = df[cols_in]
   print(df.shape)

   return df.to_csv(index=False).encode('utf-8')

#def convert_df_to_excel(df):
#   from io import BytesIO
#   from pyxlsb import open_workbook as open_xlsb
#   import streamlit as st
#   output = BytesIO()
#   writer = pd.ExcelWriter(output, engine='xlsxwriter')
#   df.to_excel(writer, index=False, sheet_name='Sheet1')
#   workbook = writer.book
#   worksheet = writer.sheets['Sheet1']
#   format1 = workbook.add_format({'num_format': '0.00'}) 
#   worksheet.set_column('A:A', None, format1)  
#   writer.save()
#   processed_data = output.getvalue()
#   return processed_data

csv = convert_df_to_csv(df)
#xlsx = convert_df_to_excel(df)

_, col1, col2 = st.columns([2,1,1])

with col1:
   st.download_button(
      label="Descargar en CSV",
      data=csv,
      file_name="itinerarios.csv",
      mime="text/csv",
      key='download-csv'
      )

#with col2:
#   st.download_button(
#      label='Descargar en Excel',
#      data=xlsx ,
#      file_name='itinerarios.xlsx'
#      )

columns = [
   'carrier'
   ,'pol'
   ,'pol_name'
   ,'pod'
   ,'pod_name'
   ,'eta'
   ,'etd'
   ,'transshipment_count'
   ,'transit_time'
   #,'cyclosing'
   ,'transhipments_name_1'
   ,'transhipments_name_2'
   ,'transhipments_name_3'
   ,'transhipments_name_4'
   ,'vessel'
   ,'service'
   ]

AgGrid(df[columns], agrid_options(df[columns], 20))