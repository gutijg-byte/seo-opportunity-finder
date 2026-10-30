# SEO Opportunity Finder

**Convierte una exportación de consultas de Search Console en una lista priorizada de hipótesis SEO.**

Herramienta de línea de comandos en Python, sin dependencias externas ni claves API. Procesa los archivos localmente y no realiza conexiones de red.

## Ejemplo en un minuto

Requiere Python 3.10 o posterior. Desde esta carpeta:

```bash
python seo_opportunities.py examples/queries.csv --output reports/demo.csv
```

En macOS/Linux puede ser necesario usar `python3`.

La demostración usa datos completamente ficticios. Devuelve cuatro consultas:

| Consulta | CTR actual | Posición media | Brecha de clics del escenario |
|---|---:|---:|---:|
| auditoria seo tecnica | 1,20 % | 8,4 | 95 |
| python para seo | 0,56 % | 11,2 | 80 |
| monitorizar canonical | 0,25 % | 9,8 | 38 |
| consultor geo | 2,81 % | 6,5 | 35 |

## Usar tus datos

Exporta la tabla de **Consultas** del informe de rendimiento de Search Console como CSV. Si recibes un ZIP, extrae el CSV de consultas. No uses el archivo de páginas, fechas o comparaciones entre periodos.

```bash
python seo_opportunities.py data/consultas.csv --output reports/revision.csv --min-impressions 200 --min-position 4 --max-position 15 --target-ctr 0.04 --exclude "tu marca" --exclude "otra variante"
```

- Entrada: UTF-8, con o sin BOM; separador coma, punto y coma o tabulación.
- Columnas obligatorias: `query`, `clicks`, `impressions`, `position`. También admite `Top queries` / `Consultas principales`, `Clics`, `Impresiones` y `Posición`.
- Recuentos: enteros sin separadores de miles. Posición: decimal con punto o coma (si usas coma y delimitador coma, encierra el valor entre comillas).
- Una fila por consulta. Se rechazan duplicados para evitar combinar periodos o dimensiones accidentalmente.
- El CTR se recalcula como clics / impresiones; la columna CTR de entrada se ignora.
- `--exclude` elimina coincidencias parciales sin distinguir mayúsculas ni tildes.
- El archivo de salida debe ser nuevo: no se sobrescriben informes existentes.
- En la salida, `ctr` y `scenario_target_ctr` son fracciones: `0.05` significa 5 %.

## Metodología: una hipótesis, no una predicción

Por defecto se seleccionan consultas con al menos 100 impresiones, posición media entre 4 y 20 y CTR inferior al escenario del 5 %.

```text
scenario_click_gap = impressions × target_ctr − clicks
```

Solo se muestran brechas positivas, ordenadas de mayor a menor. La fórmula supone impresiones constantes y alcanzar el CTR elegido; el resultado expresa clics adicionales hipotéticos durante el mismo periodo exportado. El 5 % es un parámetro de demostración, no un benchmark de Google ni una curva universal por posición. Ajusta el escenario al segmento estudiado y compara distintas hipótesis.

Antes de actuar, revisa la intención de búsqueda, la página asociada, el dispositivo, el país, la marca y el aspecto real de la SERP. Una posición media no equivale a una posición fija. El CSV por consultas no permite identificar por sí solo la URL que debes optimizar.

La herramienta no estima conversiones, ingresos, causalidad ni visibilidad GEO. Tampoco recupera consultas ausentes del archivo exportado. Un ranking de brechas no sustituye una evaluación del valor comercial.

## Calidad y privacidad

```bash
python -m unittest discover -s tests -v
```

Las pruebas cubren cálculo y ordenación, exclusiones, idiomas, datos inválidos, duplicados y protección frente a sobrescritura. Las consultas que podrían interpretarse como fórmulas al abrir el resultado en una hoja de cálculo reciben un apóstrofo inicial.

Guarda exportaciones reales en `data/` y resultados en `reports/`; ambas carpetas se excluyen de Git. No publiques información de clientes. Los archivos de `examples/` son sintéticos y sí se versionan.

## Estructura

- `seo_opportunities.py`: lectura, validación, ranking y CLI.
- `tests/`: pruebas con la biblioteca estándar.
- `examples/`: entrada ficticia y salida esperada.

## Próximos pasos posibles

- Comparar periodos con validación de fechas y dimensiones.
- Incorporar objetivos de CTR por segmentos definidos por el usuario.
- Exportar un informe HTML con explicación de cada oportunidad.

Estas mejoras todavía no están implementadas. Para proponer cambios, abre una issue con un caso reproducible y datos ficticios.

## Referencia

[Documentación del informe de rendimiento de Search Console](https://support.google.com/webmasters/answer/7576553?hl=es).

## Autoría y licencia

Preparado para Juan · `gutijg-byte`, con asistencia de IA en la implementación inicial. Licencia MIT: permite reutilización y uso comercial manteniendo el aviso de licencia. No implica respaldo de Google.
