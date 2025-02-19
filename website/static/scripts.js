// Event listener for the form submission
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission

    // Get the file inputs
    const fundingFileInput = document.getElementById('file-funding-input');
    const chickFileInput = document.getElementById('file-chick-input');
    const childrenFileInput = document.getElementById('file-children-input');

    // Create a FormData object and append the files
    const formData = new FormData();
    formData.append('file-funding', fundingFileInput.files[0]);
    formData.append('file-chick', chickFileInput.files[0]);
    formData.append('file-children', childrenFileInput.files[0]);

    // Send the files to the server using fetch
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json()) // Convert response to JSON
    .then(data => {
        if (data.unmatched.length > 0) {
            // Display unmatched names and dropdowns for manual matching
            const unmatchedList = document.getElementById('unmatched-list');
            unmatchedList.innerHTML = ''; // Clear previous content
            data.unmatched.sort().forEach(item => {
                const div = document.createElement('div');
                div.className = 'mb-4 unmatched-item';
                div.innerHTML = `
                    <label class="block text-sm font-medium text-gray-700">${item}</label>
                    <select class="mt-1 block w-full" data-name="${item}">
                        <option value="">-- Select a Match --</option>
                        ${data.possibleMatches.map(match => `<option value="${match['Child ID']}">${match['Full Name']}</option>`).join('')}
                    </select>
                `;
                unmatchedList.appendChild(div);
            });
            document.getElementById('unmatched-names').style.display = 'block';

            // Add event listener to search bar
            document.getElementById('search-bar').addEventListener('input', function() {
                const filter = this.value.toLowerCase();
                document.querySelectorAll('.unmatched-item').forEach(function(item) {
                    const text = item.querySelector('label').textContent.toLowerCase();
                    item.style.display = text.includes(filter) ? '' : 'none';
                });
            });

            // Add event listener to remove selected options from other dropdowns
            document.querySelectorAll('select[data-name]').forEach(select => {
                select.addEventListener('change', function() {
                    const selectedValue = this.value;
                    const selectedName = this.getAttribute('data-name');
                    document.querySelectorAll('select[data-name]').forEach(otherSelect => {
                        if (otherSelect !== this) {
                            otherSelect.querySelector(`option[value="${selectedValue}"]`).remove();
                        }
                    });
                    if (selectedValue) {
                        const label = this.previousElementSibling;
                        label.classList.add('text-green-600');
                        label.innerHTML += ` (Matched with ${selectedValue})`;
                        this.setAttribute('disabled', 'true');
                    }
                });
            });
        } else {
            // If no unmatched names, directly show the result
            const downloadLink = document.getElementById('download-link');
            downloadLink.href = data.fileUrl;
            downloadLink.download = 'funding_data_summary.xlsx';
            downloadLink.style.display = 'block';
            document.getElementById('result').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error); // Log any errors
    });
});

// Event listener for the finalize button
document.getElementById('finalize-button').addEventListener('click', function() {
    const unmatchedSelects = document.querySelectorAll('#unmatched-list select');
    const matches = Array.from(unmatchedSelects).map(select => ({
        name: select.getAttribute('data-name'),
        id: select.value
    }));

    fetch('/finalize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ matches })
    })
    .then(response => response.json())
    .then(data => {
        const downloadLink = document.getElementById('download-link');
        downloadLink.href = data.fileUrl;
        downloadLink.download = 'funding_data_summary.xlsx';
        downloadLink.style.display = 'block';
        document.getElementById('result').style.display = 'block';
        document.getElementById('unmatched-names').style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error); // Log any errors
    });
});