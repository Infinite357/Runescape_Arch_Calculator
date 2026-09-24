const screenshotInput = document.getElementById("screenshotInput");
const analyzeButton = document.getElementById("analyzeButton");
const previewImage = document.getElementById("previewImage");
const statusText = document.getElementById("status");
const resultsDiv = document.getElementById("results");

let uploadedImage = null;

function onOpenCvReady() {
    cvReady = true;
    statusText.textContent = "OpenCV is ready. Upload a screenshot.";
}

window.Module = {
    onRuntimeInitialized() {
        onOpenCvReady();
    }
};

screenshotInput.addEventListener("change", () => {
    const file = screenshotInput.files[0];

    if (!file) {
        return;
    }

    const imageUrl = URL.createObjectURL(file);
    previewImage.src = imageUrl;

    uploadedImage = new Image();uploadedImage.onload = () => {
        statusText.textContent = "Screenshot loaded. Click Analyze.";
    };

    uploadedImage.src = imageUrl;
});

analyzeButton.addEventListener("click", async () => {
    if (!cvReady) {
        statusText.textContent = "OpenCV is still loading. Wait a moment.";
        return;
    }

    if (!uploadedImage) {
        statusText.textContent = "Please upload a screenshot first.";
        return;
    }

    resultsDiv.innerHTML = "";
    statusText.textContent = "Analyzing...";

    const items = await loadItems();

    for (const item of items) {
        const result = await findItemInScreenshot(uploadedImage, item);

        displayResult(item, result);
    }

    statusText.textContent = "Done.";
});

async function loadItems() {
    const response = await fetch("data/items.json");
    return await response.json();
}

function loadImageFromPath(path) {
    return new Promise((resolve) => {
        const img = new Image();
        img.src = path;

        img.onload = () => {
            resolve(img);
        };
    });
}

async function findItemInScreenshot(screenshotImg, item) {
    const templateImg = await loadImageFromPath(item.template);

    const screenshotMat = cv.imread(screenshotImg);
    const templateMat = cv.imread(templateImg);

    const resultCols = screenshotMat.cols - templateMat.cols + 1;
    const resultRows = screenshotMat.rows - templateMat.rows + 1;

    const result = new cv.Mat(resultRows, resultCols, cv.CV_32FC1);

    cv.matchTemplate(
        screenshotMat,
        templateMat,
        result,
        cv.TM_CCOEFF_NORMED
    );

    const minMax = cv.minMaxLoc(result);
    const confidence = minMax.maxVal;
    const location = minMax.maxLoc;

    screenshotMat.delete();
    templateMat.delete();
    result.delete();

    return {
        found: confidence >= 0.75,
        confidence: confidence,
        x: location.x,
        y: location.y
    };
}

function displayResult(item, result) {
    const div = document.createElement("div");

    if (result.found) {
        div.className = "match";
        div.textContent =
            `${item.name} found. Confidence: ${result.confidence.toFixed(3)} at x=${result.x}, y=${result.y}`;
    } else {
        div.className = "no-match";
        div.textContent =
            `${item.name} not found. Confidence: ${result.confidence.toFixed(3)}`;
    }

    resultsDiv.appendChild(div);
}