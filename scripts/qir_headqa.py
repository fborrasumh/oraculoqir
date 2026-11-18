#!/usr/bin/env python3
"""OráculoQIR · años antiguos desde HEAD-QA (conjunto de datos académico con los exámenes oficiales del Ministerio de Sanidad
y su respuesta correcta; Vilares y Gómez-Rodríguez, ACL 2019; v2: Correa-Guillén, Gómez-Rodríguez y Vilares, 2025. Licencia MIT).
Se ejecuta en GitHub Actions:  python3 scripts/qir_headqa.py
Solo rellena los años que no tengan ya un examen completo (portal oficial o cuaderno + plantilla de la cosecha).
Cada cuaderno de HEAD-QA se llama como el del Ministerio, «Cuaderno_2013_1_Q»: convocatoria 2013, examen de enero de 2014.
Si el año ya tiene el cuaderno PDF (de la cosecha) sin plantilla, solo toma sus respuestas (data/raw/<año>/respuestas_cruce.json),
y solo si el cuaderno es el mismo (enunciados parecidos pregunta a pregunta). Si no hay cuaderno, escribe data/raw/<año>/headqa.json."""
import json, re, sys, time, pathlib, urllib.request, urllib.parse
R = pathlib.Path(__file__).resolve().parent.parent; RAW = R / 'data' / 'raw'
LETRA = 'Q'
CONJUNTOS = ['alesi12/head_qa_v2']   # la v2 incluye los cuadernos de la v1 y años más recientes
API = 'https://datasets-server.huggingface.co'
UA = {'User-Agent': 'Mozilla/5.0 (OraculoFSE; +https://github.com/fborrasumh)'}


def get(ruta):
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + ruta, headers=UA), timeout=120) as r: return json.loads(r.read())
        except Exception as e:
            print('  reintento', ruta[:90], e); time.sleep(4 * (k + 1))
    raise RuntimeError('sin respuesta de ' + ruta)


def completo(d):
    """¿Ya hay un examen usable en este año? (portal, o cuaderno + plantilla de la cosecha)"""
    return (d / 'respuestas.json').exists() or ((d / 'cuaderno.txt').exists() and (d / 'plantilla.txt').exists())


def filas(ds):
    """Todas las filas en español del conjunto (todas sus particiones), leyendo sus ficheros parquet de una vez."""
    import io, pyarrow.parquet as pq
    ps = [p for p in get('/parquet?dataset=' + urllib.parse.quote(ds))['parquet_files'] if p['config'] in ('es', 'default')]
    print(f'  {ds}: {len(ps)} ficheros parquet en español ({sorted({p["split"] for p in ps})})')
    for p in ps:
        with urllib.request.urlopen(urllib.request.Request(p['url'], headers=UA), timeout=300) as r: b = r.read()
        for row in pq.read_table(io.BytesIO(b)).to_pylist(): yield row


def palabras(t): return set(re.findall(r'[a-záéíóúñü0-9]{3,}', str(t).lower()))


def parecido(a, b):
    A, B = palabras(a), palabras(b)
    return len(A & B) / max(1, len(A | B))


def main():
    examenes = {}
    for ds in CONJUNTOS:
        try:
            for r in filas(ds):
                nom = str(r.get('name') or '')
                m = re.match(r'Cuaderno_(20\d\d)_\d+_([A-Z]+)$', nom)
                if not m or m.group(2) != LETRA: continue
                y = int(m.group(1)) + 1
                if str(y) in examenes and examenes[str(y)]['ds'] != ds: continue   # cada año, de un solo conjunto (el primero que lo tenga)
                ans = sorted(r.get('answers') or [], key=lambda a: int(a['aid']))
                e = examenes.setdefault(str(y), {'ds': ds, 'nombre': nom, 'qs': {}})
                e['qs'][int(r['qid'])] = {'n': int(r['qid']), 'enunciado': str(r.get('qtext') or '').strip(), 'opciones': [str(a['atext']).strip() for a in ans],
                                          'correcta': int(r['ra']) if r.get('ra') not in (None, '') else None, 'imagen': bool(r.get('image'))}
        except Exception as ex: print('  ✕', ds, ex)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import qir_datos as M
    for y in sorted(examenes, key=int):
        e = examenes[y]; d = RAW / y; qs = [e['qs'][k] for k in sorted(e['qs'])]; fuente = f'https://huggingface.co/datasets/{e["ds"]} :: {e["nombre"]}'
        if completo(d): print(f'{y}: ya hay examen completo; HEAD-QA ({e["nombre"]}, {len(qs)} preguntas) no se usa'); continue
        if len(qs) < 150: print(f'{y}: HEAD-QA solo tiene {len(qs)} preguntas de {e["nombre"]}; no se usa'); continue
        if (d / 'cuaderno.txt').exists():
            # hay cuaderno (de la cosecha) sin plantilla: de HEAD-QA solo se toman las respuestas, si es el MISMO cuaderno
            cq, _ = M.mejor_cuaderno((d / 'cuaderno.txt').read_text(encoding='utf-8')); cq = {q['n']: q for q in cq}
            comunes = [q for q in qs if q['n'] in cq]
            sim = sum(parecido(q['enunciado'], cq[q['n']]['enunciado']) for q in comunes) / max(1, len(comunes))
            if len(comunes) < 0.9 * len(cq) or sim < 0.6:
                print(f'{y}: el cuaderno no es el mismo que el de HEAD-QA ({len(comunes)} preguntas comunes, parecido medio {sim:.2f}); no se usan sus respuestas'); continue
            resp = {str(q['n']): q['correcta'] for q in qs if q['correcta']}
            (d / 'respuestas_cruce.json').write_text(json.dumps(resp), encoding='utf-8')
            (d / 'headqa.json').unlink(missing_ok=True)   # con cuaderno propio, las preguntas salen del PDF
            o = d / 'origen.txt'; prev = o.read_text(encoding='utf-8') if o.exists() else 'Copia de terceros del documento oficial del Ministerio de Sanidad\n'
            o.write_text(prev.rstrip('\n') + f'\nrespuestas: {fuente}\n', encoding='utf-8')
            print(f'{y}: respuestas de HEAD-QA OK ← {fuente} ({len(resp)} respuestas; mismo cuaderno: {len(comunes)} preguntas, parecido medio {sim:.2f})')
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / 'headqa.json').write_text(json.dumps(qs, ensure_ascii=False), encoding='utf-8')
        (d / 'origen.txt').write_text(f'Copia de terceros del documento oficial del Ministerio de Sanidad\nheadqa: {fuente}\n', encoding='utf-8')
        print(f'{y}: HEAD-QA OK ← {fuente} ({len(qs)} preguntas, {sum(1 for q in qs if q["correcta"])} con respuesta, {sum(1 for q in qs if q["imagen"])} con imagen)')

if __name__ == '__main__':
    main()
