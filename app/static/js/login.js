$(function () {
    $('#loginForm').on('submit', function (e) {
        e.preventDefault();

        const username = $('#loginInput').val();
        const password = $('#passwordInput').val();

        if (!username || !password) {
            $('#loginError').text('Username and password are required.').removeClass('d-none');
            return;
        }

        $.ajax({
            type: 'POST',
            url: '/api/private/auth/login',
            contentType: 'application/json',
            data: JSON.stringify({
                username: username,
                password: password
            }),
            success: function () {
                window.location.href = '/dashboard';
            },
            error: function (xhr) {
                const message = xhr.responseJSON?.detail || 'Incorrect username or password.';
                $('#loginError').text(message).removeClass('d-none');
            }
        });
    });
});