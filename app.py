import streamlit as st
from PIL import Image
import google.generativeai as genai
import mysql.connector
from datetime import datetime
import pandas as pd
from io import BytesIO
import os



# =========================
# CONFIGURACION PAGINA
# =========================

st.set_page_config(
    page_title="Evaluación Ergonómica IA",
    page_icon="🧍",
    layout="centered"
)

# =========================
# CONEXION MYSQL
# =========================

conexion = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)

cursor = conexion.cursor()

# =========================
# API GEMINI
# =========================

#genai.configure(
#    api_key=os.getenv("GEMINI_API_KEY")
#)

genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel(
    "models/gemini-2.5-flash"
)

st.title("Evaluación Ergonómica con IA")
st.caption("Seguridad y Salud en el Trabajo")

st.divider()

# =========================
# DATOS PERSONALES
# =========================

st.subheader("Datos del trabajador")

nombre = st.text_input("Nombres completos")

dni = st.text_input("DNI")

edad = st.number_input(
    "Edad",
    18,
    100
)

sexo = st.selectbox(
    "Sexo",
    ["Masculino", "Femenino"]
)

ocupacion = st.selectbox(
    "Tipo de ocupación",
    ["Asistencial", "Administrativo"]
)

# =========================
# CUESTIONARIO
# =========================

st.subheader("Cuestionario Ergonómico")

escala = [1,2,3,4,5]

st.caption("1 = Nunca | 5 = Muy frecuente")

cuello = st.select_slider(
    "Dolor de cuello",
    options=escala,
    value=1
)

espalda = st.select_slider(
    "Dolor de espalda",
    options=escala,
    value=1
)

lumbar = st.select_slider(
    "Dolor lumbar",
    options=escala,
    value=1
)

hombros = st.select_slider(
    "Dolor de hombros",
    options=escala,
    value=1
)

afecto = st.radio(
    "¿El dolor afectó su trabajo?",
    ["Sí", "No"]
)

falta = st.radio(
    "¿Ha faltado al trabajo por dolor?",
    ["Sí", "No"]
)

horas_sentado = st.radio(
    "¿Permanece más de 2 horas sentado?",
    ["Sí", "No"]
)

horas_pc = st.radio(
    "¿Usa computadora más de 4 horas?",
    ["Sí", "No"]
)

st.divider()

# =========================
# FOTO
# =========================

st.subheader("Fotografía")

uploaded_file = st.file_uploader(
    "Suba una fotografía de su postura",
    type=["jpg", "jpeg", "png"]
)

# =========================
# ANALISIS
# =========================

