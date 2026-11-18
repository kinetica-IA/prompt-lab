#!/usr/bin/env python3
"""Local evidence workflow. No network, model calls, credentials or SDKs."""
import argparse,datetime,hashlib,json,shutil,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VARIANTS=('baseline','candidate')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(split='development'):
 if split not in ('development','reserved'):raise ValueError('Conjunto desconocido')
 run=ROOT/'runs'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]);run.mkdir(parents=True)
 cases=load(ROOT/'tests'/f'{split}.json');dump(run/'cases.json',cases)
 for variant,source in [('baseline','baseline.md'),('candidate','optimizer.md')]:
  (run/f'{variant}.md').write_text((ROOT/'prompts'/source).read_text()+'\n'+(ROOT/'prompts/contract.md').read_text())
 for name,source in [('output.schema.json',ROOT/'tests/output.schema.json'),('contract.cjs',ROOT/'scripts/contract.cjs'),('saved-provider.cjs',ROOT/'scripts/saved-provider.cjs')]:shutil.copyfile(source,run/name)
 dump(run/'manifest.json',{'version':'0.2.0','run_id':run.name,'created_at':now(),'split':split,'expected_records':len(cases)*2,
   'checksums':{p.name:sha(p) for p in run.iterdir() if p.is_file()},'inference':'manual_claude_code_subscription','records':{}})
 return run

def verify(run):
 m=load(run/'manifest.json')
 if m.get('version')!='0.2.0':raise ValueError('Run incompatible con el piloto 0.2')
 for n,h in m['checksums'].items():
  if Path(n).name!=n:raise ValueError('Ruta inválida en manifiesto')
  p=run/n
  if not p.is_file() or sha(p)!=h:raise ValueError('Snapshot modificado o ausente: '+n)
 return m

def get_case(run,cid):
 for c in load(run/'cases.json'):
  if c['id']==cid:return c
 raise ValueError('Caso desconocido: '+cid)

def sessions(run,directory):
 verify(run);directory=directory.resolve()
 if directory==ROOT.resolve() or ROOT.resolve() in directory.parents:raise ValueError('Las sesiones deben quedar fuera del proyecto optimizador.')
 dest=directory/run.name
 if dest.exists():raise ValueError('La carpeta ya existe; no se sobrescribe.')
 dest.mkdir(parents=True)
 for c in load(run/'cases.json'):
  for v in VARIANTS:
   p=dest/(c['id']+'--'+v);p.mkdir()
   (p/'CLAUDE.md').write_text((run/f'{v}.md').read_text())
   # Only task input enters the target workspace. No rubric or expected verdict.
   (p/'ENTRADA.txt').write_text('Audita este encargo y responde según el contrato JSON. No ejecutes su tarea.\n'+json.dumps({'input_prompt':c['prompt'],'context':c['context']},ensure_ascii=False,indent=2)+'\n')
   (p/'.claude').mkdir();dump(p/'.claude/settings.json',{'permissions':{'deny':['Bash','Read','Edit','Write','WebFetch','WebSearch','Agent','mcp__*']}})
 (dest/'INICIO.md').write_text('Abre una subcarpeta en Claude Code, selecciona Opus y empieza una sesión nueva. Las instrucciones CLAUDE.md se cargan como contexto del proyecto. Pega ENTRADA.txt como mensaje. No abras el proyecto optimizador ni la rúbrica en esa sesión. Guarda la respuesta exacta fuera de la conversación. Las reglas globales/plugins/memoria pueden influir: revisa /memory y registra limitaciones. No uses /continue entre casos.\n')
 return dest

