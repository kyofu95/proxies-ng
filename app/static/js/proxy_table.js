let gridInstance = null;

function fetchProxies(country_code = '') {
    let url = 'http://localhost:8000/api/proxy/';
    if (country_code) {
        url += `?country_code=${country_code}`;
    }

    return fetch(url)
        .then(res => res.json())
        .then(data => {
            return data.map(proxy => [
                proxy.ip,
                proxy.port,
                proxy.protocol,
                proxy.geoaddress.country_iso_code,
                proxy.health.latency,
                new Date(proxy.health.last_tested).toLocaleString()
            ]);
        });
}

function renderGrid(rows) {
    if (gridInstance) gridInstance.destroy();

    gridInstance = new gridjs.Grid({
        columns: [
            'IP Address',
            'Port',
            'Protocol',
            'Country',
            'Latency (ms)',
            'Last Tested'
        ],
        data: rows,
        search: false,
        sort: true,
        pagination: {
            enabled: true,
            limit: 10
        }
    }).render(document.getElementById("proxy-table"));
}

function loadCountries() {
    fetch('http://localhost:8000/api/country/')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById("country-select");

            const defaultOption = document.createElement("option");
            defaultOption.value = '';
            defaultOption.textContent = 'All';
            select.appendChild(defaultOption);

            data.sort().forEach(code => {
                const option = document.createElement("option");
                option.value = code;
                option.textContent = code;
                select.appendChild(option);
            });
        });
}

document.addEventListener("DOMContentLoaded", function () {
    loadCountries();

    fetchProxies().then(renderGrid);

    document.getElementById("country-select").addEventListener("change", function () {
        selectedCountry = this.value;
        fetchProxies(selectedCountry).then(renderGrid);
    });
});