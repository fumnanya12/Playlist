document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('myModal');
    const openModalButton = document.getElementById('openModal');
    const closeModalButton = document.querySelector('.close');
    const yesButton = document.querySelector('.yes-button');
    const noButton = document.querySelector('.no-button');

    // Pre-select the option based on the user's previous response
    const userResponse = document.getElementById('permission-response').getAttribute('data-response');  // Response passed from Flask (Yes/No)
    if (userResponse === 'Yes') {
        yesButton.style.backgroundColor = 'green';  // Highlight Yes button
    } else if (userResponse === 'No') {
        noButton.style.backgroundColor = 'red';  // Highlight No button
    }

    // Open modal
    openModalButton.onclick = function () {
        modal.style.display = 'flex';  // Show modal
    };

    // Close modal
    closeModalButton.onclick = function () {
        modal.style.display = 'none';  // Hide modal
    };

    // Close modal when clicking outside of the content
    window.onclick = function (event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };

    // Function to send POST request with the user's response
    function sendResponseToServer(response) {
        fetch('/submit_permission', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ response: response }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response saved:', data.response);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    // Event listeners for Yes/No buttons
    yesButton.addEventListener('click', function () {
        sendResponseToServer('Yes');
        yesButton.style.backgroundColor = 'green';
        noButton.style.backgroundColor = '';  // Reset No button style
    });

    noButton.addEventListener('click', function () {
        sendResponseToServer('No');
        noButton.style.backgroundColor = 'red';
        yesButton.style.backgroundColor = '';  // Reset Yes button style
    });
});
