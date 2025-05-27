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
            'Last used',
            {
                name: 'Actions',
                formatter: (_, row) => {
                    const name = row.cells[0].data;
                    return gridjs.h('button', {
                        className: 'btn btn-sm btn-danger',
                        onclick: () => handleDeleteSource(name)
                    }, 'Delete');
                }
            }
        ],
        className: {
            table: 'table table-striped table-hover'
        },
        sort: false,
        search: false,
        server: {
            url: `${window.location.origin}/api/private/source/all`,
            then: data => data.map(source => [
                source.name,
                source.uri,
                source.uri_predefined_type,
                source.health.total_conn_attempts + ' / ' + source.health.failed_conn_attempts,
                timedeltaFormat(new Date() - new Date(source.health.last_used))
            ]),
        },
    }).render(document.getElementById("source-table"));
}

function handleAddSource(event) {
    event.preventDefault();

    const name = $('#nameInput').val();
    const url = $('#urlInput').val();
    const type = $('#typeInput').val();

    if (!name || !url || !type) {
        $('#sourceError').text('All fields are required').removeClass('d-none');
        return;
    }

    $.ajax({
        url: `${window.location.origin}/api/private/source/`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            name: name,
            uri: url,
            uri_predefined_type: type,
            type: 1
        }),
        success: function () {
            $('#sourceError').addClass('d-none');
            $('#addSourceForm')[0].reset();
            renderGrid();
        },
        error: function (xhr) {
            if (xhr.status === 422) {
                $('#sourceError').text('Invalid input. Please check the fields.').removeClass('d-none');
            } else if (xhr.status === 409) {
                $('#sourceError').text('Source already exists.').removeClass('d-none');
            } else {
                const message = xhr.responseJSON?.detail || 'An unexpected error occurred.';
                $('#sourceError').text(message).removeClass('d-none');
            }
        }
    });
}

function handleDeleteSource(name) {
    if (!confirm(`Are you sure you want to delete the source "${name}"?`)) return;

    $.ajax({
        url: `${window.location.origin}/api/private/source/`,
        method: 'DELETE',
        contentType: 'application/json',
        data: JSON.stringify({ name }),
        success: function () {
            renderGrid();
        },
        error: function (xhr) {
            const message = xhr.responseJSON?.detail || 'Failed to delete source.';
            $('#sourceError').text(message).removeClass('d-none').addClass('alert-danger');
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    renderGrid();
    $('#addSourceForm').on('submit', handleAddSource);
});