$(function () {
    $('#changePasswordForm').on('submit', function (e) {
        e.preventDefault();

        const currentPassword = $('#currentPassword').val();
        const newPassword = $('#newPassword').val();
        const confirmPassword = $('#confirmPassword').val();

        if (!currentPassword || !newPassword || !confirmPassword) {
            $('#passwordChangeError').text('All password fields are required.').removeClass('d-none');
            return;
        }

        if (newPassword != confirmPassword) {
            $('#passwordChangeError').text('New password not confirmed.').removeClass('d-none');
            return;
        }

        if (newPassword == currentPassword) {
            $('#passwordChangeError').text('New and current passwords should not match.').removeClass('d-none');
            return;
        }

        $.ajax({
            type: 'POST',
            url: '/api/private/user/change_password',
            contentType: 'application/json',
            data: JSON.stringify({
                old_password: currentPassword,
                new_password: newPassword
            }),
            success: function () {
                window.location.href = '/login';
            },
            error: function (xhr) {
                const message = xhr.responseJSON?.detail || 'Incorrect username or password.';
                $('#passwordChangeError').text(message).removeClass('d-none').addClass('alert-danger');
            }
        });
    });
});