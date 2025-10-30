function updateCorrectChoice(checkbox) {
    const allCheckboxes = document.querySelectorAll('.correct-choice');
    allCheckboxes.forEach(cb => {
        if (cb !== checkbox) {
            cb.checked = false;
        }
    });

    const choiceItem = checkbox.closest('.choice-item');
    const allItems = document.querySelectorAll('.choice-item');
    allItems.forEach(item => item.classList.remove('correct'));

    if (checkbox.checked) {
        choiceItem.classList.add('correct');
    }
}

function addChoice() {
    const choiceCount = document.querySelectorAll('.choice-item').length;
    if (choiceCount < 6) {
        console.log('Add new choice');
    }
}

function removeChoice(button) {
    const choiceItem = button.closest('.choice-item');
    choiceItem.remove();
}

function updateChoiceOrders() {
    const choiceItems = document.querySelectorAll('.choice-item');
    choiceItems.forEach((item, index) => {
        const orderInput = item.querySelector('.choice-order');
        if (orderInput) {
            orderInput.value = index;
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    updateChoiceOrders();

    document.querySelectorAll('.correct-choice').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateCorrectChoice(this);
        });

        if (checkbox.checked) {
            updateCorrectChoice(checkbox);
        }
    });
});