if uploaded_file is not None:

    image = Image.open(uploaded_file)

    st.image(
        image,
        caption="Imagen subida",
        use_container_width=True
    )

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        analizar = st.button(
            "🔍 Analizar postura",
            use_container_width=True
        )

    if analizar:

        # VALIDAR CAMPOS

        if nombre == "" or dni == "":
            st.error("Complete nombres y DNI")
            st.stop()

        with st.spinner("Analizando postura..."):

            prompt = f"""
            Analiza la postura ergonómica de la persona.

            DATOS:
            Nombre: {nombre}
            Edad: {edad}
            Sexo: {sexo}
            Ocupación: {ocupacion}

            CUESTIONARIO:
            Dolor cuello: {cuello}/5
            Dolor espalda: {espalda}/5
            Dolor lumbar: {lumbar}/5
            Dolor hombros: {hombros}/5

            Afectó trabajo: {afecto}
            Faltas laborales: {falta}

            Más de 2 horas sentado: {horas_sentado}
            Más de 4 horas computadora: {horas_pc}

            Evalúa:
            - cuello
            - espalda
            - hombros
            - postura sentado

            Devuelve:
            1. Nivel de riesgo ergonómico (BAJO, MEDIO o ALTO)
            2. Evaluación breve
            3. Recomendaciones
            4. Pausas activas
            5. Riesgo SST general

            Responde breve y profesional pero no tan extenso.
            """

            response = model.generate_content(
                [prompt]
            )

            resultado = response.text

        # =========================
        # DETECTAR RIESGO
        # =========================

        resultado_lower = resultado.lower()

        if "alto" in resultado_lower:
            nivel_riesgo = "ALTO"

        elif "medio" in resultado_lower:
            nivel_riesgo = "MEDIO"

        else:
            nivel_riesgo = "BAJO"

        # =========================
        # GUARDAR MYSQL
        # =========================

        sql = """
        INSERT INTO evaluaciones (
            nombres,
            dni,
            edad,
            sexo,
            ocupacion,

            dolor_cuello,
            dolor_espalda,
            dolor_lumbar,
            dolor_hombros,

            afecta_trabajo,
            falta_trabajo,

            horas_sentado,
            horas_pc,

            nivel_riesgo,
            resultado,
            fecha
        )
        VALUES (
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,
            %s,%s,
            %s,%s,
            %s,%s,%s
        )
        """

        valores = (
            nombre,
            dni,
            edad,
            sexo,
            ocupacion,

            cuello,
            espalda,
            lumbar,
            hombros,

            afecto,
            falta,

            horas_sentado,
            horas_pc,

            nivel_riesgo,
            resultado,
            datetime.now()
        )

        cursor.execute(sql, valores)

        conexion.commit()

        # =========================
        # RESULTADOS
        # =========================

        st.success("✅ Evaluación completada")

        st.subheader("Resultado")

        if nivel_riesgo == "ALTO":
            st.error(f"Riesgo ergonómico: {nivel_riesgo}")

        elif nivel_riesgo == "MEDIO":
            st.warning(f"Riesgo ergonómico: {nivel_riesgo}")

        else:
            st.success(f"Riesgo ergonómico: {nivel_riesgo}")

        st.write(resultado)

        st.warning(
            "Este resultado es referencial y no reemplaza evaluación médica u ocupacional."
        )
# =========================
# BUSQUEDA E HISTORIAL
# =========================

st.divider()

st.subheader("🔎 Búsqueda y Seguimiento")

buscar = st.text_input(
    "Buscar por DNI o nombres"
)

col1, col2 = st.columns(2)

with col1:
    btn_buscar = st.button(
        "Buscar Evaluaciones",
        use_container_width=True
    )

with col2:
    btn_todos = st.button(
        "Ver Últimos Registros",
        use_container_width=True
    )

# =========================
# BUSQUEDA
# =========================

if btn_buscar:

    sql = """
    SELECT
        id,
        nombres,
        dni,
        edad,
        sexo,
        ocupacion,
        nivel_riesgo,
        fecha
    FROM evaluaciones
    WHERE
        dni LIKE %s
        OR nombres LIKE %s
    ORDER BY id DESC
    """

    valor = f"%{buscar}%"

    cursor.execute(sql, (valor, valor))

    registros = cursor.fetchall()

    if len(registros) > 0:

        columnas = [
            "ID",
            "Nombres",
            "DNI",
            "Edad",
            "Sexo",
            "Ocupación",
            "Riesgo",
            "Fecha"
        ]

        df = pd.DataFrame(
            registros,
            columns=columnas
        )

        st.success(
            f"Se encontraron {len(df)} registros"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        # =========================
        # EXCEL
        # =========================

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Evaluaciones"
            )

        excel_data = output.getvalue()

        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name="evaluaciones_ergonomicas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:

        st.warning(
            "No se encontraron registros"
        )

# =========================
# ULTIMOS REGISTROS
# =========================

if btn_todos:

    cursor.execute("""
        SELECT
            id,
            nombres,
            dni,
            edad,
            sexo,
            ocupacion,
            nivel_riesgo,
            fecha
        FROM evaluaciones
        ORDER BY id DESC
        LIMIT 50
    """)

    registros = cursor.fetchall()

    columnas = [
        "ID",
        "Nombres",
        "DNI",
        "Edad",
        "Sexo",
        "Ocupación",
        "Riesgo",
        "Fecha"
    ]

    df = pd.DataFrame(
        registros,
        columns=columnas
    )

    st.dataframe(
        df,
        use_container_width=True
    )

    # =========================
    # EXCEL
    # =========================

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Historial"
        )

    excel_data = output.getvalue()

    st.download_button(
        label="📥 Descargar Historial Excel",
        data=excel_data,
        file_name="historial_ergonomia.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )