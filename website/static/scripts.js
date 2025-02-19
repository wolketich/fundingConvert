// Event listener for the form submission
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    // Get the file inputs
    const fundingFileInput = document.getElementById('file-funding-input');
    const chickFileInput = document.getElementById('file-chick-input');

    // Create a FormData object and append the files
    const formData = new FormData();
    formData.append('file-funding', fundingFileInput.files[0]);
    formData.append('file-chick', chickFileInput.files[0]);

    // Send the files to the server using fetch
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob()) // Convert response to blob
    .then(blob => {
        // Create a download link for the converted file
        const downloadLink = document.getElementById('download-link');
        const url = window.URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'funding_data_summary.xlsx';
        downloadLink.style.display = 'block'; // Show the download link
        document.getElementById('result').style.display = 'block'; // Show the result section
    })
    .catch(error => {
        console.error('Error:', error); // Log any errors
    });
});