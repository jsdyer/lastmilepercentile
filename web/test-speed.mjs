const start = document.querySelector('#test-start');
const status = document.querySelector('#test-state');
const result = document.querySelector('#test-readings');
const testRoot = new URL('./ndt/',import.meta.url);
const speeds = new Map();
const formatted = new Intl.NumberFormat('en-CA',{maximumFractionDigits:2});

function save(direction,value) {
  if (!Number.isFinite(value) || value <= 0) return;
  speeds.set(direction,value);
  result.textContent = [...speeds].map(([name,rate]) => name+' '+formatted.format(rate)+' Mbps').join(' · ');
}
function apply() {
  const value = speeds.get(document.querySelector('#direction').value);
  if (value !== undefined) {
    const field = document.querySelector('#speed');
    field.value = value.toFixed(2);
    field.dispatchEvent(new Event('input'));
  }
}
document.querySelector('#direction').addEventListener('change',apply);
start.addEventListener('click', async () => {
  if (start.disabled) return;
  start.disabled = true;
  speeds.clear();
  result.textContent = '';
  status.textContent = 'Finding an M-Lab test server…';
  try {
    const code = await window.ndt7.test({
      userAcceptedDataPolicy:true, metadata:{client_name:'coolcode-lastmilepercentile',client_version:'1.0'},
      downloadworkerfile:new URL('ndt7-download-worker.js',testRoot).href,
      uploadworkerfile:new URL('ndt7-upload-worker.js',testRoot).href
    }, {
      downloadStart() { status.textContent = 'Measuring download speed…'; },
      downloadComplete(data) { save('download',data.LastClientMeasurement?.MeanClientMbps); apply(); },
      uploadStart() { status.textContent = 'Measuring upload speed…'; },
      uploadComplete(data) {
        const stats = data.LastServerMeasurement?.TCPInfo;
        if (stats?.ElapsedTime > 0) save('upload',8*stats.BytesReceived/stats.ElapsedTime);
        apply();
      },
      error() { status.textContent = 'An M-Lab test connection could not finish.'; }
    });
    status.textContent = code === 0 && speeds.size === 2
      ? 'Test complete. Choose your city and network to compare the measured speed.'
      : 'The test did not return both speeds. Compare any result shown or enter your own speed.';
  } catch {
    status.textContent = 'M-Lab is unavailable. You can enter a speed below and still compare it.';
  } finally { start.disabled = false; }
});
