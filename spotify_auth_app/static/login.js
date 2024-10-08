window.addEventListener('load', function() {
    console.log('Page loaded'); // Check if the script is running
    var loader = document.querySelector('.loader-container'); // Updated selector
    var content = document.getElementById('content');
    console.log('Loader:', loader);
    console.log('Content:', content);
    
    if (loader && content) {
        setTimeout(function() {
            loader.style.display = 'none'; // Hide the loader
            content.style.display = 'block'; // Show the content
        }, 2000); // Delay to see the loader for 2 seconds
    } else {
        console.error('Loader or content element not found');
    }
});