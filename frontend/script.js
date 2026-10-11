
const API_URL = "https://medischedule-26s2.onrender.com";

// Voice assistant state
var voiceRoom = null;
var activeRoomName = null;
var voiceConnecting = false;

// =========================
// NAVIGATION
// =========================

function showSection(sectionId) {
    document.getElementById(sectionId).scrollIntoView({
        behavior: "smooth"
    });
}


// =========================
// REGISTER PATIENT
// =========================

async function registerPatient() {

    const name = document.getElementById("patientName").value;
    const age = document.getElementById("patientAge").value;
    const phone = document.getElementById("patientPhone").value;
    const email = document.getElementById("patientEmail").value;

    if (!name || !age || !phone || !email) {
        document.getElementById("patientMessage").innerText =
            "Please fill all patient details.";
        return;
    }

    try {

        const response = await fetch(`${API_URL}/patients`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                age: Number(age),
                phone: phone,
                email: email
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to register patient");
        }

        document.getElementById("patientMessage").innerText =
            `Patient registered successfully! Patient ID: ${data.patient_id}`;

        document.getElementById("patientName").value = "";
        document.getElementById("patientAge").value = "";
        document.getElementById("patientPhone").value = "";
        document.getElementById("patientEmail").value = "";

        loadStatistics();

    } catch (error) {

        document.getElementById("patientMessage").innerText =
            `Error: ${error.message}`;
    }
}


// =========================
// ADD DOCTOR
// =========================

async function addDoctor() {

    const name = document.getElementById("doctorName").value;
    const specialization =
        document.getElementById("specialization").value;

    const availableDays =
        document.getElementById("availableDays").value;

    const availableTime =
        document.getElementById("availableTime").value;

    if (!name || !specialization || !availableDays || !availableTime) {

        document.getElementById("doctorMessage").innerText =
            "Please fill all doctor details.";

        return;
    }

    try {

        const response = await fetch(`${API_URL}/doctors`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                name: name,

                specialization: specialization,

                available_days: availableDays,

                available_time: availableTime
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to add doctor");
        }

        document.getElementById("doctorMessage").innerText =
            `Doctor added successfully! Doctor ID: ${data.doctor_id}`;

        document.getElementById("doctorName").value = "";
        document.getElementById("specialization").value = "";
        document.getElementById("availableDays").value = "";
        document.getElementById("availableTime").value = "";

        loadStatistics();

    } catch (error) {

        document.getElementById("doctorMessage").innerText =
            `Error: ${error.message}`;
    }
}


// =========================
// BOOK APPOINTMENT
// =========================

async function bookAppointment() {

    const patientId =
        document.getElementById("appointmentPatient").value;

    const doctorId =
        document.getElementById("appointmentDoctor").value;

    const date =
        document.getElementById("appointmentDate").value;

    const time =
        document.getElementById("appointmentTime").value;

    const reason =
        document.getElementById("appointmentReason").value;

    if (!patientId || !doctorId || !date || !time) {

        document.getElementById("appointmentMessage").innerText =
            "Please fill patient ID, doctor ID, date and time.";

        return;
    }

    try {

        const response = await fetch(`${API_URL}/appointments`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                patient_id: Number(patientId),

                doctor_id: Number(doctorId),

                appointment_date: date,

                appointment_time: time,

                reason: reason
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to book appointment");
        }

        document.getElementById("appointmentMessage").innerText =
            `Appointment booked successfully! Appointment ID: ${data.appointment_id}`;

        document.getElementById("appointmentPatient").value = "";
        document.getElementById("appointmentDoctor").value = "";
        document.getElementById("appointmentDate").value = "";
        document.getElementById("appointmentTime").value = "";
        document.getElementById("appointmentReason").value = "";

        loadAppointments();
        loadStatistics();

    } catch (error) {

        document.getElementById("appointmentMessage").innerText =
            `Error: ${error.message}`;
    }
}


// =========================
// LOAD APPOINTMENTS
// =========================

