$(document).ready(function () {
    $(".nav-link:contains('Sign out')").on("click", function (e) {
        e.preventDefault();

        $.ajax({
            type: "POST",
            url: "/api/private/auth/logout",
            success: function (response) {
                console.log("Logged out:", response.message);
                window.location.href = "/login";
            },
            error: function (xhr) {
                console.error("Logout failed:", xhr.responseText);
                alert("Failed to log out.");
            }
        });
    });
});