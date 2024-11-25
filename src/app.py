import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Configuración del user-agent y URL
url = "https://ycharts.com/companies/TSLA/revenues"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}
response = requests.get(url, headers=headers)

# Parsear el contenido HTML
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Buscar todas las tablas
    table = soup.find("table")  # Suponemos que la tabla principal tiene el tag <table>
    
    if table:
        rows = table.find_all("tr")  # Buscar todas las filas dentro de la tabla
        data = []

        # Extraer datos de las filas
        for row in rows[1:]:  # Saltamos la cabecera IMPORTANTE
            cols = row.find_all("td")
            if len(cols) == 2:
                date = cols[0].get_text(strip=True)
                revenue = cols[1].get_text(strip=True)
                data.append({"Date": date, "Revenue": revenue})

        # Crear DataFrame
        tesla_revenue = pd.DataFrame(data)
        print(tesla_revenue)
    else:
        print("No se encontró ninguna tabla en el HTML.")
else:
    print("No se pudo acceder a la página web.")



# Limpieza de la columna Revenue
def limpia_revenue(value):
    if "B" in value:  # Billones
        return float(value.replace("B", "").replace(",", "").strip()) * 1e9
    elif "M" in value:  # Millones
        return float(value.replace("M", "").replace(",", "").strip()) * 1e6
    else:  # Otros casos (valores numéricos simples)
        return float(value.replace(",", "").strip())

# Aplicar la función a la columna Revenue
tesla_revenue["Revenue"] = tesla_revenue["Revenue"].apply(limpia_revenue)

# Convertir valores limpios a float
tesla_revenue["Revenue"] = tesla_revenue["Revenue"].astype(float)

# Continuar con SQLite
import sqlite3

# Conectar a SQLite
connection = sqlite3.connect("Tesla.db")
cursor = connection.cursor()

# Crear la tabla (si no existe)
cursor.execute("""
CREATE TABLE IF NOT EXISTS revenue (
    Date TEXT,
    Revenue REAL
)
""")

# Insertar datos en la tabla
tesla_tuples = list(tesla_revenue.to_records(index=False))  # Convierte el DataFrame en una lista de tuplas
cursor.executemany("INSERT INTO revenue (Date, Revenue) VALUES (?, ?)", tesla_tuples)

# Guardar cambios
connection.commit()

# Consultar y mostrar los datos almacenados
for row in cursor.execute("SELECT * FROM revenue"):
    print(row)

# Cerrar conexión
connection.close()





#GRAFICAR

# 1) INGRESOS TRIMESTRALES

# Conectar a SQLite y cargar los datos en un DataFrame
connection = sqlite3.connect("Tesla.db")
query = "SELECT * FROM revenue"
tesla_revenue = pd.read_sql_query(query, connection)

# Convertir la columna Date a tipo datetime y ordenarla
try:
    tesla_revenue["Date"] = pd.to_datetime(tesla_revenue["Date"], format="%B %d, %Y", errors="coerce")
except Exception as e:
    print(f"Error al convertir las fechas: {e}")

# Eliminar filas con fechas no válidas
tesla_revenue = tesla_revenue.dropna(subset=["Date"])
tesla_revenue = tesla_revenue.sort_values(by="Date")

# Crear el gráfico de series de tiempo
plt.figure(figsize=(12, 6))
plt.plot(tesla_revenue["Date"], tesla_revenue["Revenue"], marker='o', color='blue', label="Ingresos")

# Mejorar la visualización
plt.title("Evolución de los ingresos trimestrales de Tesla", fontsize=16)
plt.xlabel("Fecha", fontsize=14)
plt.ylabel("Ingresos (USD)", fontsize=14)
plt.grid(True, linestyle='--', alpha=0.6)
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.legend(fontsize=12)

plt.tight_layout()
plt.show()

connection.close()
#BENEFICIO BRUTO ANUAL

# Conectar a SQLite y cargar los datos en un DataFrame
connection = sqlite3.connect("Tesla.db")
query = "SELECT * FROM revenue"
tesla_revenue = pd.read_sql_query(query, connection)

# Convertir la columna Date a tipo datetime y ordenarla
tesla_revenue["Date"] = pd.to_datetime(tesla_revenue["Date"], format="%B %d, %Y", errors="coerce")
tesla_revenue = tesla_revenue.dropna(subset=["Date"])
tesla_revenue = tesla_revenue.sort_values(by="Date")

# Calcular los ingresos anuales (sumando trimestrales)
tesla_revenue["Year"] = tesla_revenue["Date"].dt.year  # Extraer el año
annual_revenue = tesla_revenue.groupby("Year")["Revenue"].sum().reset_index()  # Agrupar por año y sumar

# Crear el gráfico del beneficio bruto anual
plt.figure(figsize=(12, 6))
plt.bar(annual_revenue["Year"], annual_revenue["Revenue"], color='red', edgecolor='black', label="Beneficio Bruto")

# Mejorar la visualización
plt.title("Beneficio bruto anual de Tesla", fontsize=16)
plt.xlabel("Año", fontsize=14)
plt.ylabel("Beneficio bruto (USD)", fontsize=14)
plt.xticks(annual_revenue["Year"], fontsize=10, rotation=45)
plt.yticks(fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.legend(fontsize=12)

plt.tight_layout()
plt.show()

connection.close()

# BENEFICIO BRUTO MENSUAL

# Conectar a SQLite y cargar los datos en un DataFrame
connection = sqlite3.connect("Tesla.db")
query = "SELECT * FROM revenue"
tesla_revenue = pd.read_sql_query(query, connection)

# Convertir la columna Date a tipo datetime y ordenarla
tesla_revenue["Date"] = pd.to_datetime(tesla_revenue["Date"], format="%B %d, %Y", errors="coerce")
tesla_revenue = tesla_revenue.dropna(subset=["Date"])
tesla_revenue = tesla_revenue.sort_values(by="Date")

# Calcular los ingresos mensuales
tesla_revenue["Year-Month"] = tesla_revenue["Date"].dt.to_period("M")  # Crear columna "Año-Mes"
monthly_revenue = tesla_revenue.groupby("Year-Month")["Revenue"].sum().reset_index()  # Sumar ingresos por mes
monthly_revenue["Year-Month"] = monthly_revenue["Year-Month"].astype(str)  # Convertir Period a str para graficar

# Crear el gráfico del beneficio bruto mensual
plt.figure(figsize=(14, 7))
plt.bar(
    monthly_revenue["Year-Month"],
    monthly_revenue["Revenue"],
    color='purple',  # Usar un color diferente (coral)
    edgecolor='black',
    label="Beneficio Bruto Mensual"
)
# Mejorar la visualización
plt.title("Beneficio bruto mensual de Tesla", fontsize=16)
plt.xlabel("Mes", fontsize=14)
plt.ylabel("Beneficio bruto (USD)", fontsize=14)
plt.xticks(fontsize=10, rotation=45)  # Rotar etiquetas de los meses
plt.yticks(fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.legend(fontsize=12)

# Ajustar el diseño y mostrar el gráfico
plt.tight_layout()
plt.show()

# Cerrar la conexión a la base de datos
connection.close()