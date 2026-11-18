const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {JSDOM} = require('jsdom');
function fixture() {
  const source = fs.readFileSync('templates/clientes.html','utf8');
  const body = source.split('<script>')[0];
  const dom = new JSDOM(body);
  const reads = [], writes = [];
  const sandbox = {document:dom.window.document, console, setTimeout, clearTimeout,
    showMsg(){},modalHide(){},modalShow(){},
    apiGet(){return new Promise(resolve=>reads.push(resolve));},
    apiPost(){return new Promise(resolve=>writes.push(resolve));},apiPut(){return new Promise(resolve=>writes.push(resolve));}};
  vm.createContext(sandbox);
  vm.runInContext(source.split('<script>')[1].split('</script>')[0].replace(/{{.*?}}/g,'/api/clients'),sandbox);
  return {dom,sandbox,reads,writes};
}
const tick = () => new Promise(resolve => setImmediate(resolve));
test('only the latest response renders and client values remain text',async()=>{
  const f=fixture();
  f.sandbox.loadClients();
  f.reads[1]([{id:1,name:'<img src=x onerror=alert(1)>',email:'a@example.com',active:true}]);
  await tick();
  f.reads[0]([{id:2,name:'Old response',active:true}]);
  await tick();
  const content=f.dom.window.document.getElementById('clients-content');
  assert.equal(content.querySelectorAll('img').length,0);
  assert.match(content.textContent,/<img/);
  assert.doesNotMatch(content.textContent,/Old response/);
  f.dom.window.close();
});
test('repeated submit sends one write and restores the button',async()=>{
  const f=fixture();
  f.dom.window.document.getElementById('client-name').value='Cliente';
  const event={preventDefault(){}};
  f.sandbox.saveClient(event);f.sandbox.saveClient(event);
  assert.equal(f.writes.length,1);
  const button=f.dom.window.document.querySelector('#form-client button[type="submit"]');
  assert.equal(button.disabled,true);
  f.writes[0]({id:1});await tick();
  assert.equal(button.disabled,false);
  f.dom.window.close();
});
