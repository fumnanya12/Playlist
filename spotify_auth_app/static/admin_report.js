window.addEventListener('load', function() {
    console.log('Page loaded'); // Check if the script is running
    var loader = document.getElementById('loader');
    var content = document.getElementById('content');
    var report = document.getElementById('Report');
    var dashboard = document.getElementById('Modal-content');
    console.log('Loader:', loader);
    console.log('Content:', content);
    console.log('Report:', report);
    console.log('Dashboard:', dashboard);
    
    if (loader && content) {
        setTimeout(function() {
            loader.style.display = 'none'; // Hide the loader
            content.style.display = 'block'; // Show the content
            report.style.display = 'block';
            
        }, 1000); // Delay to see the loader for 2 seconds
    } else {
        console.error('Loader or content element not found');
    }
});


