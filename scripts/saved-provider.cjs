'use strict';
// Promptfoo interface name only: no network, SDK or model call.
module.exports=class SavedOutputProvider {
  id(){return 'local-saved-output';}
  async callApi(_prompt, context){
    if(typeof context?.vars?.saved_output!=='string') throw new Error('Falta respuesta guardada.');
    return {output:context.vars.saved_output};
  }
};
