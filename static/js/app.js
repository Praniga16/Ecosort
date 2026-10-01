/**
 * ============================================================
 * EcoSort AI - Complete Frontend Controller
 * ============================================================
 * Features:
 * - Image upload
 * - Drag and drop
 * - Image preview
 * - Waste prediction
 * - Live camera
 * - Camera capture
 * - Automatic prediction
 * - History page
 * - Analytics page
 * - Mobile navigation
 * - Toast notifications
 * ============================================================
 */


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let selectedFile = null;
let cameraStream = null;


/* ============================================================
   PAGE INITIALIZATION
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    // Lucide icons
    if (window.lucide) {
        try {
            lucide.createIcons();
        } catch (error) {
            console.warn("Lucide icons could not initialize:", error);
        }
    }

    // Mobile navigation
    setupMobileNav();

    // Scanner page
    if (document.getElementById("dropzone")) {
        initScanner();
    }

    // History page
    if (document.getElementById("historyTableBody")) {
        initHistoryPage();
    }

    // Analytics page
    if (document.getElementById("categoryChart")) {
        initAnalyticsPage();
    }

});


/* ============================================================
   TOAST NOTIFICATIONS
   ============================================================ */

function showToast(message, type = "info") {

    let container =
        document.getElementById("toastContainer");

    if (!container) {

        container =
            document.createElement("div");

        container.id =
            "toastContainer";

        container.className =
            "toast-container";

        document.body.appendChild(container);
    }


    const icons = {

        success: "✓",

        error: "✕",

        warning: "⚠",

        info: "ℹ"

    };


    const toast =
        document.createElement("div");

    toast.className =
        `toast toast-${type}`;


    toast.innerHTML = `

        <span class="toast-icon">
            ${icons[type] || "ℹ"}
        </span>

        <span class="toast-message">
            ${message}
        </span>

    `;


    container.appendChild(toast);


    setTimeout(function () {

        toast.style.opacity = "0";

        toast.style.transform =
            "translateX(100%)";

        toast.style.transition =
            "all 0.3s ease";


        setTimeout(function () {

            toast.remove();

        }, 300);

    }, 4000);

}


/* ============================================================
   MOBILE NAVIGATION
   ============================================================ */

function setupMobileNav() {

    const toggleBtn =
        document.getElementById(
            "mobileToggle"
        );

    const sidebar =
        document.getElementById(
            "sidebar"
        );


    if (
        toggleBtn &&
        sidebar
    ) {

        toggleBtn.addEventListener(
            "click",
            function () {

                sidebar.classList.toggle(
                    "mobile-open"
                );

            }
        );

    }

}


/* ============================================================
   SCANNER INITIALIZATION
   ============================================================ */

