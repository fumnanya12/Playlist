// Get modal element
const modal = document.getElementById("myModal");

// Get button that opens the modal
const btn = document.getElementById("openModal");

// Get the <span> element that closes the modal
const closeBtn = document.querySelector(".close");

// When the user clicks the button, open the modal
btn.onclick = function() {
  modal.style.display = "flex"; // Show the modal
}

// When the user clicks on <span> (x), close the modal
closeBtn.onclick = function() {
  modal.style.display = "none"; // Hide the modal
}

// When the user clicks anywhere outside the modal content, close it
window.onclick = function(event) {
  if (event.target === modal) {
    modal.style.display = "none";
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('myModal');
  const openModalButton = document.getElementById('openModal');
  const closeModalButton = document.querySelector('.close');
  const yesButton = document.querySelector('.yes-button');
  const noButton = document.querySelector('.no-button');

  // Pre-select the option based on the user's previous response
  const userResponse = "{{ response }}";  // Response passed from Flask (Yes/No)
  if (userResponse === 'Yes') {
    yesButton.style.backgroundColor = 'green';  // Highlight Yes button
  } else if (userResponse === 'No') {
    noButton.style.backgroundColor = 'red';  // Highlight No button
  }

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
      // Optionally show feedback to the user
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

  // Close the modal if clicked outside
  window.addEventListener('click', function (event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});
