# CryptoEngineer Data and Model Platform
## Automatización de predicción del comportamiento de Criptomonedas
### Proyecto TFM: Master en Data Science y Master en Data Engineering and Big Data

## Frontal Marketplace Algoritmos

Se ha desarrollado un frontal Web para la publicación de los modelos y scripts por parte de los Data Scientist.

Se ha desarrollado con Streamlit, que es una librería de Python de código abierto que permite generar aplicaciones web.

Desde esta aplicación los usuarios van a poder publicar los modelos o scripts que hayan entrenado o desarrollado, quedando visibles para poder utilizarlo por parte de los traders. Los diferentes algoritmos serán evaluados y se mostrará su evolución en el tiempo, y también podrán ser valorados por parte de otros usuarios.

## Diseño de solución

El Marketplace se ha desarrollado en un script de Python. Para ejecutarlo se ha generado un Docker que carga el fichero y lo ejecuta, dejando disponible su acceso a los usuarios.

El Docker se ha registrado en ECR de AWS y se ha creado una Tarea y Servicio en ECS para disponibilizar públicamente la app web.

La aplicación web tendrá una página de login para acceder al resto de información. Aquí los usuarios deberán autenticarse con el usuario y token facilitados. Se validará que el usuario tiene permiso para acceder y se le redireccionará a la página de Marketplace.

Una vez logado el sitio tendrá un menú izquierdo donde podrá navegar a las dos zonas disponibles, Marketplace y Zona Personal. También tendrá en el menú izquierdo un botón para Cerrar Sesión del usuario.

## Evaluación de Modelos

En la publicación de cualquier modelo se planifica una evaluación de los modelos, que genera un job de Glue para usar el modelo y el script facilitados, y se planifica periódicamente con un Trigger de Glue.

Esta evaluación periódica genera una salida en formato CSV con los diferentes resultados y el contraste con la evolución del mercado del Symbol. Se almacena todo en S3 y se recupera cuando se muestran los modelos como información adicional para valorar la degradación o no del mismo.

## Despliegue de la aplicación

Para la puesta a disposición de los usuarios de nuestra aplicación se han analizado alternativas como AWS AppRunner que podría ser una opción preferente, aunque no está disponible en nuestro entorno AWS de desarrollo, o bien AWS Beanstalk que permite escalar aplicaciones o servicios web de manera automatizada. Finalmente, hemos optado por una solución realmente simple y suficiente para un MVP o producto demo inicial, AWS Elastic Container Service con Fargate.

AWS Fargate es un motor serverless de pago por uso que nos permite correr aplicaciones en contenedores y donde la administración de los servidores, los recursos y el escalado se traslada a AWS. Con esta solución podemos poner en marcha nuestra solución en minutos y de manera relativamente sencilla. En el caso de que quisiéramos una disponibilidad total, 24x7, de la aplicación podríamos optar por ECS sobre máquinas EC2 de pequeño tamaño que podrían ahorrarnos costes, pero inicialmente hemos priorizado la flexibilidad del modelo Fargate.

## Content
A continuación se detalla el contenido de este repositorio en sus diferentes carpetas con objeto de facilitar la navegación:

- **app**: contiene el código de la aplicación en Streamlit y su dockerización.
- **glue_jobs**: contiene el código o script para el trabajo de AWS Glue de evaluación de modelos.
- **jobeval_lambda**: contiene el código fuente de la función AWS Lambda que genera el trabajo de Glue que evluará el modelo.
- **predict-mlflow**: es una carpeta con el código para evaluar el uso de mlflow para desplegar modelos. Es una funcionalidad **no en producción**. Posible uso en próximos pasos.
- **app-mlflow**: es una carpeta con el código desplegar en contenedores la app de Streamlit y mlflow para el registro de modelos. Es una funcionalidad **no en producción**. Posible uso en próximos pasos.
- **starter_model**: contiene diferentes scripts para pruebas de modelos y el uso de mlflow. 

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