function initScanner() {

    const dropzone =
        document.getElementById(
            "dropzone"
        );

    const fileInput =
        document.getElementById(
            "fileInput"
        );

    const browseBtn =
        document.getElementById(
            "browseBtn"
        );

    const analyzeBtn =
        document.getElementById(
            "analyzeBtn"
        );

    const removeBtn =
        document.getElementById(
            "removeBtn"
        );

    const startCameraBtn =
        document.getElementById(
            "startCameraInlineBtn"
        );

    const captureBtn =
        document.getElementById(
            "captureBtnInline"
        );

    const stopCameraBtn =
        document.getElementById(
            "stopCameraInlineBtn"
        );


    /* --------------------------------------------------------
       FILE UPLOAD
       -------------------------------------------------------- */

    if (
        browseBtn &&
        fileInput
    ) {

        browseBtn.addEventListener(
            "click",
            function () {

                fileInput.click();

            }
        );


        fileInput.addEventListener(
            "change",
            function (event) {

                if (
                    event.target.files &&
                    event.target.files.length > 0
                ) {

                    handleFileSelection(
                        event.target.files[0]
                    );

                }

            }
        );

    }


    /* --------------------------------------------------------
       DRAG & DROP
       -------------------------------------------------------- */

    if (dropzone) {

        [
            "dragenter",
            "dragover"
        ].forEach(function (eventName) {

            dropzone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();

                    dropzone.classList.add(
                        "drag-over"
                    );

                }
            );

        });


        [
            "dragleave",
            "drop"
        ].forEach(function (eventName) {

            dropzone.addEventListener(
                eventName,
                function (event) {

                    event.preventDefault();

                    dropzone.classList.remove(
                        "drag-over"
                    );

                }
            );

        });


        dropzone.addEventListener(
            "drop",
            function (event) {

                if (
                    event.dataTransfer &&
                    event.dataTransfer.files &&
                    event.dataTransfer.files.length > 0
                ) {

                    handleFileSelection(
                        event.dataTransfer.files[0]
                    );

                }

            }
        );

    }


    /* --------------------------------------------------------
       ANALYZE BUTTON
       -------------------------------------------------------- */

    if (analyzeBtn) {

        analyzeBtn.addEventListener(
            "click",
            analyzeImage
        );

    }


    /* --------------------------------------------------------
       REMOVE BUTTON
       -------------------------------------------------------- */

    if (removeBtn) {

        removeBtn.addEventListener(
            "click",
            resetScan
        );

    }


    /* --------------------------------------------------------
       CAMERA BUTTONS
       -------------------------------------------------------- */

    /*
       IMPORTANT:
       There is ONLY ONE listener for each
       camera button.
    */

    if (startCameraBtn) {

        startCameraBtn.addEventListener(
            "click",
            startInlineCamera
        );

    }


    if (captureBtn) {

        captureBtn.addEventListener(
            "click",
            captureInlinePhoto
        );

    }


    if (stopCameraBtn) {

        stopCameraBtn.addEventListener(
            "click",
            stopInlineCamera
        );

    }


    /* --------------------------------------------------------
       SCANNER TABS
       -------------------------------------------------------- */

    const tabButtons =
        document.querySelectorAll(
            "#scannerTabs .tab-btn"
        );


    tabButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const target =
                        button.dataset.tab;

                    switchScannerTab(
                        target
                    );

                }
            );

        }
    );

}


/* ============================================================
   SCANNER TAB SWITCHING
   ============================================================ */

function switchScannerTab(targetId) {

    const tabButtons =
        document.querySelectorAll(
            "#scannerTabs .tab-btn"
        );

    const panels =
        document.querySelectorAll(
            ".tab-panel"
        );


    tabButtons.forEach(
        function (button) {

            button.classList.toggle(
                "active",
                button.dataset.tab === targetId
            );

        }
    );


    panels.forEach(
        function (panel) {

            panel.classList.toggle(
                "active",
                panel.id === targetId
            );

        }
    );


    /*
       If user leaves camera tab,
       safely stop camera.
    */

    if (
        targetId !== "cameraTab" &&
        cameraStream
    ) {

        stopInlineCamera();

    }

}


/* ============================================================
   FILE VALIDATION
   ============================================================ */

function handleFileSelection(file) {

    if (!file) {
        return;
    }


    const validTypes = [

        "image/jpeg",

        "image/jpg",

        "image/png",

        "image/webp"

    ];


    const maxSize =
        10 * 1024 * 1024;


    if (
        !validTypes.includes(
            file.type
        )
    ) {

        showToast(
            "Please upload a valid JPG, PNG, or WEBP image.",
            "error"
        );

        return;
    }


    if (
        file.size > maxSize
    ) {

        showToast(
            "File size exceeds the 10 MB limit.",
            "error"
        );

        return;
    }


    selectedFile =
        file;


    previewImage(
        file
    );

}


/* ============================================================
   IMAGE PREVIEW
   ============================================================ */

function previewImage(file) {

    const dropzone =
        document.getElementById(
            "dropzone"
        );

    const previewContainer =
        document.getElementById(
            "previewContainer"
        );

    const previewImg =
        document.getElementById(
            "previewImg"
        );

    const fileNameDisplay =
        document.getElementById(
            "fileNameDisplay"
        );

    const fileSizeDisplay =
        document.getElementById(
            "fileSizeDisplay"
        );


    if (
        !previewImg ||
        !previewContainer
    ) {

        return;
    }


    const reader =
        new FileReader();


    reader.onload =
        function (event) {

            previewImg.src =
                event.target.result;


            if (fileNameDisplay) {

                fileNameDisplay.textContent =
                    file.name;

            }


            if (fileSizeDisplay) {

                fileSizeDisplay.textContent =
                    (
                        file.size /
                        (
                            1024 * 1024
                        )
                    ).toFixed(2) +
                    " MB";

            }


            if (dropzone) {

                dropzone.style.display =
                    "none";

            }


            previewContainer.classList.add(
                "active"
            );


            hideResult();

        };


    reader.readAsDataURL(
        file
    );

}


