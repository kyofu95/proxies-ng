let gridInstance = null;
let selectedCountry = '';

const displayNames = new Intl.DisplayNames(['en'], { type: 'region' });

function renderGrid() {
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
        className: {
            table: 'table table-striped table-hover'
        },
        sort: false,
        search: false,
        pagination: {
            limit: 10,
            server: {
                url: (prev, page, limit) => {
                    params = `${prev}?limit=${limit}&offset=${page * limit}`

                    if (selectedCountry) {
                        params += '&country_code=' + selectedCountry
                    }

                    return params
                }
            }
        },
        server: {
            url: 'http://localhost:8000/api/proxy/',
            then: data => data.proxies.map(proxy => [
                proxy.ip,
                proxy.port,
                proxy.protocol,
                displayNames.of(proxy.geoaddress.country_iso_code) || proxy.geoaddress.country_iso_code,
                proxy.health.latency,
                new Date(proxy.health.last_tested).toLocaleString()
            ]),
            total: data => data.total
        },
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

            const countries = data.map(code => ({
                code,
                name: displayNames.of(code) || code
            }));

            countries.sort((a, b) => a.name.localeCompare(b.name, 'en'));

            countries.forEach(({ code, name }) => {
                const option = document.createElement("option");
                option.value = code;
                option.textContent = name;
                select.appendChild(option);
            });
        });
}

document.addEventListener("DOMContentLoaded", function () {
    loadCountries();
    renderGrid();

    document.getElementById("country-select").addEventListener("change", function () {
        selectedCountry = this.value;
        renderGrid();
    });
});