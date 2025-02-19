document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const fundingFileInput = document.getElementById('file-funding-input');
    const chickFileInput = document.getElementById('file-chick-input');
    const formData = new FormData();
    formData.append('file-funding', fundingFileInput.files[0]);
    formData.append('file-chick', chickFileInput.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const downloadLink = document.getElementById('download-link');
        const url = window.URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = 'funding_data_summary.xlsx';
        downloadLink.style.display = 'block';
        document.getElementById('result').style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
    });
});