/* ============================================================
   RESET SCAN
   ============================================================ */

function resetScan() {

    selectedFile =
        null;


    const dropzone =
        document.getElementById(
            "dropzone"
        );

    const previewContainer =
        document.getElementById(
            "previewContainer"
        );

    const fileInput =
        document.getElementById(
            "fileInput"
        );


    if (fileInput) {

        fileInput.value =
            "";

    }


    if (dropzone) {

        dropzone.style.display =
            "flex";

    }


    if (previewContainer) {

        previewContainer.classList.remove(
            "active"
        );

    }


    hideResult();

}


/* ============================================================
   AI IMAGE ANALYSIS
   ============================================================ */

async function analyzeImage() {

    if (!selectedFile) {

        showToast(
            "Please select or capture an image first.",
            "warning"
        );

        return;
    }


    const scanningOverlay =
        document.getElementById(
            "scanningOverlay"
        );

    const analyzeBtn =
        document.getElementById(
            "analyzeBtn"
        );


    if (scanningOverlay) {

        scanningOverlay.classList.add(
            "active"
        );

    }


    if (analyzeBtn) {

        analyzeBtn.disabled =
            true;

    }


    const formData =
        new FormData();


    /*
       Flask expects the field name "image".
    */

    formData.append(
        "image",
        selectedFile
    );


    try {

        const response =
            await fetch(
                "/predict",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (scanningOverlay) {

            scanningOverlay.classList.remove(
                "active"
            );

        }


        if (analyzeBtn) {

            analyzeBtn.disabled =
                false;

        }


        if (
            !response.ok ||
            !data.success
        ) {

            if (
                data.model_loaded === false
            ) {

                showToast(
                    data.error ||
                    "AI model is not trained.",
                    "warning"
                );


                showModelNotTrainedResult(
                    data.error
                );

            }

            else {

                showToast(
                    data.error ||
                    "Unable to analyze image.",
                    "error"
                );

            }


            return;
        }


        showToast(
            "Classification complete!",
            "success"
        );


        showResult(
            data
        );


        updateStatistics();

    }

    catch (error) {

        console.error(
            "Prediction error:",
            error
        );


        if (scanningOverlay) {

            scanningOverlay.classList.remove(
                "active"
            );

        }


        if (analyzeBtn) {

            analyzeBtn.disabled =
                false;

        }


        showToast(
            "Network or server error occurred.",
            "error"
        );

    }

}


/* ============================================================
   SHOW AI RESULT
   ============================================================ */

function showResult(data) {

    const placeholder =
        document.getElementById(
            "resultPlaceholder"
        );

    const content =
        document.getElementById(
            "resultContent"
        );


    if (placeholder) {

        placeholder.style.display =
            "none";

    }


    if (!content) {

        return;
    }


    const emoji =
        document.getElementById(
            "resEmoji"
        );

    const name =
        document.getElementById(
            "resName"
        );

    const category =
        document.getElementById(
            "resCategory"
        );

    const confidence =
        document.getElementById(
            "resConfidence"
        );

    const advice =
        document.getElementById(
            "resAdvice"
        );


    if (emoji) {

        emoji.textContent =
            data.icon ||
            "♻️";

    }


    if (name) {

        name.textContent =
            data.name ||
            data.class ||
            "Unknown";

    }


    if (category) {

        category.textContent =
            data.category ||
            "Unknown";


        category.className =
            "result-category-tag " +
            (
                data.category ===
                "Recyclable"
                    ? "recyclable"
                    : "general-waste"
            );

    }


    if (confidence) {

        const confidenceValue =
            Number(
                data.confidence || 0
            );


        confidence.textContent =
            confidenceValue.toFixed(1) +
            "%";

    }


    if (advice) {

        advice.textContent =
            data.advice ||
            "Follow local waste disposal guidelines.";

    }


    /*
       Confidence message
    */

    const alertBox =
        document.getElementById(
            "confidenceAlert"
        );


    if (alertBox) {

        const confidenceValue =
            Number(
                data.confidence || 0
            );


        let level =
            "high";


        if (
            confidenceValue < 60
        ) {

            level =
                "low";

        }

        else if (
            confidenceValue < 80
        ) {

            level =
                "moderate";

        }


        alertBox.className =
            `confidence-alert ${level}`;


        alertBox.innerHTML = `

            <span>
                ●
                ${
                    data.confidence_level ||
                    (
                        level === "high"
                            ? "High Confidence"
                            : level === "moderate"
                                ? "Moderate Confidence"
                                : "Low Confidence"
                    )
                }
            </span>

            ${
                data.confidence_tip
                    ? `
                        <span
                            style="
                                font-size:0.8rem;
                                opacity:0.9;
                            "
                        >
                            (${data.confidence_tip})
                        </span>
                    `
                    : ""
            }

        `;

    }


    /*
       Probability scores
    */

    const probabilityList =
        document.getElementById(
            "probabilitiesList"
        );


    if (
        probabilityList &&
        data.scores
    ) {

        probabilityList.innerHTML =
            "";


        let probabilityItems =
            [];


        /*
           New format:
           [
             {
               name: "plastic",
               probability: 92
             }
           ]
        */

        if (
            Array.isArray(
                data.scores
            )
        ) {

            probabilityItems =
                data.scores.map(
                    function (item) {

                        return {

                            name:
                                item.name ||
                                item.class ||
                                "Unknown",

                            probability:
                                Number(
                                    item.probability ||
                                    item.score ||
                                    0
                                )

                        };

                    }
                );

        }

        /*
           Old format:
           {
              plastic: 92,
              paper: 4
           }
        */

        else {

            probabilityItems =
                Object.entries(
                    data.scores
                ).map(
                    function (
                        [
                            name,
                            value
                        ]
                    ) {

                        return {

                            name:
                                name,

                            probability:
                                Number(
                                    value ||
                                    0
                                )

                        };

                    }
                );

        }


        probabilityItems.sort(
            function (a, b) {

                return (
                    b.probability -
                    a.probability
                );

            }
        );


        probabilityItems.forEach(
            function (
                item,
                index
            ) {

                const percentage =
                    Math.max(
                        0,
                        Math.min(
                            100,
                            item.probability
                        )
                    );


                const element =
                    document.createElement(
                        "div"
                    );


                element.className =
                    "prob-item";


                const displayName =
                    String(
                        item.name
                    );


                element.innerHTML = `

                    <div class="prob-meta">

                        <span>
                            ${
                                displayName
                                    .charAt(0)
                                    .toUpperCase()
                                +
                                displayName
                                    .slice(1)
                            }
                        </span>

                        <span>
                            ${percentage.toFixed(1)}%
                        </span>

                    </div>


                    <div class="prob-bar-bg">

                        <div
                            class="prob-bar-fill ${
                                index === 0
                                    ? "top"
                                    : ""
                            }"
                            style="
                                width:${percentage}%;
                            "
                        ></div>

                    </div>

                `;


                probabilityList.appendChild(
                    element
                );

            }
        );

    }


    content.classList.add(
        "active"
    );

}


/* ============================================================
   MODEL NOT TRAINED RESULT
   ============================================================ */

function showModelNotTrainedResult(
    errorMsg
) {

    const placeholder =
        document.getElementById(
            "resultPlaceholder"
        );

    const content =
        document.getElementById(
            "resultContent"
        );


    if (placeholder) {

        placeholder.style.display =
            "none";

    }


    if (!content) {

        return;
    }


    content.innerHTML = `

        <div
            style="
                background:rgba(
                    245,
                    158,
                    11,
                    0.1
                );

                border:1px solid #F59E0B;

                padding:24px;

                border-radius:14px;

                text-align:center;
            "
        >

            <div
                style="
                    font-size:2.5rem;
                    margin-bottom:12px;
                "
            >
                ⚠️
            </div>


            <h3
                style="
                    color:#F59E0B;
                    font-size:1.2rem;
                    margin-bottom:8px;
                "
            >
                Model Not Trained Yet
            </h3>


            <p
                style="
                    font-size:0.9rem;
                    color:#6B7D76;
                    margin-bottom:16px;
                "
            >
                ${
                    errorMsg ||
                    "Please train the MobileNetV2 model using python train.py."
                }
            </p>


            <code
                style="
                    background:#041F17;
                    color:#2DD496;
                    padding:6px 14px;
                    border-radius:6px;
                    font-size:0.85rem;
                "
            >
                python train.py
            </code>

        </div>

    `;


    content.classList.add(
        "active"
    );

}


/* ============================================================
   HIDE RESULT
   ============================================================ */

function hideResult() {

    const placeholder =
        document.getElementById(
            "resultPlaceholder"
        );

    const content =
        document.getElementById(
            "resultContent"
        );


    if (placeholder) {

        placeholder.style.display =
            "flex";

    }


    if (content) {

        content.classList.remove(
            "active"
        );

    }

}


/* ============================================================
   LIVE CAMERA
   ============================================================ */

async function startInlineCamera() {

    const video =
        document.getElementById(
            "cameraVideoInline"
        );

    const viewport =
        document.getElementById(
            "cameraViewportInline"
        );

    const inactive =
        document.getElementById(
            "cameraInactiveMsg"
        );

    const captureBtn =
        document.getElementById(
            "captureBtnInline"
        );

    const stopBtn =
        document.getElementById(
            "stopCameraInlineBtn"
        );

    const controls =
        document.getElementById(
            "cameraControlsInline"
        );


    /*
       Check video element.
    */

    if (!video) {

        showToast(
            "Camera preview is unavailable.",
            "error"
        );

        return;
    }


    /*
       Check browser support.
    */

    if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia
    ) {

        showToast(
            "Your browser does not support camera access.",
            "error"
        );

        return;
    }


    /*
       If an old stream exists,
       stop it first.
    */

    if (cameraStream) {

        stopInlineCamera();

    }


    try {

        /*
           SIMPLE CAMERA REQUEST.

           Do NOT use:
           facingMode
           fixed width
           fixed height

           This makes the application
           compatible with more Windows webcams.
        */

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: true,

                audio: false

            });


        /*
           Attach stream to visible video.
        */

        video.srcObject =
            cameraStream;


        video.autoplay =
            true;

        video.muted =
            true;

        video.playsInline =
            true;


        /*
           Make sure camera panel is active.
        */

        if (viewport) {

            viewport.classList.add(
                "active"
            );

        }


        if (inactive) {

            inactive.style.display =
                "none";

        }


        /*
           Show controls.
        */

        if (controls) {

            controls.style.display =
                "flex";

        }


        if (captureBtn) {

            captureBtn.style.display =
                "inline-flex";

        }


        if (stopBtn) {

            stopBtn.style.display =
                "inline-flex";

        }


        /*
           Start playback.
        */

        await video.play();


        /*
           Wait until metadata is available.
        */

        video.onloadedmetadata =
            function () {

                video.play()
                    .catch(
                        function (error) {

                            console.warn(
                                "Video playback:",
                                error
                            );

                        }
                    );

            };


        console.log(
            "Camera started:",
            video.videoWidth,
            "x",
            video.videoHeight
        );


        showToast(
            "Camera is ready. Position the waste inside the frame.",
            "success"
        );

    }

    catch (error) {

        console.error(
            "CAMERA ERROR:",
            error
        );


        /*
           Clean up.
        */

        if (cameraStream) {

            cameraStream
                .getTracks()
                .forEach(
                    function (track) {

                        track.stop();

                    }
                );

            cameraStream =
                null;

        }


        /*
           Specific error messages.
        */

        if (
            error.name ===
            "NotAllowedError"
        ) {

            showToast(
                "Camera permission was denied. Click the camera icon in Chrome and select Allow.",
                "error"
            );

        }

        else if (
            error.name ===
            "NotFoundError"
        ) {

            showToast(
                "No camera was found on this computer.",
                "error"
            );

        }

        else if (
            error.name ===
            "NotReadableError"
        ) {

            showToast(
                "The camera is being used by another application. Close Camera, Teams, Zoom, or Meet.",
                "error"
            );

        }

        else if (
            error.name ===
            "SecurityError"
        ) {

            showToast(
                "Chrome blocked camera access for this page.",
                "error"
            );

        }

        else {

            showToast(
                "Unable to open camera: " +
                error.name,
                "error"
            );

        }

    }

}


