# Importamos las librerías
import pandas as pd
import numpy as np
import sklearn
from fastapi import FastAPI
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neighbors import NearestNeighbors

# Indicamos título y descripción de la API
app = FastAPI(title='Proyecto Individual -Machine Learning Operations (MLOps) -Jorge Emiliano',
              description='API de datos y recomendaciones de películas')

# Datasets
df = pd.read_csv('/Volumes/Jorge HD/movies/ETL/movies_final.csv')
df = pd.read_csv('/Volumes/Jorge HD/movies/movies_ml.csv')

# Función para reconocer el servidor local

@app.get('/')
async def index():
    return {'Hola! Bienvenido a la API de recomendacion. Por favor dirigite a /docs'}

@app.get('/about/')
async def about():
    return {'Proyecto Individual -Machine Learning Operations (MLOps)'}

# Función de películas por mes

@app.get('/peliculas_mes/({mes})')
def peliculas_mes(mes:str):
    ''' Se ingresa el mes y lafunción retorna la cantidad de películas que se estrenaron ese mes
    (nombre del mes, en str, ejemplo: 'enero') historicamente.
    '''
    mes = mes.lower()
    meses = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12}

    mes_numero = meses[mes]

    # Convertir la columna 'fecha' a un objeto de tipo fecha
    df['release_date'] = pd.to_datetime(df['release_date'])

    # Tratamos la excepción 
    try:
        month_filtered = df[df['release_date'].dt.month == mes_numero]
    except (ValueError, KeyError, TypeError):
        return None
    
    # Filtramos valores duplicados del dataframe y calculamos 
    month_unique = month_filtered.drop_duplicates(subset='id')
    respuesta = month_unique.shape[0]

    return{'mes': mes, 'cantidad': respuesta}

# Función de películas por día

@app.get('/peliculas_dia/({dia})')
def peliculas_dia(dia:str):
    '''Se ingresa el dia y la función retorna la cantidad de peliculas que se 
    estrenaron ese dia (de la semana, en str, ejemplo 'lunes') históricamente
    '''
    # Creamos diccionario para normalizar
    days = {
        'lunes': 'Monday',
    'martes': 'Tuesday',
    'miercoles': 'Wednesday',
    'jueves': 'Thursday',
    'viernes': 'Friday',
    'sabado': 'Saturday',
    'domingo': 'Sunday'}

    day = days[dia.lower()]

    # Filtramos los duplicados del dataframe y calculamos
    lista_peliculas_day = df[df['release_date'].dt.day_name() == day].drop_duplicates(subset='id')
    respuesta = lista_peliculas_day.shape[0]

    return {'dia': dia, 'cantidad': respuesta}

# Función de métricas por franquicia

@app.get('/franquicia/({franquicia})')
def franquicia(franquicia:str):
    '''Se ingresa la franquicia, retornando la cantidad de peliculas, ganancia total y promedio
    '''
    # Filtramos el dataframe
    lista_peliculas_franquicia = df[(df['collection'] == franquicia)].drop_duplicates(subset='id')

    # Calculamos
    cantidad_peliculas_franq = (lista_peliculas_franquicia).shape[0]
    revenue_franq = lista_peliculas_franquicia['revenue'].sum()
    promedio_franq = revenue_franq/cantidad_peliculas_franq

    return {'franquicia':franquicia, 'cantidad':cantidad_peliculas_franq, 'ganancia_total':revenue_franq, 'ganancia_promedio':promedio_franq}

# Función peliculas por pais

@app.get('/peliculas_pais/({pais})')
def peliculas_pais(pais:str):
    '''Ingresas el pais, retornando la cantidad de películas producidas en el mismo.
    '''
    # Filtramos el dataframe y contamos filas
    movies_filtered = df[(df['country'] == pais)]
    movies_unique = movies_filtered.drop_duplicates(subset='id')
    respuesta = movies_unique.shape[0]

    return {'pais':pais, 'cantidad': respuesta}

