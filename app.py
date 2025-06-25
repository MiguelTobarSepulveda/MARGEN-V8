import streamlit as st
import pandas as pd
import requests          # <---- ¡Agrega esta línea!
from io import BytesIO


# Diccionario de usuarios y contraseñas permitidas
USUARIOS = {
    "miguel": "1234",
    "jsmith": "abc123"
}

# Estado de sesión para recordar si el usuario ya se logueó
if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

def login():
    st.title("Login")
    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if usuario in USUARIOS and clave == USUARIOS[usuario]:
            st.session_state["logueado"] = True
            st.session_state["usuario"] = usuario
            st.success(f"¡Bienvenido, {usuario}!")
            st.rerun()

        else:
            st.error("Usuario o contraseña incorrectos")

if not st.session_state["logueado"]:
    login()
    st.stop()
else:
    st.sidebar.success(f"Sesión iniciada como {st.session_state['usuario']}")
    # A partir de aquí va el resto de tu app normal


    # --------- CARGA AUTOMÁTICA DEL ARCHIVO DESDE GOOGLE DRIVE ---------
    url_drive = 'https://drive.google.com/uc?export=download&id=1QhyIyTnKyupJ7Cg_TUMHUX0jcu-RbJuj'
    @st.cache_data(show_spinner=False)
    def cargar_excel_drive(url):
        response = requests.get(url)
        if response.status_code == 200:
            return pd.ExcelFile(BytesIO(response.content))
        else:
            st.error('No se pudo descargar el archivo de Google Drive.')
            return None

    @st.cache_data(show_spinner=False)
    def cargar_excels_drive(url):
       response = requests.get(url)
    if response.status_code == 200:
        xls = pd.ExcelFile(BytesIO(response.content))
        ventas = pd.read_excel(xls, sheet_name="LIBRO DE VENTAS")
        recetas = pd.read_excel(xls, sheet_name="RECETAS DE PRODUCTOS")
        precios = pd.read_excel(xls, sheet_name="PRECIO DE INSUMOS")
        return ventas, recetas, precios
    else:
        st.error('No se pudo descargar el archivo de Google Drive.')
        return None, None, None

ventas, recetas, precios = cargar_excels_drive(url_drive)
if ventas is not None:
    st.success("Archivo cargado correctamente.")

        
# -------- FILTROS DE CONSULTA --------
cliente_sel = st.sidebar.selectbox("Cliente", ["Todos"] + sorted(ventas["CLIENTE"].unique().tolist()))
producto_sel = st.sidebar.selectbox("Producto", ["Todos"] + sorted(ventas["NOMBRE DE PRODUCTO"].unique().tolist()))
mes_sel = st.sidebar.selectbox("Mes", ["Todos"] + sorted(pd.to_datetime(ventas["FECHA"]).dt.strftime('%Y-%m').unique()))

# -------- APLICAR FILTROS --------
data = ventas.copy()
if cliente_sel != "Todos":
    data = data[data["CLIENTE"] == cliente_sel]
if producto_sel != "Todos":
    data = data[data["NOMBRE DE PRODUCTO"] == producto_sel]
if mes_sel != "Todos":
    data = data[pd.to_datetime(data["FECHA"]).dt.strftime('%Y-%m') == mes_sel]

# -------- RESULTADOS FILTRADOS --------
st.write("Resultados filtrados:")
st.dataframe(data)
st.info("Pronto podrás ver márgenes y más detalles. ¿Qué filtro te gustaría agregar?")


 else:
    st.error("No se pudo cargar el archivo.")
