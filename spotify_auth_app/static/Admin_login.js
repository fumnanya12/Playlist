
    // Function to remove flash messages after 5 seconds
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(function(message) {
            message.style.display = 'none';
        });
    }, 5000); // 5000ms = 5 seconds

    