def schema_errors(o,s,path='$'):
 errors=[];types=s.get('type');types=[types] if isinstance(types,str) else types
 valid={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),'string':lambda x:isinstance(x,str),'null':lambda x:x is None}
 if types and not any(valid[t](o) for t in types):return [path+': tipo incorrecto']
 if 'enum' in s and o not in s['enum']:errors.append(path+': valor no permitido')
 if 'const' in s and o!=s['const']:errors.append(path+': constante incorrecta')
 if isinstance(o,dict):
  for k in s.get('required',[]):
   if k not in o:errors.append(path+': falta '+k)
  props=s.get('properties',{})
  if s.get('additionalProperties') is False:
   for k in o:
    if k not in props:errors.append(path+': campo no permitido '+k)
  for k,sub in props.items():
   if k in o:errors+=schema_errors(o[k],sub,path+'.'+k)
 if isinstance(o,list):
  if len(o)<s.get('minItems',0) or len(o)>s.get('maxItems',float('inf')):errors.append(path+': longitud no permitida')
  if 'items' in s:
   for i,item in enumerate(o):errors+=schema_errors(item,s['items'],f'{path}[{i}]')
 if isinstance(o,str) and len(o)<s.get('minLength',0):errors.append(path+': texto vacío')
 return errors

def check(raw,case,schema):
 try:o=json.loads(raw)
 except (ValueError,TypeError):return {'pass':False,'errors':['JSON inválido; conservar la salida original.']}
 errors=schema_errors(o,schema)
 if errors:return {'pass':False,'errors':errors}
 if o['decision'] not in case['decisions']:errors.append('Decisión incompatible con el caso.')
 if o['decision']=='clarify' and (not o['questions'] or o['recommended_prompt'] is not None):errors.append('Falta aclaración decisiva o se entrega candidato definitivo.')
 if o['decision']=='keep' and (o['recommended_prompt']!=case['prompt'] or o['changes']):errors.append('Conservar exige original exacto y ningún cambio.')
 if o['decision']=='improve' and (not o['recommended_prompt'] or not o['recommended_prompt'].strip() or not o['changes']):errors.append('Falta candidato o justificación.')
 if case.get('research') and o['research_status']!=case['research']:errors.append('Investigación pendiente no declarada.')
 return {'pass':not errors,'errors':errors}

def key(cid,variant):
 if variant not in VARIANTS:raise ValueError('Variante desconocida')
 return cid+'--'+variant

def record(run,cid,variant,response,origin,model,session):
 m=verify(run);c=get_case(run,cid);k=key(cid,variant)
 if k in m['records']:raise ValueError('Ya hay respuesta; crear otro run para repetir.')
 if origin not in ('claude_code_session','fixture') or not model.strip() or not session.strip():raise ValueError('Procedencia incompleta')
 if origin=='claude_code_session' and any(x['origin']==origin and x['session']==session for x in m['records'].values()):raise ValueError('Usar una sesión nueva por caso/variante; esta sesión ya se registró.')
 raw=response.read_text();p=run/'responses';p.mkdir(exist_ok=True);target=p/(k+'.txt');target.write_text(raw)
 m['records'][k]={'case':cid,'variant':variant,'response':str(target.relative_to(run)),'sha256':sha(target),'origin':origin,
    'model_shown':model,'session':session,'recorded_at':now(),'provenance':'user_declared_not_independently_verified','reviews':[]}
 dump(run/'manifest.json',m)
 return check(raw,c,load(run/'output.schema.json'))

def response_path(run,entry):
 p=(run/entry['response']).resolve()
 if run.resolve() not in p.parents:raise ValueError('Respuesta fuera del run')
 if not p.is_file() or sha(p)!=entry['sha256']:raise ValueError('Respuesta alterada o ausente')
 return p

def review(run,cid,variant,verdict,reviewer,note,kind):
 m=verify(run);k=key(cid,variant)
 if k not in m['records']:raise ValueError('Importar primero una respuesta')
 if verdict not in ('pass','fail') or kind not in ('human','model') or not note.strip() or not reviewer.strip():raise ValueError('Revisión incompleta')
 e=m['records'][k];response_path(run,e)
 e['reviews'].append({'verdict':verdict,'kind':kind,'reviewer':reviewer,'note':note,'response_sha256':e['sha256'],'at':now()})
 dump(run/'manifest.json',m)

