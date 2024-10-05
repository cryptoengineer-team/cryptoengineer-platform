# CryptoEngineer Data and Model Platform
## Automatización de predicción del comportamiento de Criptomonedas
### Proyecto TFM: Master en Data Science y Master en Data Engineering and Big Data

## Plataforma de datos
Una plataforma de datos es una solución de software que permite gestionar, transformar y distribuir datos de manera eficiente, convirtiéndolos en información valiosa para la empresa. Uno de sus objetivos es unificar y consolidar información de diferentes fuentes tanto externas como internas a la empresa y así facilitar el acceso a usuarios y aplicaciones. 

Actualmente, muchas organizaciones han adoptado este tipo de soluciones para transformarlos en productos y adoptar un enfoque de “Datos como Servicio”, Daas. Así se han convertido en un software de producción, un activo crítico del negocio, que garantice la calidad y disponibilidad de los datos para su comercialización a los clientes finales

## Data Lake

Este propuesta se fundamenta en la adopción del data lake como producto de negocio. Un data lake o lago de datos es un repositorio centralizado donde se almacenan grandes volúmenes de datos, tanto estructurados como no estructurados, para su posterior procesamiento para tareas de análisis de datos, de machine learning o de análisis en tiempo real. a cualquier escala. 

Al analizar las necesidades de la solución se ha optado por un almacenamiento basado en objetos, frente a un almacenamiento de ficheros o de bloques, y en concreto por AWS Simple Storage Service o S3.

Finalmente, se ha descartado la necesidad de consolidad en un datawarehouse o almacén de datos, que están más orientados a almacenar múltiples datos estructurados y con relaciones entre las entidades

### Arquitectura Medallion

La Arquitectura Medallion, ampliamente divulgada por Databricks[2], es un modelo de tres capas para estructurar los datos en un Data Lake: bronce, plata y oro, incrementándose en cada una de ellas el nivel de refinamiento de los datos. Principalmente nos facilita la gestión eficiente de grandes volúmenes, con transformaciones graduales (más fáciles de comprender) lo que evita reprocesar siempre desde el origen y además nos permite la compresión de los datos optimizando así el almacenamiento consumido.

## Workflows y Trabajos de AWS Glue
Básicamente, AWS Glue es un servicio de ETLs totalmente administrado por AWS y de pago por uso sin necesidad de aprovisionar instancias. Y el Job es la unidad básica de la ETL. Para nuestro proyecto, un trabajo consiste en un notebook (traducido a script automáticamente por AWS) que carga datos de fuentes externas o definidas en el catálogo y realiza transformaciones sobre ellos.

Se han definido trabajos de AWS Glue:
- Trabajos de ingesta de datos por lotes
- Trabajos de ingesta de datos históricoa
- Trabajos de transformación de datos silver
- Trabajo de Transformación de datos gold

La orquestación de trabajos se refiere a la ejecución coordinada de diversas tareas y procesos dentro de un pipeline de datos y asegura que estos procesos se ejecuten de manera fluida, en el orden debido y eficientemente. Se continua confiando en AWS Glue para orquestar nuestros trabajos y diseñar nuestros procesos ELT. 

Una ELT o pipeline en AWS Glue está compuesta principalmente de los scripts y otras herramientas como las descritas a continuación:
•	Job, ya se ha comentado anteriormente. Es la unidad de trabajo y consiste en un script de carga datos y realiza transformaciones sobre ellos
•	Triggers se encargan de disparar los Jobs. Pueden ejecutarse de forma planificada, con un evento de CloudWatch o incluso un comando cron.
•	Crawler es el servicio encargado de conectarse a un almacén de datos, determinar el esquema de los datos almacenados y de generar las tablas de metadatos. 

Los workflows que se han generado son:
- Pipeline de captura de datos históricos
- Pipeline de captura de datos en modo batch
- Pipeline de captura de datos en modo Batch para Criptomonedas

## Content
A continuación se detalla el contenido de este repositorio en sus diferentes carpetas con objeto de facilitar la navegación:

- **glue_jobs**: contiene los notebooks y/o scripts en Python que se ejecutan en cada uno de los trabajos de AWS Glue para ingestar, transformar y consolidar los datos.

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




