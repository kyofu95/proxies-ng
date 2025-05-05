$(function () {
    $('#loginForm').on('submit', function (e) {
        e.preventDefault();

        const username = $('#loginInput').val();
        const password = $('#passwordInput').val();

        if (!username || !password) {
            $('#loginError').text('Username and password are required.').removeClass('d-none');
            return;
        }

        const data = new URLSearchParams();
        data.append('username', username);
        data.append('password', password);

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
                if (xhr.status === 401) {
                    $('#loginError').text('Incorrect username or password.').removeClass('d-none');
                } else {
                    $('#loginError').text('Unexpected error occurred.').removeClass('d-none');
                }
            }
        });
    });
});