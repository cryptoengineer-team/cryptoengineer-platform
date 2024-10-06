# CryptoEngineer Data and Model Platform
### Automatización de predicción del comportamiento de Criptomonedas
![](images/portada_criptoengineer.png)
### Proyecto TFM: Master en Data Science y Master en Data Engineering and Big Data

## Problem Description
Este proyecto busca democratizar el acceso a las estrategias de trading algorítmicas, permitiendo a los desarrolladores monetizar sus algoritmos y a los traders beneficiarse de herramientas avanzadas que optimizan sus operaciones. El MVP que se ha desarrollado refleja los primeros pasos hacia la creación de una plataforma integral que combine el almacenamiento de grandes volúmenes de datos, la evaluación de algoritmos y la visualización de resultados.

### Problem Statement

El desarrollo del proyecto ha sido diseñado para abordar tres componentes clave que proporcionan la base necesaria para expandir la plataforma en el futuro:
- Un datalake creado para almacenar y gestionar grandes volúmenes de datos históricos en modo “batch” relacionados con criptomonedas. Estos datos incluyen precios, volúmenes de transacción y otros indicadores importantes del mercado. El datalake está alojado en la nubep pública de Amazon (AWS), utilizando servicios como Amazon S3 o Amazon Glue, lo que garantiza su escalabilidad y seguridad. Los desarrolladores de algoritmos pueden acceder a estos datos para realizar análisis y diseñar e implementar sus estrategias.

- Una librería desarrollada en Python que permite a los desarrolladores acceder y manipular fácilmente los datos almacenados en el datalake, previa autentificación del usuario. Esta librería incluye funciones predefinidas que optimizan la extracción y el procesamiento de datos, permitiendo a los desarrolladores centrarse en la creación de algoritmos en lugar de en la gestión de datos. Esto reduce significativamente el tiempo necesario para desarrollar y probar estrategias de trading algorítmico.

- Una interfaz gráfica sencilla pero funcional que permite a los desarrolladores cargar y evaluar sus algoritmos en la plataforma. Los algoritmos son evaluados automáticamente utilizando los datos del datalake, y los resultados se visualizan directamente en la interfaz. Este sistema de retroalimentación ayuda a los desarrolladores a ajustar y mejorar sus algoritmos antes de lanzarlos al marketplace. La interfaz está diseñada para ser intuitiva y accesible, facilitando el uso a desarrolladores.

## Content
A continuación se detalla el contenido de este repositorio en sus diferentes carpetas con objeto de facilitar la navegación:

- **data-platform**: contiene los notebooks y scripts para los trabajos de AWS Glue que alimentan al repositorio de datos, el data lake de la plataforma. Se definen trabajos de ingesta de datos a la capa bronce, de transformación en la capa silver y gold.

- **app-platform**: contiene el codigo de la aplicación principal en Streamlit así como de las diferentes funciones AWS Lambda que le dan servicios y funcionalidades.

- **sdk**: contiene el código fuente de la libreria que los usuarios analistas pueden usar para acceder al catalogo de datos y realizar las descargas de los datos necesarios para analizar y diseñar sus estrategias de inversión.

- **terraform**: es una sección aún en progreso y opcional que se irá completando en siguientes versiones. Almacena las definiciones para el despliegue de partes de la solución usando Terraform.

## Autores
Este proyecto ha sido realizado por las siguientes personas:

	- Eduardo Muñoz Sala		            Máster Data Engineer
	- Julian Luis García Pérez		    Máster Data Engineer
	- David Martín Hernández		    Máster Data Engineer
	- Héctor Jesús Ibañez Dura		    Máster Data Science
	- Eugenio Chinea García		            Máster Data Science
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




