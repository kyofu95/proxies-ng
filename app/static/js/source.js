let gridInstance = null;

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
            'Name',
            'URL',
            'Type',
            'Total conn',
            'Last used'
        ],
        className: {
            table: 'table table-striped table-hover'
        },
        sort: false,
        search: false,
        server: {
            url: `${window.location.origin}/api/private/source/all/`,
            then: data => data.map(source => [
                source.name,
                source.uri,
                source.uri_predefined_type,
                source.health.total_conn_attemps + ' / ' + source.health.failed_conn_attemps,
                timedeltaFormat(new Date() - new Date(source.health.last_used))
            ]),
        },
    }).render(document.getElementById("source-table"));
}

document.addEventListener("DOMContentLoaded", function () {
    renderGrid();
});