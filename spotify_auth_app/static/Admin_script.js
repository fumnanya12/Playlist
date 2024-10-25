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
            dashboard.style.display = 'block';
          
            
        }, 1000); // Delay to see the loader for 2 seconds
    } else {
        console.error('Loader or content element not found');
    }
});

    function updatePermission(user_name, isChecked) {
        const data = {
            'user_name': user_name,
            'response': isChecked
        };
        console.log("hello");

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
            // Here you can optionally change the button indicator style if needed
        })
        .catch(error => {
            console.error('Error updating permission:', error);
        });
    }
    document.addEventListener('DOMContentLoaded', function() {
        const userRows = document.querySelectorAll('tr');
        console.log(userRows);
        userRows.forEach((row, index) => {
           // Check if there's a <p> tag in the first <td> before accessing its text
        const userNameElement = row.querySelector('td p');
        
            if (userNameElement) {
            let userName = userNameElement.innerText.trim();
            const switchId = `switch${index}`;
            console.log(userName, switchId);
            userName = encodeURIComponent(userName);

            // Fetch the current permission status for each user
            fetch(`/get_permission_status/${userName}?switchid=${switchId}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Data received:', data); // Log the response to verify
                    const isChecked = data.user_permission === 'Yes';
                    const checkbox = document.getElementById(data.switchid);
                    console.log(checkbox);
                    console.log(isChecked);
                    if (checkbox) {
                        checkbox.checked = isChecked;
                    }
                })
                .catch(error => {
                    console.error('Error fetching permission status:', error);
                });
            }
            else {
                console.error(`User name element not found in row ${index}`);
            }
        });
        
    });
    