# Función métricas por productora

@app.get('/productoras/({productora})')
def productoras(productora:str):
    '''Ingresas la productora, retornando la ganancia total y la cantidad de peliculas que produjeron.
    '''
    # Filtramos el dataframe
    lita_peliculas_productoras = df[(df['company'] == productora)].drop_duplicates(subset='id')

    # Calculamos 
    cantidad_peliculas_prod = (lita_peliculas_productoras).shape[0]
    revenue_prod = lita_peliculas_productoras['revenue'].sum()

    return {'productora': productora, 'ganancia_total': revenue_prod, 'cantidad': cantidad_peliculas_prod}

# Función métricas por peliculas

@app.get('/retorno/({pelicula})')
def retorno(pelicula):
    '''Ingresas la película, retornando la inversión, la ganancia, el retorno y el año en el que lanzó
    '''
    # Filtramos el dataframe y Calculamos
    info_pelicula = df[(df['title'] == pelicula)].drop_duplicates(subset='title')
    pelicula_nombre = info_pelicula['title'].iloc[0]
    inversion_pelicula =  str(info_pelicula['budget'].iloc[0])
    ganancia_pelicula = str(info_pelicula['revenue'].iloc[0])
    retorno_pelicula = str(info_pelicula['return'].iloc[0])
    year_pelicula = str(info_pelicula['release_year'].iloc[0])

    return {'pelicula':pelicula_nombre, 'inversion':inversion_pelicula, 'ganacia':ganancia_pelicula,'retorno':retorno_pelicula, 'anio':year_pelicula}


# Función de recomendación

# Aseguramos que los datos de la columna 'overview' sean strings
df['overview'] = df['overview'].fillna('').astype('str')

# Aseguramos que los datos de la columna 'genres' sean strings
df['genres'] = df['genres'].apply(lambda x: ' '.join(map(str, x)) if isinstance(x, list) else '')

# Reemplazamos los valores NaN con cadenas vacías en la columna 'production_companies'
df['production_companies'] = df['production_companies'].fillna('')

# Convertimos la columna 'production_companies' a string si es necesario
df['production_companies'] = df['production_companies'].apply(lambda x: ' '.join(map(str, x)) if isinstance(x, list) else x)

# Creamos una nueva columna combinando las características de interés
df['combined_features'] = df['overview'] + ' ' + df['genres'] + ' ' + df['production_companies']

# Convertimos todos los textos a minusculas para evitar duplicados
df['combined_features'] = df['combined_features'].str.lower()

#  Creamos una matriz de conteo usando CountVectorizer que convierte los textos en una matriz de frecuencias de palabras
cv = CountVectorizer(stop_words='english', max_features=5000)
count_matrix = cv.fit_transform(df['combined_features'])

# Creamos un modelo para encontrar los vecinos mas cercanos en un espacio de caracteristicas
nn = NearestNeighbors(metric='cosine', algorithm='brute')
nn.fit(count_matrix)

# Creamos un indice de titulos de peliculas y eliminamos los duplicados
indices = pd.Series(df.index, index=df['title']).drop_duplicates()


@app.get("/recomendacion/{titulo}")
def recomendacion(titulo: str):
    '''Ingresas un nombre de película y te recomienda 5 similares
    '''
    # Verificamos si el titulo ingresado se encuentra en el df
    if titulo not in df['title'].values:
        return 'La pelicula no se encuentra en el conjunto de la base de datos.'
    else:
        # Obtenemos el índice de la película que coincide con el título
        index = indices[titulo]

        # Obtenemos las puntuaciones de similitud de las 5 peliculas más cercanas
        distances, indices_knn = nn.kneighbors(count_matrix[index], n_neighbors=6)  

        # Obtenemos los indices de las peliculas
        movie_indices = indices_knn[0][1:]  

        # Devolvemos las 5 peliculas mas similares
        return {'lista recomendada': df['title'].iloc[movie_indices].tolist()}