/* ============================================================
   STOP CAMERA
   ============================================================ */

function stopInlineCamera() {

    const video =
        document.getElementById(
            "cameraVideoInline"
        );

    const viewport =
        document.getElementById(
            "cameraViewportInline"
        );

    const inactive =
        document.getElementById(
            "cameraInactiveMsg"
        );

    const captureBtn =
        document.getElementById(
            "captureBtnInline"
        );

    const stopBtn =
        document.getElementById(
            "stopCameraInlineBtn"
        );

    const controls =
        document.getElementById(
            "cameraControlsInline"
        );


    /*
       Stop all tracks.
    */

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                function (track) {

                    track.stop();

                }
            );

        cameraStream =
            null;

    }


    /*
       Disconnect video.
    */

    if (video) {

        video.pause();

        video.srcObject =
            null;

    }


    /*
       Restore inactive screen.
    */

    if (viewport) {

        viewport.classList.remove(
            "active"
        );

    }


    if (inactive) {

        inactive.style.display =
            "flex";

    }


    if (captureBtn) {

        captureBtn.style.display =
            "none";

    }


    if (stopBtn) {

        stopBtn.style.display =
            "none";

    }


    if (controls) {

        controls.style.display =
            "none";

    }

}


/* ============================================================
   CAPTURE CAMERA IMAGE
   ============================================================ */

function captureInlinePhoto() {

    const video =
        document.getElementById(
            "cameraVideoInline"
        );


    /*
       Camera must be running.
    */

    if (
        !video ||
        !cameraStream
    ) {

        showToast(
            "Start the camera before capturing an image.",
            "warning"
        );

        return;
    }


    /*
       Camera must have a frame.
    */

    if (
        !video.videoWidth ||
        !video.videoHeight
    ) {

        showToast(
            "Camera is still starting. Please wait a moment.",
            "warning"
        );

        return;
    }


    /*
       Create canvas.
    */

    const canvas =
        document.createElement(
            "canvas"
        );


    canvas.width =
        video.videoWidth;


    canvas.height =
        video.videoHeight;


    const context =
        canvas.getContext(
            "2d"
        );


    /*
       Capture current frame.
    */

    context.drawImage(

        video,

        0,

        0,

        canvas.width,

        canvas.height

    );


    /*
       Convert to JPG.
    */

    canvas.toBlob(

        function (blob) {

            if (!blob) {

                showToast(
                    "Could not capture camera image.",
                    "error"
                );

                return;
            }


            const file =
                new File(

                    [blob],

                    `camera_capture_${Date.now()}.jpg`,

                    {
                        type:
                            "image/jpeg"
                    }

                );


            /*
               Save as selected file.
            */

            selectedFile =
                file;


            /*
               Stop camera.
            */

            stopInlineCamera();


            /*
               Switch to Upload tab.
            */

            switchScannerTab(
                "uploadTab"
            );


            /*
               Show captured image.
            */

            handleFileSelection(
                file
            );


            /*
               Automatically analyze.
            */

            setTimeout(
                function () {

                    analyzeImage();

                },
                250
            );


            showToast(
                "Photo captured. Analyzing waste...",
                "success"
            );

        },

        "image/jpeg",

        0.92

    );

}