async function loadAppointments() {

    try {

        const response =
            await fetch(`${API_URL}/appointments`);

        const data = await response.json();

        const container =
            document.getElementById("appointmentsData");

        container.innerHTML = "";

        if (data.appointments.length === 0) {

            container.innerHTML =
                "<p>No appointments found.</p>";

            return;
        }

        data.appointments.forEach(appointment => {

            const card =
                document.createElement("div");

            card.className = "appointment-card";

            card.innerHTML = `

                <strong>
                    Appointment #${appointment.id}
                </strong>

                <p>
                    👤 Patient:
                    ${appointment.patient_name}
                </p>

                <p>
                    👨‍⚕️ Doctor:
                    ${appointment.doctor_name}
                </p>

                <p>
                    🏥 Specialization:
                    ${appointment.specialization}
                </p>

                <p>
                    📅 Date:
                    ${appointment.appointment_date}
                </p>

                <p>
                    ⏰ Time:
                    ${appointment.appointment_time}
                </p>

                <p>
                    📝 Reason:
                    ${appointment.reason || "Not specified"}
                </p>

                <p>
                    📌 Status:
                    <strong>${appointment.status}</strong>
                </p>

                ${
                    appointment.status === "Booked"
                    ?
                    `<button
                        class="cancel-btn"
                        onclick="cancelAppointment(${appointment.id})">
                        Cancel Appointment
                    </button>`
                    :
                    ""
                }

            `;

            container.appendChild(card);

        });

    } catch (error) {

        document.getElementById("appointmentsData").innerHTML =
            `<p>Error loading appointments: ${error.message}</p>`;
    }
}


// =========================
// CANCEL APPOINTMENT
// =========================

async function cancelAppointment(id) {

    const confirmed =
        confirm("Are you sure you want to cancel this appointment?");

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(`${API_URL}/appointments/${id}`, {

                method: "DELETE"
            });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to cancel appointment");
        }

        alert("Appointment cancelled successfully.");

        loadAppointments();
        loadStatistics();

    } catch (error) {

        alert(`Error: ${error.message}`);
    }
}


// =========================
// AI ASSISTANT
// =========================

async function askAI() {

    const input =
        document.getElementById("aiMessage");

    const message =
        input.value.trim();

    if (!message) {
        return;
    }

    const chat =
        document.getElementById("chatMessages");


    // USER MESSAGE

    const userMessage =
        document.createElement("div");

    userMessage.className =
        "user-message";

    userMessage.innerText =
        message;

    chat.appendChild(userMessage);

    input.value = "";

    chat.scrollTop =
        chat.scrollHeight;


    // LOADING MESSAGE

    const loading =
        document.createElement("div");

    loading.className =
        "ai-message";

    loading.innerText =
        "MediSchedule AI is thinking...";

    chat.appendChild(loading);


    try {

        const response =
            await fetch(`${API_URL}/ai-assistant`, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    user_id: "web_patient",

                    message: message
                })
            });

        const data =
            await response.json();

        loading.remove();


        if (!response.ok) {
            throw new Error(
                data.detail || "AI request failed"
            );
        }


        const aiMessage =
            document.createElement("div");

        aiMessage.className =
            "ai-message";


        let reply = data.response;


        // Try to extract Lyzr response text

        if (typeof data.response === "object") {

            reply =
                data.response.response ||
                data.response.message ||
                data.response.answer ||
                JSON.stringify(
                    data.response
                );
        }


        aiMessage.innerText =
            reply;

        chat.appendChild(aiMessage);

        chat.scrollTop =
            chat.scrollHeight;


    } catch (error) {

        loading.innerText =
            `AI Error: ${error.message}`;
    }
}


// =========================
// LOAD STATISTICS
// =========================

async function loadStatistics() {

    try {

        const patientsResponse =
            await fetch(`${API_URL}/patients`);

        const patients =
            await patientsResponse.json();

        document.getElementById("patientCount").innerText =
            patients.count;


        const doctorsResponse =
            await fetch(`${API_URL}/doctors`);

        const doctors =
            await doctorsResponse.json();

        document.getElementById("doctorCount").innerText =
            doctors.count;


        const appointmentsResponse =
            await fetch(`${API_URL}/appointments`);

        const appointments =
            await appointmentsResponse.json();

        document.getElementById("appointmentCount").innerText =
            appointments.count;

    } catch (error) {

        console.log(
            "Unable to load statistics:",
            error
        );
    }
}


// =========================
// INITIALIZE WEBSITE
// =========================

window.addEventListener("load", () => {

    loadStatistics();

    loadAppointments();

});ch

/* =========================================
   MEDISCHEDULE AI - LIVE VOICE ASSISTANT
   ========================================= */

