import test from 'node:test';
import assert from 'node:assert/strict';
import {bracket} from '../web/band.mjs';
import {readFileSync} from 'node:fs';
test('intervals and equal cutoffs',()=>{
  const p=[1,5,10,50,99],v=[1,2,2,60,130];
  assert.equal(bracket(0,v,p).label,'Below P1');
  assert.equal(bracket(2,v,p).label,'At the shared P5–P10 cutoff');
  assert.equal(bracket(42,v,p).label,'Between P10 and P50');
  assert.equal(bracket(200,v,p).label,'Above P99');
  assert.equal(bracket(60,v,p).label,'At P50');
  assert.equal(bracket(-1,v,p),null);
});
test('every published cohort matches its month and has ordered boundaries',()=>{
  const json=file=>JSON.parse(readFileSync(new URL('../web/data/'+file,import.meta.url)));
  const meta=json('status.json');let count=0;
  for (const m of meta.months) for(const d of ['download','upload']) {
    const rows=json(m.month+'-'+d+'.json');assert.equal(rows.length,m.counts[d]); count+=rows.length;
    assert.equal(new Set(rows.map(r=>JSON.stringify(r.slice(0,3)))).size,rows.length);
    for (const row of rows) {
      assert(row[4]>=meta.min_count); assert.equal(row.length,5+meta.percentiles.length);
      row.slice(5).forEach((v,i,a)=>assert(Number.isFinite(v) && v>=0 && (!i || v>=a[i-1])));
    }
  }
  assert.equal(count,meta.cohorts);
});
