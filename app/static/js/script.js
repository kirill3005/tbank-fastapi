async function regFunction(event) {
    event.preventDefault();  // Предотвращаем стандартное действие формы

    // Получаем форму и собираем данные из неё
    const form = document.getElementById('registration-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/user/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        // Проверяем успешность ответа
        if (!response.ok) {
            // Получаем данные об ошибке
            const errorData = await response.json();
            displayErrors(errorData);  // Отображаем ошибки
            return;  // Прерываем выполнение функции
        }

        const result = await response.json();

        if (result.message) {  // Проверяем наличие сообщения о успешной регистрации
            window.location.href = '/user/profile';  // Перенаправляем пользователя на страницу логина
        } else {
            alert(result.message || 'Неизвестная ошибка');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.');
    }
}

// Функция для отображения ошибок
function displayErrors(errorData) {
    let message = 'Произошла ошибка';

    if (errorData && errorData.detail) {
        if (Array.isArray(errorData.detail)) {
            // Обработка массива ошибок
            message = errorData.detail.map(error => {
                if (error.type === 'string_too_short') {
                    return `Поле "${error.loc[1]}" должно содержать минимум ${error.ctx.min_length} символов.`;
                }
                return error.msg || 'Произошла ошибка';
            }).join('\n');
        } else {
            // Обработка одиночной ошибки
            message = errorData.detail || 'Произошла ошибка';
        }
    }

    // Отображение сообщения об ошибке
    alert(message);
}

async function loginFunction(event, conv_id) {
    event.preventDefault();  // Предотвращаем стандартное действие формы

    // Получаем форму и собираем данные из неё
    const form = document.getElementById('login-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await fetch('/user/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        // Проверяем успешность ответа
        if (!response.ok) {
            // Получаем данные об ошибке
            const errorData = await response.json();
            displayErrors(errorData);  // Отображаем ошибки
            return;  // Прерываем выполнение функции
        }

        const result = await response.json();

        if (result.message) {  // Проверяем наличие сообщения о успешной регистрации
            const conv = await fetch('http://api.fusionfind.ru/new_conversation?api_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzM1OTcwMTI0fQ.pyRntCTCRnGJM1t9wafVwBtiSGGOULGAhNRioLIY6aI&db_token=MS05ZUl0ZktDLXpGeGVOTFNyZE5uZmFBPT0',
                {method: "POST",
                    headers: {
                        'Content-Type': 'application/json'
                    },
                body: ''
                });
            const jsn = await conv.json();
            const conv_id = jsn.conv_id;
            window.location.href = '/user/profile';  // Перенаправляем пользователя на страницу логина
        } else {
            alert(result.message || 'Неизвестная ошибка');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при входе. Пожалуйста, попробуйте снова.');
    }
}
async function logoutFunction() {
    try {
        // Отправка POST-запроса для удаления куки на сервере
        let response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Проверка ответа сервера
        if (response.ok) {
            // Перенаправляем пользователя на страницу логина
            window.location.href = '/user/login';
        } else {
            // Чтение возможного сообщения об ошибке от сервера
            const errorData = await response.json();
            console.error('Ошибка при выходе:', errorData.message || response.statusText);
        }
    } catch (error) {
        console.error('Ошибка сети', error);
    }
}

async function buy_tokens(event) {
        event.preventDefault();
        const input = document.getElementById('tokenAmount');
        let count = parseInt(input.value);

        try {
            const response = await fetch('/user/buy_tokens', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({'tokens': count})
            });

            // Проверяем успешность ответа
            if (!response.ok) {
                // Получаем данные об ошибке
                const errorData = await response.json();
                displayErrors(errorData);  // Отображаем ошибки
                return;  // Прерываем выполнение функции
            }

            const result = await response.json();

            if (result.message) {  // Проверяем наличие сообщения о успешной регистрации
                window.location.href = '/user/profile';  // Перенаправляем пользователя на страницу логина
            } else {
                alert(result.message || 'Неизвестная ошибка');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Произошла ошибка. Пожалуйста, попробуйте снова.' + error);
        }
    }



async function newProject(event) {
    event.preventDefault();  // Предотвращаем стандартное действие формы

    // Получаем форму и собираем данные из неё
    const form = document.getElementById('db-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const loader = document.getElementById('loader');
    loader.style.display = 'flex';

    try {
        const response = await fetch('/user/new_project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        // Проверяем успешность ответа
        if (!response.ok) {
            // Получаем данные об ошибке
            const errorData = await response.json();
            displayErrors(errorData);  // Отображаем ошибки
            return;  // Прерываем выполнение функции
        }

        const result = await response.json();

        if (result.message) {  // Проверяем наличие сообщения о успешной регистрации
            loader.style.display = 'none';
            window.location.href = '/user/profile';  // Перенаправляем пользователя на страницу логина
        } else {
            alert(result.message || 'Неизвестная ошибка');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при входе. Пожалуйста, попробуйте снова.');
    }
}