// JS extracted from index.html to keep scripts separate
async function uploadFile() {
    const fileInput = document.getElementById('pdfUpload');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a PDF file.');
        return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1010000);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resultEl = document.getElementById('result');
        resultEl.innerHTML = renderProcessingCard();

        const response = await fetch('http://localhost:5000/getSalaryDetails', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });

        // Read response text first and attempt safe JSON parse so we can show helpful errors
        const raw = await response.text();
        let data = null;
        try {
            data = raw ? JSON.parse(raw) : null;
            data = JSON.parse(data)
        } catch (e) {
            data = null; // not JSON
        }

        if (response.ok) {
            // Accept two formats:
            // format 1: { salaryDetails: { basicPay, grossPay, netPay } }
            // format 2: { basicPay, grossPay, netPay }
            let salaryObj = null;
            if (data && data.salaryDetails && typeof data.salaryDetails === 'object') {
                salaryObj = data.salaryDetails;
            } else if (data && (typeof data.basicPay !== 'undefined' || typeof data.grossPay !== 'undefined' || typeof data.netPay !== 'undefined')) {
                salaryObj = data;
            }

            if (salaryObj) {
                resultEl.innerHTML = renderSalaryCard(salaryObj);
            } else if (data && Object.keys(data).length === 0 && raw && !data) {
                // response body wasn't JSON but contained text
                resultEl.innerHTML = renderErrorCard('Server returned non-JSON response: ' + escapeHtml(raw));
            } else {
                const message = data && data.error ? data.error : 'Unexpected response shape from server';
                resultEl.innerHTML = renderErrorCard(message);
            }
        } else {
            // Non-2xx response — include HTTP status and any server message (json or text)
            let message = `HTTP ${response.status} ${response.statusText}`;
            if (data && data.error) message += ' — ' + data.error;
            else if (raw) message += ' — ' + raw;
            resultEl.innerHTML = renderErrorCard(message);
            console.warn('Fetch failed:', response.status, response.statusText, raw);
        }
    } catch (error) {
        const resultEl = document.getElementById('result');
        const message = error.name === 'AbortError' ? 'Request timed out after 1000 seconds' : error.message;
        resultEl.innerHTML = renderErrorCard(message);
    } finally {
        clearTimeout(timeoutId);
    }
}

function fmtCurrency(n){
    try{
        if (n === null || typeof n === 'undefined' || n === '') return '';
        let s = n;
        // If input is not a string, convert to string
        if (typeof s !== 'string') s = String(s);
        // Remove common currency symbols, commas and whitespace
        s = s.replace(/[,₹$€£\s]/g, '');
        // Keep only digits, minus and dot
        s = s.replace(/[^0-9.-]/g, '');
        const num = Number(s);
        if (!isFinite(num)) return n;
        return num.toLocaleString('en-IN', {style:'currency', currency:'INR', maximumFractionDigits:2});
    }catch(e){
        return n;
    }
}

function renderProcessingCard(){
    return `
        <div class="card">
            <div class="left">
                <div class="title">Processing<span class="processing"> · please wait</span></div>
                <div class="subtitle">We're extracting salary details from your PDF. This may take a few moments.</div>
            </div>
        </div>
    `;
}

function renderErrorCard(message){
    return `
        <div class="card">
            <div class="left">
                <div class="title">Error</div>
                <div class="subtitle error">${escapeHtml(message)}</div>
            </div>
        </div>
    `;
}

function renderSalaryCard(s){
    console.log('Rendering salary card with data:', s);
    const basic = fmtCurrency(s.basicPay);
    const gross = fmtCurrency(s.grossPay);
    const net = fmtCurrency(s.netPay);
    const employer = s.employerName || s.employer || '';
    const employerHtml = employer ? `<div class="subtitle" style="margin-top:8px"><strong>Employer:</strong> ${escapeHtml(employer)}</div>` : '';
    return `
        <div class="card">
            <div class="left">
                <div class="title">Salary Details <span class="net-badge">Net Pay</span></div>
                <div class="subtitle">Clean, at-a-glance view of extracted amounts</div>
                ${employerHtml}

                <div class="amounts">
                    <div class="amount">
                        <div class="label">Basic Pay</div>
                        <div class="value">${basic}</div>
                    </div>
                    <div class="amount">
                        <div class="label">Gross Pay</div>
                        <div class="value">${gross}</div>
                    </div>
                    <div class="amount">
                        <div class="label">Net Pay</div>
                        <div class="value">${net}</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function escapeHtml(str){
    if(!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
}

// keep uploadFile available globally (onclick uses it)
window.uploadFile = uploadFile;