// Initialize voice state BEFORE any voice functions use it.

function setVoiceStatus(status, message) {
    const statusElement = document.getElementById("voiceStatus");
    const messageElement = document.getElementById("voiceMessage");
    const startButton = document.getElementById("startCallButton");
    const endButton = document.getElementById("endCallButton");

    if (statusElement) statusElement.textContent = status;
    if (messageElement) messageElement.textContent = message;

    if (startButton) {
        startButton.disabled = voiceConnecting || !!voiceRoom;
    }

    if (endButton) {
        endButton.disabled = !voiceRoom && !voiceConnecting;
    }
}



async function startVoiceCall() {
    if (voiceRoom || voiceConnecting) return;

    if (!window.LivekitClient) {
        setVoiceStatus(
            "Library unavailable",
            "Unable to load LiveKit. Check your internet connection and reload the page."
        );
        return;
    }

    voiceConnecting = true;
    setVoiceStatus("Connecting...", "Requesting a new voice session.");

    let room = null;

    try {
        // Request a fresh session from our backend.
        const roomName =
            "medischedule-" +
            Date.now() +
            "-" +
            Math.random().toString(36).slice(2, 8);

        const response = await fetch(`${API_URL}/start-voice-session`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_identity: "patient_demo_001",
                room_name: roomName
            })
        });

        const session = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof session.detail === "string"
                    ? session.detail
                    : JSON.stringify(session.detail || "Unable to start voice session")
            );
        }

        if (!session.userToken || !session.livekitUrl) {
            throw new Error("The backend did not return the LiveKit connection details.");
        }

        activeRoomName = session.roomName || roomName;

        // Create the LiveKit room.
        room = new LivekitClient.Room();
        voiceRoom = room;

        room.on(
            LivekitClient.RoomEvent.TrackSubscribed,
            (track, publication, participant) => {
                if (track.kind === LivekitClient.Track.Kind.Audio) {
                    const audioElement = document.getElementById("remoteAudio");
                    if (audioElement) {
                        track.attach(audioElement);
                        audioElement.play().catch(() => {
                            setVoiceStatus(
                                "Connected",
                                "Click the audio player's play button if you cannot hear the agent."
                            );
                        });
                    }
                }
            }
        );

        room.on(
            LivekitClient.RoomEvent.Disconnected,
            () => {
                const audioElement = document.getElementById("remoteAudio");
                if (audioElement) audioElement.srcObject = null;

                voiceRoom = null;
                voiceConnecting = false;
                activeRoomName = null;

                setVoiceStatus("Disconnected", "The voice call has ended.");
            }
        );

        setVoiceStatus("Connecting to voice room...", "Please allow microphone access.");

        await room.connect(session.livekitUrl, session.userToken);

        // Publish the user's microphone.
        await room.localParticipant.setMicrophoneEnabled(true);

        voiceConnecting = false;
        setVoiceStatus(
            "Connected",
            session.agentDispatched
                ? "Connected. You can now speak to MediSchedule AI."
                : "Connected to the room. Waiting for the voice agent."
        );

    } catch (error) {
        console.error("Voice call error:", error);

        if (room) {
            try {
                room.disconnect();
            } catch (_) {
                // Ignore cleanup errors.
            }
        }

        voiceRoom = null;
        voiceConnecting = false;
        activeRoomName = null;

        setVoiceStatus("Connection failed", error.message);
    }
}

async function endVoiceCall() {
    const room = voiceRoom;
    const roomName = activeRoomName;

    voiceConnecting = false;

    // Disconnect locally even if the backend end request fails.
    if (room) {
        try {
            room.disconnect();
        } catch (error) {
            console.error("Error disconnecting LiveKit:", error);
        }
    }

    voiceRoom = null;
    activeRoomName = null;

    const audioElement = document.getElementById("remoteAudio");
    if (audioElement) {
        audioElement.pause();
        audioElement.srcObject = null;
    }

    if (roomName) {
        try {
            const response = await fetch(`${API_URL}/end-voice-session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    room_name: roomName
                })
            });

            if (!response.ok) {
                const result = await response.json().catch(() => ({}));
                console.warn("Backend session-end response:", result);
            }
        } catch (error) {
            console.error("Could not notify backend to end session:", error);
        }
    }

    setVoiceStatus("Disconnected", "Your voice call has ended.");
}