/* ============================================================
   REAL-TIME STATISTICS
   ============================================================ */

async function updateStatistics() {

    try {

        const response =
            await fetch(
                "/api/stats"
            );


        const data =
            await response.json();


        if (
            !data.success ||
            !data.stats
        ) {

            return;
        }


        const stats =
            data.stats;


        const totalEl =
            document.getElementById(
                "statTotalScans"
            );

        const recyclableEl =
            document.getElementById(
                "statRecyclable"
            );

        const generalEl =
            document.getElementById(
                "statGeneralWaste"
            );

        const accuracyEl =
            document.getElementById(
                "statModelAccuracy"
            );


        if (totalEl) {

            totalEl.textContent =
                stats.total_scans;

        }


        if (recyclableEl) {

            recyclableEl.textContent =
                stats.recyclable_count;

        }


        if (generalEl) {

            generalEl.textContent =
                stats.general_waste_count;

        }


        if (accuracyEl) {

            if (
                data.meta &&
                data.meta.val_accuracy
            ) {

                accuracyEl.textContent =
                    data.meta.val_accuracy +
                    "%";

            }

            else {

                accuracyEl.textContent =
                    stats.avg_confidence +
                    "%";

            }

        }

    }

    catch (error) {

        console.warn(
            "Could not update statistics:",
            error
        );

    }

}


