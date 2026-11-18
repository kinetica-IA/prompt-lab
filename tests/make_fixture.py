"""Integration fixture: does not call Claude. Not model evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pilot
run=pilot.prepare();case=pilot.get_case(run,'D02_conservar')
o={'decision':'keep','diagnosis':['Fixture para comprobar infraestructura.'],'questions':[],'assumptions':[],'recommended_prompt':case['prompt'],'changes':[],'research_status':'not_needed','sources':[],'validation':'static_review_only','limitations':['No es una respuesta de Opus.']}
p=run/'fixture.txt';pilot.dump(p,o)
for variant in pilot.VARIANTS:pilot.record(run,case['id'],variant,p,'fixture','fixture_not_model','fixture')
pilot.report(run);print(run)
