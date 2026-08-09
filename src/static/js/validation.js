document.getElementById('userForm').addEventListener('submit', function(e) {
    const validateField = (field, min, max, fieldName) => {
        const value = parseInt(field.value);
        if (value < min || value > max) {
            alert(`Введенный Вами параметр (${fieldName}) находится за пределами научных исследований. Пожалуйста, попробуйте ввести другое значение.`);
            field.focus();
            return false;
        }
        return true;
    };

    const ageValid = validateField(document.getElementById('age'), 18, 50, 'Возраст');
    const heightValid = validateField(document.getElementById('height'), 150, 220, 'Рост');
    const weightValid = validateField(document.getElementById('weight'), 40, 200, 'Вес');

    if (!ageValid || !heightValid || !weightValid) {
        e.preventDefault();
    }
});

// Валидация бюджета
document.getElementById('budget').addEventListener('input', function(e) {
    const value = parseInt(e.target.value);
    
    if (value < 0 || isNaN(value)) {
        this.setCustomValidity('Введите положительное число');
    } else {
        this.setCustomValidity('');
    }
});

// Блокировка ввода символов
document.getElementById('budget').addEventListener('keypress', function(e) {
    if (e.key === '-' || e.key === 'e' || e.key === 'E') {
        e.preventDefault();
    }
});
