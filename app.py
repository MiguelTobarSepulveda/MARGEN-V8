import streamlit as st
import pandas as pd
import requests          # <---- ¡Agrega esta línea!
from io import BytesIO

st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100vw;
        }
    </style>
""", unsafe_allow_html=True)


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

    # ----- FILTROS DINÁMICOS INTERCONECTADOS -----
    ventas['MES'] = pd.to_datetime(ventas["FECHA"]).dt.strftime('%Y-%m')
    filtro_df = ventas.copy()

    if "mes_sel" not in st.session_state:
        st.session_state["mes_sel"] = "Todos"
    if "cliente_sel" not in st.session_state:
        st.session_state["cliente_sel"] = "Todos"
    if "producto_sel" not in st.session_state:
        st.session_state["producto_sel"] = "Todos"
        
    # **AGREGA ESTA LÍNEA**
    meses_opciones = ["Todos"] + sorted(ventas["MES"].unique())
    
    # Filtro MES
    # --- FILTROS EN UNA SOLA FILA ---
    col1, col2, col3 = st.columns(3)
    with col1:
        mes_sel = st.selectbox("Mes", meses_opciones, index=meses_opciones.index(st.session_state["mes_sel"]))
    if mes_sel != "Todos":
        filtro_df = filtro_df[filtro_df["MES"] == mes_sel]

    with col2:
        cliente_opciones = ["Todos"] + sorted(filtro_df["CLIENTE"].unique())
        cliente_sel = st.selectbox("Cliente", cliente_opciones, index=cliente_opciones.index(st.session_state["cliente_sel"]))
    if cliente_sel != "Todos":
        filtro_df = filtro_df[filtro_df["CLIENTE"] == cliente_sel]

    with col3:
        producto_opciones = ["Todos"] + sorted(filtro_df["NOMBRE DE PRODUCTO"].unique())
        producto_sel = st.selectbox("Producto", producto_opciones, index=producto_opciones.index(st.session_state["producto_sel"]))
    if producto_sel != "Todos":
        filtro_df = filtro_df[filtro_df["NOMBRE DE PRODUCTO"] == producto_sel]


    # Guarda selección actual
    st.session_state["mes_sel"] = mes_sel
    st.session_state["cliente_sel"] = cliente_sel
    st.session_state["producto_sel"] = producto_sel

    # -------- RESULTADOS FILTRADOS --------
    st.write("Resultados filtrados:")
    st.dataframe(filtro_df, use_container_width=True)
    st.info("Pronto podrás ver márgenes y más detalles. ¿Qué filtro te gustaría agregar?")
   import numpy as np

    if not filtro_df.empty:
        filtro_df = filtro_df.copy()
        filtro_df['MES_VENTA'] = pd.to_datetime(filtro_df['FECHA']).dt.strftime('%Y-%m')

        def calcular_costo_unitario(row):
            cod_producto = row["CODIGO DE PRODUCTO"]
            mes_venta = row["MES_VENTA"]
            receta = recetas[recetas["CODIGO DE PRODUCTO"] == cod_producto]
            costo_unitario = 0.0
            for _, insumo in receta.iterrows():
                cod_insumo = insumo["CODIGO INSUMO"]
                cantidad_insumo = insumo["CANTIDAD DE INSUMO"]
                precios_mes = precios[
                    (precios["CODIGO INSUMO"] == cod_insumo) &
                    (pd.to_datetime(precios["FECHA"]).dt.strftime('%Y-%m') == mes_venta)
                ]
                if not precios_mes.empty:
                    precio_insumo = precios_mes.iloc[0]["PRECIO DE INSUMO"]
                    costo_unitario += cantidad_insumo * precio_insumo
            return costo_unitario

    # Calcula COSTO DEL PRODUCTO (unitario)
        filtro_df["COSTO DEL PRODUCTO"] = filtro_df.apply(calcular_costo_unitario, axis=1)
        filtro_df["MARGEN EN PESOS"] = filtro_df["NETO"] - (filtro_df["COSTO DEL PRODUCTO"] * filtro_df["CANTIDAD"])
        filtro_df["% MARGEN"] = np.where(
            filtro_df["NETO"] != 0,
            filtro_df["MARGEN EN PESOS"] / filtro_df["NETO"] * 100,
            0
        )

        st.subheader("Resultados filtrados (con costo y margen)")
        st.dataframe(
            filtro_df[
                [
                    "CLIENTE",
                    "CODIGO DE PRODUCTO",
                    "NOMBRE DE PRODUCTO",
                    "PRECIO UNITARIO",
                    "CANTIDAD",
                    "NETO",
                    "COSTO DEL PRODUCTO",
                    "MARGEN EN PESOS",
                    "% MARGEN"
                ]
            ],
            use_container_width=True
        )
    else:
        st.info("No hay datos filtrados para calcular márgenes.")


else:
    st.error("No se pudo cargar el archivo.")
