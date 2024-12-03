window.addEventListener('load', function() {
    console.log('Page loaded'); // Check if the script is running
    var loader = document.getElementById('loader');
    var content = document.getElementById('content');
    var report = document.getElementById('Report');
    console.log('Loader:', loader);
    console.log('Content:', content);
    
    if (loader && content) {
        setTimeout(function() {
            loader.style.display = 'none'; // Hide the loader
            content.style.display = 'block'; // Show the content
            report.style.display = 'block';
        }, 900); // Delay to see the loader for 2 seconds
    } else {
        console.error('Loader or content element not found');
    }
});
document.getElementById("spotifyForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Access the input values
    const spotifyId = document.getElementById("spotifyId").value;
    const email = document.getElementById("email").value;
    console.log(spotifyId, email);

    if (!spotifyId || !email) {
        alert("Both fields are required!");
        return;
    }
    if (!email.includes("@")) {
        alert("Please enter a valid email address.");
        return;
    }
    

    fetch("/submit_spotify_ID", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ spotifyId, email })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to submit data.");
            }
            return response.json();
        })
        .then(data => {
            alert(data.message); // Show success message
            if (data.redirect_url) {
                window.location.href = data.redirect_url; // Redirect based on the backend response
            } else {
                console.log(data.message);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("There was an error submitting your data.");
        });
    
});