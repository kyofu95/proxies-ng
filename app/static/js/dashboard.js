$(document).ready(function () {
    $.get("/api/health/", function (data) {
        $("#statusLabel").text("✔ " + data.status.toUpperCase());
    }).fail(function (xhr, status, error) {
        var errorMessage = xhr.responseJSON ? xhr.responseJSON.detail : "An error occurred";
        $("#statusLabel").text("❗ Error: " + errorMessage);
    });
});