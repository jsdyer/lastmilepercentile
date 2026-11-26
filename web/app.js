import {bracket} from './band.mjs';
const $ = id => document.getElementById(id);
const fmt = Intl.NumberFormat('en-CA', {maximumFractionDigits: 2});
const precise = Intl.NumberFormat('en-CA', {maximumSignificantDigits: 7});
const names = {AB:'Alberta',BC:'British Columbia',MB:'Manitoba',NB:'New Brunswick',NL:'Newfoundland and Labrador',NS:'Nova Scotia',NT:'Northwest Territories',NU:'Nunavut',ON:'Ontario',PE:'Prince Edward Island',QC:'Quebec',SK:'Saskatchewan',YT:'Yukon'};
const monthName = s => new Date(s+'-15T12:00:00Z').toLocaleDateString('en-CA',{year:'numeric',month:'long',timeZone:'UTC'});
let status, rows = [], generation = 0;
function options(id, entries, preferred, keepMissing = false) {
  const select = $(id);
  select.replaceChildren(...entries.map(([key, label]) => new Option(label, key)));
  if (entries.some(([key]) => String(key) === String(preferred))) {
    select.value = preferred;
  } else if (keepMissing && preferred) {
    select.add(new Option(preferred + ' · no published group', preferred, false, true));
  }
  select.disabled = !select.options.length;
}
async function json(file) {
  const response = await fetch(new URL(file,import.meta.url));
  if (!response.ok) throw Error(response.status);
  return response.json();
}
function networks(preferred = $('asn').value, keepMissing = false) {
  const choices = rows.filter(r => r[0] === $('region').value && r[1] === $('city').value).sort((a,b)=> b[4]-a[4]);
  options('asn', choices.map(r=>[r[2],r[3] + ' · AS' + r[2]]),preferred,keepMissing);
  display();
}
function cities(preferred = $('city').value, asn = $('asn').value, keepMissing = false) {
  const values = [...new Set(rows.filter(r=>r[0] === $('region').value).map(r=>r[1]))].sort((a,b)=>a.localeCompare(b));
  options('city', values.map(v=>[v,v]), preferred, keepMissing);
  networks(asn, keepMissing);
}
async function load(initial = false) {
  const mine = ++generation;
  const prefs = initial ? [document.body.dataset.region || 'BC',document.body.dataset.city || 'Langley',document.body.dataset.asn || '852'] : ['region','city','asn'].map(id=>$(id).value);
  const month = $('month').value, dir = $('direction').value;
  $('status').textContent = 'Loading comparison groups…';
  $('results').hidden = $('source-file').hidden = true;
  ['region','city','asn'].forEach(id=>$(id).disabled = true);
  try {
    const next = await json(`data/${month}-${dir}.json`);
    if (mine !== generation) return;
    rows = next;
    const keepMissing = !initial || Boolean(document.body.dataset.asn);
    options('region',[...new Set(rows.map(r=>r[0]))].sort().map(v=>[v,names[v] || v]),prefs[0],keepMissing);
    const src = status.months.find(m=>m.month===month).sources[dir];
    $('source-file').href = src.url; $('source-file').hidden = false;
    cities(prefs[1], prefs[2], keepMissing);
  } catch { if (mine === generation) $('status').textContent = 'This month could not be loaded. Try another month or reload the page.'; }
}
function display() {
  if ($('asn').disabled) return;
  const row = rows.find(r=>r[0]===$('region').value && r[1]===$('city').value && String(r[2])===$('asn').value);
  if (!row) {
    $('results').hidden = true;
    $('status').textContent = 'No qualifying tests for this city and network in the selected month and direction. Choose a different month or comparison.';
    return;
  }
  $('status').textContent = '';
  $('results').hidden = false;
  const speed = $('speed').valueAsNumber, values = row.slice(5);
  const band = bracket(speed,values,status.percentiles);
  $('context').textContent = row[1]+', '+row[0]+' / '+monthName($('month').value);
  $('band').textContent = band?.label || 'Enter a speed in Mbps';
  const dir = $('direction').value;
  $('result-text').textContent = band ? `${precise.format(speed)} Mbps ${dir}, compared with ${fmt.format(row[4])} ${dir} tests on ${row[3]} (AS${row[2]}).` : 'Use zero or a positive number to compare your result.';
  $('chart').replaceChildren(...values.map((n,i)=>{
    const bar = document.createElement('div'); bar.className = 'bar' + (band?.indices.includes(i) ? ' match' : '');
    const label = document.createElement('span'); label.textContent = 'P'+status.percentiles[i];
    const track = document.createElement('span'); track.className='track';
    const fill = document.createElement('i'); fill.style.width = (values.at(-1) ? 100*n/values.at(-1) : 0)+'%';
    track.append(fill);
    const val = document.createElement('strong'); val.textContent = fmt.format(n); val.title = String(n)+' Mbps';
    bar.append(label,track,val); return bar;
  }));
}
$('inputs').addEventListener('submit', e=>e.preventDefault());
$('month').onchange = $('direction').onchange = () => load();
$('region').onchange = () => cities(); $('city').onchange = () => networks(); $('asn').onchange = display; $('speed').oninput = display;
try {
  status = await json('data/status.json');
  $('edition').textContent = 'Data retrieved '+status.retrieved+' · '+status.cohorts.toLocaleString('en-CA')+' monthly city/network/direction groups.';
  options('month', status.months.map(m=>[m.month,monthName(m.month)]), status.end);
  await load(true);
} catch { $('status').textContent = 'The data index could not be loaded. Reload the page to retry.'; }
