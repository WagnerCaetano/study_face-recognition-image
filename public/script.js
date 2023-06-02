let videoElement, userIdInput;

function initializeCamera() {
  videoElement = document.createElement("video");
  videoElement.autoplay = true;
  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then((stream) => {
      videoElement.srcObject = stream;
      document.body.querySelector(".divVideo").appendChild(videoElement);
    })
    .catch((error) => {
      console.error("Error accessing camera:", error);
      alert("Error accessing camera. Please try again.");
    });
}

function captureScreenshot() {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  context.drawImage(videoElement, 0, 0, videoElement.videoWidth, videoElement.videoHeight);

  const screenshotDataUrl = canvas.toDataURL("image/png");
  const blob = dataURLtoBlob(screenshotDataUrl);
  const file = new File([blob], "screenshot.png");

  sendImage(file);
}

function dataURLtoBlob(dataURL) {
  const parts = dataURL.split(",");
  const byteString = parts[0].indexOf("base64") >= 0 ? atob(parts[1]) : decodeURIComponent(parts[1]);
  const mime = parts[0].split(":")[1].split(";")[0];

  const byteArray = new Uint8Array(byteString.length);
  for (let i = 0; i < byteString.length; i++) {
    byteArray[i] = byteString.charCodeAt(i);
  }

  return new Blob([byteArray], { type: mime });
}

function sendImage(file) {
  if (!userIdInput.value.trim()) {
    alert("Please enter a user ID.");
    return;
  }

  const userId = userIdInput.value.trim();
  const imageDb = document.getElementById("database");
  imageDb.setAttribute("src", "https://photos173431-staging.s3.sa-east-1.amazonaws.com/public/" + userId + ".jpg");

  const imageEnviada = document.getElementById("enviada");
  imageEnviada.setAttribute("src", URL.createObjectURL(file));

  const apiUrl = "http://ec2-18-228-199-45.sa-east-1.compute.amazonaws.com:5000/photos";
  const formData = new FormData();
  formData.append("file", file);

  const requestUrl = `${apiUrl}?userId=${encodeURIComponent(userId)}`;

  fetch(requestUrl, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        document.getElementById("result-text").textContent = "Error: " + data.error;
      } else {
        const similarity = data.Similarity || 0;
        document.getElementById("result-text").textContent = "Similarity: " + similarity.toFixed(2) + "%";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("result-text").textContent = "An error occurred.";
    });
}

function uploadImage() {
  const fileInput = document.getElementById("file");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select an image file.");
    return;
  }

  if (!userIdInput.value.trim()) {
    alert("Please enter a user ID.");
    return;
  }

  const userId = userIdInput.value.trim();
  const imageDb = document.getElementById("database");
  imageDb.setAttribute("src", "https://photos173431-staging.s3.sa-east-1.amazonaws.com/public/" + userId + ".jpg");

  const imageEnviada = document.getElementById("enviada");
  imageEnviada.setAttribute("src", URL.createObjectURL(file));

  const apiUrl = "http://ec2-18-228-199-45.sa-east-1.compute.amazonaws.com:5000/photos";
  const formData = new FormData();
  formData.append("file", file);

  const requestUrl = `${apiUrl}?userId=${encodeURIComponent(userId)}`;

  fetch(requestUrl, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        document.getElementById("result-text").textContent = "Error: " + data.error;
      } else {
        const similarity = data.Similarity || 0;
        document.getElementById("result-text").textContent = "Similarity: " + similarity.toFixed(2) + "%";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("result-text").textContent = "An error occurred.";
    });
}

document.addEventListener("DOMContentLoaded", function () {
  if (window.location !== "http://ec2-18-228-199-45.sa-east-1.compute.amazonaws.com:5000") {
    window.location.href = "http://ec2-18-228-199-45.sa-east-1.compute.amazonaws.com:5000";
  }
  userIdInput = document.getElementById("userId");
  initializeCamera();
});
