$(document).ready(function() {
    $('form').on('submit', function(event) {
        event.preventDefault(); // Предотвращаем стандартное поведение формы

        $.ajax({
            url: $(this).attr('action'), // URL формы
            method: 'GET',
            data: $(this).serialize(), // Сериализуем данные формы
            success: function(data) {
                $('#cloth-list').html(data.html); // Обновляем содержимое
            },
            error: function(xhr, status, error) {
                console.error('Ошибка при получении данных:', error);
            }
        });
    });
});

// Функция для переключения состояния выпадающего меню
function toggleDropdown(dropdownId) {
    const dropdownContent = document.getElementById(dropdownId);
    dropdownContent.classList.toggle('show'); // Добавляем или убираем класс .show
}

// Закрытие всех меню при клике вне их
document.addEventListener('click', function(event) {
    const dropdownContents = document.querySelectorAll('.dropdown-content');
    const dropdownButtons = document.querySelectorAll('.dropdown-toggle');

    // Закрываем все меню, если клик был вне кнопок и контента
    dropdownContents.forEach(content => {
        if (!content.contains(event.target) && !Array.from(dropdownButtons).some(button => button.contains(event.target))) {
            content.classList.remove('show'); // Закрываем меню
        }
    });
});