/* ============================================================
   HISTORY PAGE
   ============================================================ */

function initHistoryPage() {

    const searchInput =
        document.getElementById(
            "historySearch"
        );

    const clearBtn =
        document.getElementById(
            "clearHistoryBtn"
        );


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            function (event) {

                filterHistoryTable(
                    event.target.value
                        .toLowerCase()
                );

            }
        );

    }


    if (clearBtn) {

        clearBtn.addEventListener(
            "click",
            async function () {

                const confirmed =
                    confirm(
                        "Are you sure you want to clear all prediction history?"
                    );


                if (!confirmed) {

                    return;

                }


                try {

                    const response =
                        await fetch(
                            "/api/history/clear",
                            {
                                method:
                                    "POST"
                            }
                        );


                    const data =
                        await response.json();


                    if (data.success) {

                        showToast(
                            "History cleared.",
                            "info"
                        );


                        location.reload();

                    }

                }

                catch (error) {

                    showToast(
                        "Failed to clear history.",
                        "error"
                    );

                }

            }
        );

    }

}


/* ============================================================
   HISTORY SEARCH
   ============================================================ */

function filterHistoryTable(query) {

    const rows =
        document.querySelectorAll(
            "#historyTableBody tr"
        );


    rows.forEach(
        function (row) {

            const text =
                row.textContent
                    .toLowerCase();


            row.style.display =
                text.includes(query)
                    ? ""
                    : "none";

        }
    );

}


/* ============================================================
   ANALYTICS PAGE
   ============================================================ */

async function initAnalyticsPage() {

    try {

        const response =
            await fetch(
                "/api/stats"
            );


        const data =
            await response.json();


        if (
            !data.success ||
            !data.stats
        ) {

            return;

        }


        const stats =
            data.stats;


        /*
           Category chart
        */

        const categoryCanvas =
            document.getElementById(
                "categoryChart"
            );


        if (
            categoryCanvas &&
            typeof Chart !== "undefined"
        ) {

            new Chart(
                categoryCanvas.getContext(
                    "2d"
                ),
                {

                    type:
                        "doughnut",

                    data: {

                        labels: [

                            "Cardboard",

                            "Glass",

                            "Metal",

                            "Paper",

                            "Plastic",

                            "Trash"

                        ],

                        datasets: [

                            {

                                data: [

                                    stats.category_counts.cardboard || 0,

                                    stats.category_counts.glass || 0,

                                    stats.category_counts.metal || 0,

                                    stats.category_counts.paper || 0,

                                    stats.category_counts.plastic || 0,

                                    stats.category_counts.trash || 0

                                ],

                                backgroundColor: [

                                    "#D97706",

                                    "#2563EB",

                                    "#64748B",

                                    "#EAB308",

                                    "#16A36F",

                                    "#EF4444"

                                ],

                                borderWidth:
                                    0

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {

                                position:
                                    "bottom"

                            }

                        }

                    }

                }
            );

        }


        /*
           Recyclable chart
        */

        const recyclableCanvas =
            document.getElementById(
                "recyclableChart"
            );


        if (
            recyclableCanvas &&
            typeof Chart !== "undefined"
        ) {

            new Chart(

                recyclableCanvas.getContext(
                    "2d"
                ),

                {

                    type:
                        "bar",

                    data: {

                        labels: [

                            "Recyclable",

                            "General Waste"

                        ],

                        datasets: [

                            {

                                label:
                                    "Total Scanned Items",

                                data: [

                                    stats.recyclable_count || 0,

                                    stats.general_waste_count || 0

                                ],

                                backgroundColor: [

                                    "#16A36F",

                                    "#F59E0B"

                                ],

                                borderRadius:
                                    8

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        plugins: {

                            legend: {

                                display:
                                    false

                            }

                        },

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }

            );

        }

    }

    catch (error) {

        console.error(
            "Analytics initialization failed:",
            error
        );

    }

}