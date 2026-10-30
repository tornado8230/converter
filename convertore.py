import requests
import streamlit as st

#p=str(input("введите валюту :"))
url="https://cbr-xml-daily.ru/daily_json.js"
 
@st.cache_data(ttl=3600)
def zapr():
    # запрос и получэние полной информации с сайта
    zapros=requests.get(url,timeout=15)
    #print(zapros.status_code)
    zapros.raise_for_status()
    return zapros.json()

def convert(valuta,amount):
    # персчет на рубли с учетом намина    
    t=valuta["Value"]/valuta["Nominal"]
    return t*amount

def main():
    st.set_page_config(page_title="конвертер валют",layout="centered")
    st.title("конвертер валют")
    st.write("выберети валюту и узнайте ее стоймость в рублях")
    st.caption(f"источник: {url}")
    
    data=zapr()
    valuts=data["Valute"]
    
    #print("дата курса:",data["Date"][:10] )
    #print("примеры валют: USD,EUR,BHD,BOB")
    
    date=data["Date"][:10]
    st.caption(f"дата курса: {date}")
    
    codes=sorted(valuts)
    default_i=codes.index("USD")
    
    with st.form("converter"):
        code=st.selectbox("валюта",codes,index=default_i)
        amount=st.number_input(
            "сумма выбранной валюты",
            min_value=0.0,
            value=100.0,
            step=1.0,
            format="%.2f"
        )
        baton=st.form_submit_button("перевести в рубли")
        
    if baton:
        valuta=valuts[code]
        rub=convert(valuta,amount)
        
        #print("")
        #print("валюта :",valuta["Name"])
        #print("наминал :",valuta["Nominal"])
        #print(f"{amount:.2f} {code} = {rub:.2f} rub") 
        name=valuta["Name"]
        st.subheader(name)
        st.metric(f"{amount:.2f} {code} в рублях", f" {rub:.2f} rub")
        #python -m streamlit run C:\Users\PC\Desktop\python\untitled108.py

if __name__=="__main__":
    main()
