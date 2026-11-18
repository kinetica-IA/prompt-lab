# Prompt Lab — auditor v0.4

Herramienta para revisar un prompt, conservarlo si ya sirve, pedir aclaraciones decisivas o proponer el menor cambio útil. Audita el encargo; no ejecuta su tarea.

El auditor **v0.4** está fijado por elección del usuario para su trabajo. La infraestructura de registro conserva la versión **0.2.0**. Son versiones de componentes distintos. Esta entrega no reabre la comparación con otras candidatas ni afirma superioridad general.

## Uso inmediato

Abre esta carpeta como proyecto independiente en Claude Code y empieza una conversación nueva. `CLAUDE.md` importa el auditor. Pega el prompt que quieres revisar y el contexto necesario. No hacen falta dependencias npm para este uso.

También puedes aportar `prompts/optimizer.md` como instrucción en otro entorno compatible. No presupongas que disponer del archivo implica su carga automática: comprueba cómo recibe instrucciones tu herramienta.

`docs/ENCARGO.md` es una ficha opcional para registrar el objetivo. Guarda encargos reales en `encargos/`, excluido de Git.

## Qué contiene

- Auditor v0.4 y referencia breve, copiados sin cambios.
- Contrato JSON y esquema para el banco opcional.
- Nueve casos de desarrollo: D06 se retiró; los identificadores no se renumeran.
- Registro local de respuestas, revisiones y huellas de integridad.
- Pruebas de infraestructura y generador de datos sintéticos.

No incluye encargos, documentos privados, respuestas reales, identificadores de sesión ni casos reservados. Lee `docs/ENTREGA.md` para conocer los límites.

## Comprobaciones locales

Con Python 3 y Node.js disponibles, desde la raíz:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/local.test.cjs
```

No instalan paquetes ni llaman a modelos. Se comprobaron con Python 3.13 y Node 22; no se ha ensayado una matriz de versiones.

## Banco opcional de desarrollo

La elección de v0.4 ya está cerrada. Estos comandos documentan la infraestructura para usos futuros expresamente decididos, no una nueva evaluación:

```sh
python3 scripts/pilot.py prepare --split development
python3 scripts/pilot.py verify RUTA_RUN
python3 scripts/pilot.py sessions RUTA_RUN --directory ../prompt-lab-sesiones
```

Sustituye `RUTA_RUN` por la carpeta que devuelve `prepare`. Las 18 carpetas de sesión se generan fuera del proyecto autor, con entrada y variante, sin rúbrica. No se abren sesiones ni se envían consultas automáticamente. El aislamiento sigue dependiendo del entorno; instrucciones globales, memoria y extensiones pueden influir.

Una respuesta real se importa sin reescribirla; usa referencias distintas por sesión:

```sh
python3 scripts/pilot.py record RUTA_RUN --case D02_conservar --variant candidate --response respuesta.txt --origin claude_code_session --model 'versión observada' --session 'referencia única'
python3 scripts/pilot.py review RUTA_RUN --case D02_conservar --variant candidate --kind human --reviewer 'Revisor' --verdict pass --note 'Evidencia concreta'
python3 scripts/pilot.py report RUTA_RUN
```

`record` registra procedencia declarada, no autenticada de forma independiente. Una revisión de modelo no cuenta como revisión humana. Una fixture no cuenta como respuesta real. Un informe de desarrollo no acredita evaluación reservada ni el funcionamiento posterior del prompt recomendado.

Para comprobar un recorrido sintético sin modelos:

```sh
python3 tests/make_fixture.py
```

## Reproducción opcional con Promptfoo

`npm ci` instala la dependencia fijada en el lockfile y requiere red. Después, `npm run smoke` comprueba fixtures guardadas con un proveedor local. No se ha instalado ni ejecutado esta dependencia para validar esta entrega; las comprobaciones anteriores no la necesitan. El lockfile contiene dependencias transitivas, incluidas bibliotecas de proveedores: no significa que los scripts las usen para inferencia.

## Licencia y publicación

Esta copia no concede una licencia de reutilización: todavía no se ha elegido una. `private: true` en package.json evita publicar por npm; no determina la visibilidad de un repositorio GitHub.

Ver la ficha del proyecto en [KineticaAI](https://www.kineticaai.com/lab/proyectos/prompt-lab/).
