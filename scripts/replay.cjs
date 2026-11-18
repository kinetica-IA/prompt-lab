'use strict';
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..');
const run=process.argv[2]&&path.resolve(process.argv[2]);
if(!run){console.error('Uso: node scripts/replay.cjs RUTA_RUN');process.exit(2);}
const prep=cp.spawnSync('python3',[path.join(__dirname,'pilot.py'),'replay-config',run],{encoding:'utf8'});
if(prep.status!==0){console.error(prep.stderr);process.exit(2);}
const bin=process.env.PROMPTFOO_BIN||path.join(root,'node_modules/.bin/promptfoo');
if(!fs.existsSync(bin)){console.error('Promptfoo es opcional: instalar con npm ci para usar replay.');process.exit(2);}
const env={...process.env,PROMPTFOO_DISABLE_TELEMETRY:'1',PROMPTFOO_DISABLE_TEMPLATING:'1',PROMPTFOO_DISABLE_UPDATE_CHECK:'1',PROMPTFOO_CONFIG_DIR:path.join(run,'.promptfoo'),PROMPTFOO_LOG_DIR:path.join(run,'.promptfoo/logs')};
const res=cp.spawnSync(bin,['eval','-c',path.join(run,'promptfooconfig.yaml'),'-o',path.join(run,'promptfoo-local-results.json'),'--no-cache','--no-share','--no-write','--no-table'],{cwd:run,env,stdio:'inherit',timeout:60000});
if(res.error)console.error(res.error.message);
process.exit(res.status??2);
