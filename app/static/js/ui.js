document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("upload-form");
    const startBtn = document.getElementById("start-btn");

    const statusCard = document.getElementById("status-card");
    const spinner = document.getElementById("status-spinner");
    const resultSection = document.getElementById("result-section");
    const resultImage = document.getElementById("result-image");
    const downloadBtn = document.getElementById("download-btn");
    const errorAlert = document.getElementById("error-msg");

    startBtn.addEventListener("click", async () => {
        startBtn.disabled = true;

        // Reset UI
        errorAlert.classList.add("d-none");
        resultSection.classList.add("d-none");
        spinner.classList.remove("d-none");
        statusCard.classList.remove("d-none");

        const data = new FormData(form);

        try {
            const resp = await fetch("/process", { method: "POST", body: data });
            if (!resp.ok) throw new Error(`Upload failed: ${resp.status}`);
            const { processing_id } = await resp.json();

            const check = setInterval(async () => {
                const s = await fetch(`/status/${processing_id}`);
                const js = await s.json();

                if (js.status === "completed") {
                    clearInterval(check);
                    spinner.classList.add("d-none");
                    resultImage.src = `/download/${processing_id}`;
                    downloadBtn.href = `/download/${processing_id}`;
                    resultSection.classList.remove("d-none");
                } else if (js.status === "failed") {
                    clearInterval(check);
                    spinner.classList.add("d-none");
                    errorAlert.textContent = "Processing failed.";
                    errorAlert.classList.remove("d-none");
                }
            }, 2000);
        } catch (err) {
            spinner.classList.add("d-none");
            errorAlert.textContent = err.message;
            errorAlert.classList.remove("d-none");
        }
    });
});
