function updatePermission(user_name, response) {
    // Prepare the data to send
    const data = {
        'user_name': user_name,
        'response': response
    };
    console.log("hello");
    // Send an AJAX POST request
    fetch('/submit_permission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log('Permission update success:', result);
        // Optionally, display a message to the user here
    })
    .catch(error => {
        console.error('Error updating permission:', error);
    });
}