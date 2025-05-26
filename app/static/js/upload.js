document.addEventListener('DOMContentLoaded', function () {
  const fileInput = document.getElementById('file-input');
  const fileLabel = document.getElementById('file-label');
  const previewArea = document.getElementById('preview-area');
  const filePreview = document.getElementById('file-preview');
  const dropArea = document.getElementById('drop-area');
  const browseBtn = document.getElementById("browse-btn");

  browseBtn.addEventListener("click", () => {
    fileInput.click();
  });


  // Handle file selection
  fileInput.addEventListener('change', function () {
    if (fileInput.files.length > 0) {
      const file = fileInput.files[0];
      if (file.size > 5 * 1024 * 1024) {
        showError('file-size-error');
        return;
      }
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        showError('file-type-error');
        return;
      }
      fileLabel.textContent = file.name;
      previewFile(file);
    } else {
      showError('file-empty-error');
    }
  });

  // Handle drag & drop
  dropArea.addEventListener('dragover', function (e) {
    e.preventDefault();
    dropArea.classList.add('drag-over');
  });

  dropArea.addEventListener('dragleave', function () {
    dropArea.classList.remove('drag-over');
  });

  dropArea.addEventListener('drop', function (e) {
    e.preventDefault();
    dropArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.size > 5 * 1024 * 1024) {
        showError('file-size-error');
        return;
      }
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        showError('file-type-error');
        return;
      }
      fileLabel.textContent = file.name;
      previewFile(file);
    } else {
      showError('file-empty-error');
    }
  });

  // Preview the selected file
  function previewFile(file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      filePreview.src = e.target.result;
      filePreview.classList.remove('hidden');
      previewArea.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  }

  // Show error message
  function showError(id
  ) {
    document.querySelectorAll('.alert').forEach(el => el.classList.add('d-none'));
    document.getElementById(id).classList.remove('d-none');
    filePreview.classList.add('hidden');
    previewArea.classList.add('hidden');
  }
  // Enable start button when file is selected
  fileInput.addEventListener('change', function () {
    const startBtn = document.getElementById('start-btn');
    if (fileInput.files.length > 0) {
      startBtn.disabled = false;
    } else {
      startBtn.disabled = true;
    }
  });
});

