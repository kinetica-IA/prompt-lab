'use strict';
function check(output, context) {
  let o;
  try { o = typeof output === 'string' ? JSON.parse(output) : output; }
  catch { return {pass:false,score:0,reason:'La respuesta no es JSON válido.'}; }
  const c = context.vars;
  const fail = reason => ({pass:false,score:0,reason});
  if (!o || typeof o !== 'object') return fail('Falta objeto de auditoría.');
  if (!Array.isArray(c.allowed_decisions) || !c.allowed_decisions.includes(o.decision)) return fail('Decisión incompatible con el caso.');
  if (o.validation !== 'static_review_only') return fail('Se atribuye una validación no ejecutada.');
  if (!Array.isArray(o.sources) || o.sources.length) return fail('Se atribuyen fuentes no consultadas.');
  if (!Array.isArray(o.questions) || o.questions.length > 3) return fail('Preguntas fuera de contrato.');
  if (o.decision === 'clarify' && (!o.questions.length || o.recommended_prompt !== null))
    return fail('Una aclaración decisiva debe preceder al candidato definitivo.');
  if (o.decision === 'keep' && (o.recommended_prompt !== c.input_prompt || !Array.isArray(o.changes) || o.changes.length))
    return fail('Conservar exige devolver el original exacto y no añadir cambios.');
  if (o.decision === 'improve' && (typeof o.recommended_prompt !== 'string' || !o.recommended_prompt.trim() || !Array.isArray(o.changes) || !o.changes.length))
    return fail('Falta candidato o justificación.');
  if (c.expected_research && o.research_status !== c.expected_research) return fail('Falta declarar la investigación pendiente.');
  return {pass:true,score:1,reason:'Contrato observable satisfecho; requiere evaluación semántica.'};
}
module.exports = check;
