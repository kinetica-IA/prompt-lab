const path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
const made=cp.spawnSync('python3',[path.join(root,'tests/make_fixture.py')],{encoding:'utf8'});
if(made.status!==0){console.error(made.stderr);process.exit(2);}
const run=made.stdout.trim();console.log('Fixture local, NO respuesta de Opus:',run);
const result=cp.spawnSync(process.execPath,[path.join(__dirname,'replay.cjs'),run],{env:process.env,stdio:'inherit'});
process.exit(result.status??2);
