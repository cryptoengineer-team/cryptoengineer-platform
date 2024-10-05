# CryptoEngineer Data and Model Platform
## Automatización de predicción del comportamiento de Criptomonedas
### Proyecto TFM: Master en Data Science y Master en Data Engineering and Big Data

## Libreria CryptoEngineerSDK
Se ha desarrollado una librería instalable de Python. Esta librería facilita el acceso a los datos por parte de los Data Scientist y proporciona información de los datos disponibles en el Data Lake. 
 
La librería controla el acceso a los datos, autenticando a los usuarios a través de usuario y token personalizados. Además, nunca se obtiene acceso directo al Data Lake, ya que se generan urls para descarga de los datos que son válidas por unos minutos, donde se descargan los datos y se cargan en un dataframe para su posterior uso por parte de Data Scientist. La autenticación está separada en una función, api y lambda por evitar consumo de tiempo de la lambda de lectura datos al estar limitada en tiempos. 

## Content
A continuación se detalla el contenido de este repositorio en sus diferentes carpetas con objeto de facilitar la navegación:

- **InvestingScraperLoad**: contiene el código Python empleado para scrapear los indices de la plataforma Investing.

- **KrakenApiOHLC**: contiene el código Python empleado en el Job de carga de Criptomonedas que realiza llamadas al API "OHLC" de Kraken, se emplea para mantener actualizada la información de criptomonedas.

- **KrakenApiTrades**: contiene el código Python empleado en el Job de carga de Criptomonedas que realiza llamadas al API "Trades" de Kraken, se emplea para cerrar el gap existente desde la carga inicial mediante CSV hasta el día actual.

- **Limpieza de registros en Silver**: contiene el codigo empleado para limpiar duplicados puntualmente detectados en el datalake de criptomonedas.

- **load**: POR COMENTAR!!.

- **storage**: POR COMENTAR!!.

## Autores
	- Eduardo Muñoz Sala		    Máster Data Engineer
	- Julian Luis García Pérez		Máster Data Engineer
	- David Martín Hernández		    Máster Data Engineer
	- Héctor Jesús Ibañez Dura		Máster Data Science
	- Eugenio Chinea García		    Máster Data Science
	- Carlos Atuzarra García		    Máster Data Science

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




