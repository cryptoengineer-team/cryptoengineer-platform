# CryptoEngineer Data and Model Platform
## Automatización de predicción del comportamiento de Criptomonedas
### Proyecto TFM: Master en Data Science y Master en Data Engineering and Big Data

## Libreria CryptoEngineerSDK
Se ha desarrollado una librería instalable de Python. Esta librería facilita el acceso a los datos por parte de los Data Scientist y proporciona información de los datos disponibles en el Data Lake. 
 
La librería controla el acceso a los datos, autenticando a los usuarios a través de usuario y token personalizados. Además, nunca se obtiene acceso directo al Data Lake, ya que se generan urls para descarga de los datos que son válidas por unos minutos, donde se descargan los datos y se cargan en un dataframe para su posterior uso por parte de Data Scientist. La autenticación está separada en una función, api y lambda por evitar consumo de tiempo de la lambda de lectura datos al estar limitada en tiempos. 

## Diseño y funcionamiento de la librería 
 
La librería está compuesta de dos funciones principales, para leer los datos y para obtener información de qué datos están disponibles. Estas se apoyan en funciones como la de autenticación, validación de parámetros, lectura de ficheros Parquet a través de descargas de las urls y obtención de campos partición de ficheros Parquet descargados. Se apoya en servicios de AWS.

Esto interactúa a través de API Gateway de AWS que a su vez se apoya en funciones Lambda para consultar la información necesaria a través del Catálogo de Datos de Glue que se encuentran almacenadas en nuestro S3

### Funciones

- Función GET_INFO: devuelve la información de los Symbols y toda la metadata de los mismos necesaria para su explotación por parte de los Data Scientist.

- Función READER: La función reader va a permitir obtener los datos de los Symbols que necesitemos para entrenar nuestro algoritmo. En esta función se debe pasar el usuario y token en un diccionario, y se le indicará el symbol y el año inicial y final a descargar. Devolverá un Pandas dataframe con los datos solicitados.


## Content
A continuación se detalla el contenido de este repositorio en sus diferentes carpetas con objeto de facilitar la navegación:

- **lambda_list_info**: contiene el código Python de la función Lambda que se invoca al emplear el método list_info.

- **lambda_token**: contiene el código Python de la función Lambda que se invoca para autenticar al usuario peticionario.

- **lambda_read**: contiene el código Python de la función Lambda que se invoca al emplear el método reader.

- **lambda_deploy_model**: contiene el código Python de la función Lambda que se invoca para solicitar el despliegue y publicación del modelo de usuario para inferencia on-line. Esta funcionalidad esta limitada y en versión beta.

- **lambda_shutdown_model**: contiene el código Python de la función Lambda que se invoca para solicitar la eliminación del modelo desplegado por el usuario. Esta funcionalidad está en versión beta.

- **deploy_utils**: contiene diferentes scripts en código Python para realizar tests de los despliegues de modelos.

- **cryptoengineersdk.py**: contiene el codigo de la librería.

## Autores
	- Eduardo Muñoz Sala		    Máster Data Engineer
	- Julian Luis García Pérez		Máster Data Engineer
	- David Martín Hernández		    Máster Data Engineer
	- Héctor Jesús Ibañez Dura		Máster Data Science
	- Eugenio Chinea García		    Máster Data Science
	- Carlos Altuzarra García		    Máster Data Science

## Contributing
If you find some bug or typo, please let me know or fixit and push it to be analyzed. 

## License

Copyright 2024 

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.




