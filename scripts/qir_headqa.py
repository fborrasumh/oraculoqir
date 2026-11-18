#!/usr/bin/env python3
"""OráculoQIR · años antiguos desde HEAD-QA (conjunto de datos académico con los exámenes oficiales del Ministerio de Sanidad
y su respuesta correcta; Vilares y Gómez-Rodríguez, ACL 2019; v2: Correa-Guillén, Gómez-Rodríguez y Vilares, 2025. Licencia MIT).
Se ejecuta en GitHub Actions:  python3 scripts/qir_headqa.py
Solo rellena los años que no tengan ya un examen completo (portal oficial o cuaderno + plantilla de la cosecha).
Cada cuaderno de HEAD-QA se llama como el del Ministerio, «Cuaderno_2013_1_Q»: convocatoria 2013, examen de enero de 2014.
Escribe data/raw/<año>/headqa.json (preguntas, opciones y respuesta oficial) y data/raw/<año>/origen.txt."""
import json, re, sys, time, pathlib, urllib.request, urllib.parse
R = pathlib.Path(__file__).resolve().parent.parent; RAW = R / 'data' / 'raw'
LETRA = 'Q'
CONJUNTOS = ['alesi12/head_qa_v2', 'dvilares/head_qa']
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
    sp = get('/splits?dataset=' + urllib.parse.quote(ds))['splits']
    confs = [s for s in sp if s['config'] in ('es', 'default', 'es-ES', 'spanish')] or sp
    print(f'  {ds}: configuraciones {sorted({s["config"] for s in sp})}; se usan {[(s["config"], s["split"]) for s in confs]}')
    for s in confs:
        off = 0
        while True:
            j = get(f'/rows?dataset={urllib.parse.quote(ds)}&config={s["config"]}&split={s["split"]}&offset={off}&length=100')
            rs = j.get('rows', [])
            for r in rs: yield r['row']
            off += len(rs)
            if not rs or off >= j.get('num_rows_total', 0): break


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
    for y in sorted(examenes, key=int):
        e = examenes[y]; d = RAW / y; qs = [e['qs'][k] for k in sorted(e['qs'])]
        if completo(d): print(f'{y}: ya hay examen completo; HEAD-QA ({e["nombre"]}, {len(qs)} preguntas) no se usa'); continue
        if len(qs) < 150: print(f'{y}: HEAD-QA solo tiene {len(qs)} preguntas de {e["nombre"]}; no se usa'); continue
        d.mkdir(parents=True, exist_ok=True)
        (d / 'headqa.json').write_text(json.dumps(qs, ensure_ascii=False), encoding='utf-8')
        (d / 'origen.txt').write_text(f'Copia de terceros del documento oficial del Ministerio de Sanidad\nheadqa: https://huggingface.co/datasets/{e["ds"]} :: {e["nombre"]}\n', encoding='utf-8')
        print(f'{y}: HEAD-QA OK ← {e["ds"]} :: {e["nombre"]} ({len(qs)} preguntas, {sum(1 for q in qs if q["correcta"])} con respuesta, {sum(1 for q in qs if q["imagen"])} con imagen)')


if __name__ == '__main__':
    main()
