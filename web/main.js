async function updateDashboard() {
    let data = await eel.get_stats()();

    //Update CPU
    document.getElementById('cpu-text').innerText = Math.round(data.cpu) + "%";
    document.getElementById('cpu-mhz').innerText = data.cpu_mhz + " MHZ"; // New
    setProgress(data.cpu, 'cpu-ring');

    // Update GPU
    document.getElementById('gpu-text').innerText = Math.round(data.gpu_load) + "%";
    document.getElementById('gpu-temp').innerText = Math.round(data.gpu_temp) + "°C";
    document.getElementById('gpu-mhz').innerText = data.gpu_mhz + " MHZ"; // New
    setProgress(data.gpu_load, 'gpu-ring');

    // Update Process List 
    const list = document.getElementById('process-list');
    list.innerHTML = ""; // Clear old list

    // Loop through the Top 5 processes we got from Python
    data.processes.forEach(proc => {
        // Create HTML for each row
        let row = document.createElement('div');
        row.className = 'proc-row';
        
        let name = document.createElement('span');
        name.innerText = proc.name;
        
        let usage = document.createElement('span');
        usage.innerText = proc.cpu_percent.toFixed(1) + "%"; // Round to 1 decimal
        
        row.appendChild(name);
        row.appendChild(usage);
        list.appendChild(row);
    });
}

setInterval(updateDashboard, 1000);