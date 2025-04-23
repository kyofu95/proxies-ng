let gridInstance = null;
let selectedCountry = '';
let selectedProtocol = '';

const displayNames = new Intl.DisplayNames(['en'], { type: 'region' });

function timedeltaFormat(tdMilliseconds) {
    const secondsTotal = Math.floor(tdMilliseconds / 1000);
    let seconds = secondsTotal;

    const periods = [
        ["year", 60 * 60 * 24 * 365],
        ["month", 60 * 60 * 24 * 30],
        ["day", 60 * 60 * 24],
        ["hour", 60 * 60],
        ["minute", 60],
        ["second", 1],
    ];

    const strings = [];

    for (const [name, duration] of periods) {
        if (seconds >= duration) {
            const value = Math.floor(seconds / duration);
            seconds %= duration;
            strings.push(`${value} ${name}${value > 1 ? "s" : ""}`);
        }
    }

    return strings.join(", ");
}

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
            limit: 12,
            server: {
                url: (prev, page, limit) => {
                    params = `${prev}?limit=${limit}&offset=${page * limit}`

                    if (selectedCountry) {
                        params += '&country_code=' + selectedCountry
                    }

                    if (selectedProtocol) {
                        params += '&protocol=' + selectedProtocol
                    }

                    return params
                }
            }
        },
        server: {
            url: `${window.location.origin}/api/proxy/`,
            then: data => data.proxies.map(proxy => [
                proxy.ip,
                proxy.port,
                proxy.protocol,
                displayNames.of(proxy.geoaddress.country_iso_code) || proxy.geoaddress.country_iso_code,
                proxy.health.latency,
                timedeltaFormat(new Date() - new Date(proxy.health.last_tested))
            ]),
            total: data => data.total
        },
    }).render(document.getElementById("proxy-table"));
}

function loadCountries() {
    fetch(`${window.location.origin}/api/country/`)
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

function fillProtocols() {
    const protocols = ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"];

    const select = document.getElementById("protocol-select");

    const defaultOption = document.createElement("option");
    defaultOption.value = '';
    defaultOption.textContent = 'All';
    select.appendChild(defaultOption);

    protocols.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    loadCountries();
    fillProtocols();
    renderGrid();

    document.getElementById("country-select").addEventListener("change", function () {
        selectedCountry = this.value;
        renderGrid();
    });

    document.getElementById("protocol-select").addEventListener("change", function () {
        selectedProtocol = this.value;
        renderGrid();
    });
});