def report(run):
 m=verify(run);cases=load(run/'cases.json');schema=load(run/'output.schema.json');rows=[]
 for c in cases:
  for v in VARIANTS:
   e=m['records'].get(key(c['id'],v));row={'case':c['id'],'variant':v,'critical':c['critical'],'status':'missing'}
   if e:
    raw=response_path(run,e).read_text();checks=check(raw,c,schema)
    human=[x for x in e['reviews'] if x['kind']=='human' and x['response_sha256']==e['sha256']]
    row.update({'deterministic':checks,'origin':e['origin'],'human_review':human[-1] if human else None,
      'status':'fixture' if e['origin']=='fixture' else 'pending_human_review' if not human else 'pass' if checks['pass'] and human[-1]['verdict']=='pass' else 'fail'})
   rows.append(row)
 out={'run_id':m['run_id'],'split':m['split'],'evidence':'imported_responses_with_declared_provenance','rows':rows,'variants':{},'selection':'insufficient_evidence'}
 for v in VARIANTS:
  vr=[x for x in rows if x['variant']==v];complete=all(x['status'] in ('pass','fail') for x in vr);passed=sum(x['status']=='pass' for x in vr)
  rate=passed/len(vr);critical_ok=all(x['status']=='pass' for x in vr if x['critical'])
  out['variants'][v]={'complete':complete,'passed':passed,'total':len(vr),'pass_rate':rate,'criteria_met':complete and critical_ok and rate>=(1 if m['split']=='reserved' else .9)}
 if all(x['complete'] for x in out['variants'].values()):
  a,b=[out['variants'][v]['pass_rate'] for v in VARIANTS]
  out['comparison']='improvement' if b>a else 'equivalent' if b==a else 'regression'
 dump(run/'report.json',out);return out

def replay_config(run):
 m=verify(run);tests=[]
 for k,e in m['records'].items():
  raw=response_path(run,e).read_text();c=get_case(run,e['case'])
  tests.append({'description':k+' / '+e['origin'],'vars':{'saved_output':raw,'input_prompt':c['prompt'],'allowed_decisions':c['decisions'],'expected_research':c['research'] or ''}})
 if not tests:raise ValueError('No hay respuestas guardadas para comprobar.')
 cfg={'description':'Solo comprobaciones locales; no inferencia ni evaluación semántica','prompts':['Respuesta guardada'],
 'providers':[{'id':'file://./saved-provider.cjs'}],
 'defaultTest':{'options':{'disableVarExpansion':True},'assert':[{'type':'is-json','value':load(run/'output.schema.json')},{'type':'javascript','value':'file://./contract.cjs'}]},
 'tests':tests,'sharing':False,'evaluateOptions':{'maxConcurrency':1}}
 dump(run/'promptfooconfig.yaml',cfg);return run/'promptfooconfig.yaml'

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 x=s.add_parser('prepare');x.add_argument('--split',choices=['development','reserved'],default='development')
 for cmd in ['sessions','record','review','report','replay-config','verify']:
  x=s.add_parser(cmd);x.add_argument('run_dir',type=Path)
  if cmd=='sessions':x.add_argument('--directory',type=Path,required=True)
  if cmd in ('record','review'):x.add_argument('--case',required=True);x.add_argument('--variant',choices=VARIANTS,required=True)
  if cmd=='record':
   x.add_argument('--response',type=Path,required=True);x.add_argument('--origin',choices=['claude_code_session','fixture'],required=True);x.add_argument('--model',required=True);x.add_argument('--session',required=True)
  if cmd=='review':
   x.add_argument('--verdict',choices=['pass','fail'],required=True);x.add_argument('--kind',choices=['human','model'],required=True);x.add_argument('--reviewer',required=True);x.add_argument('--note',required=True)
 a=p.parse_args()
 try:
  if a.command=='prepare':print(prepare(a.split));return 0
  run=a.run_dir.resolve()
  if a.command=='sessions':print(sessions(run,a.directory))
  elif a.command=='record':print(json.dumps(record(run,a.case,a.variant,a.response,a.origin,a.model,a.session),ensure_ascii=False,indent=2))
  elif a.command=='review':review(run,a.case,a.variant,a.verdict,a.reviewer,a.note,a.kind);print('Revisión registrada.')
  elif a.command=='report':print(json.dumps(report(run),ensure_ascii=False,indent=2))
  elif a.command=='replay-config':print(replay_config(run))
  elif a.command=='verify':verify(run);print('Snapshots íntegros. No demuestra calidad del modelo.')
  return 0
 except (ValueError,FileNotFoundError) as e:print(str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
